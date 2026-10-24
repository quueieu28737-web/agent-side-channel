"""Existing E9-style training-only size-to-tool profiler and decoded attacks."""
from collections import Counter,defaultdict
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from features import exchanges

def decode(records,pack):
    return [{'name':pack['pairs'].get((a,b),pack['requests'].get(a,pack['majority'])), 'resp':b}
            for a,b in exchanges(records)]

def vector(calls,verbs):
    counts=Counter(c['name'] for c in calls);names=[c['name'] for c in calls];big=Counter(zip(names,names[1:]))
    return ([counts[v] for v in verbs]+[np.mean([c['resp'] for c in calls if c['name']==v]) if counts[v] else 0 for v in verbs]+
            [big[a,b] for a in verbs for b in ('cancel_pending_order','get_order_details')]+[len(calls)])

def fit(rows,target):
    pairs=defaultdict(Counter);requests=defaultdict(Counter);freq=Counter()
    for r in rows:
        ex=exchanges(r['records']);assert len(ex)==len(r['requests'])
        names={q['id']:q['name'] for q in r['requests']}
        # Training-only execution annotations establish the profiler's labels.
        # At test time decode() receives only ciphertext records.
        for sent,(a,b) in zip(r['client_send'],ex):
            name=names[sent['id']];pairs[a,b][name]+=1;requests[a][name]+=1;freq[name]+=1
    pack={'pairs':{k:v.most_common(1)[0][0] for k,v in pairs.items()},
          'requests':{k:v.most_common(1)[0][0] for k,v in requests.items()},
          'majority':freq.most_common(1)[0][0],'verbs':sorted(freq)}
    decoded=[decode(r['records'],pack) for r in rows];y=np.array([r['has_'+target] for r in rows])
    model=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=1,random_state=20261021)
    model.fit(np.array([vector(c,pack['verbs']) for c in decoded]),y)
    verb='cancel_pending_order' if target=='cancel' else 'return_delivered_order_items'
    counts=np.array([sum(c['name']==verb for c in cs) for cs in decoded]);best=(-1,0)
    for th in range(int(counts.max(initial=0))+2):
        p=counts>=th;ba=.5*(p[y==1].mean()+(~p[y==0]).mean())
        if ba>best[0]:best=(ba,th)
    pack.update(model=model,verb=verb,threshold=best[1])
    return pack

def predict(rows,pack):
    decoded=[decode(r['records'],pack) for r in rows]
    s=pack['model'].predict_proba(np.array([vector(c,pack['verbs']) for c in decoded]))[:,1]
    count=np.array([sum(c['name']==pack['verb'] for c in cs) for cs in decoded])
    return {'profile_gboost':(s,(s>=.5).astype(int)),
            'profile_count_rule':(count.astype(float),(count>=pack['threshold']).astype(int))}
