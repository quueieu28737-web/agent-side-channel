"""Frozen train/test attackers and task-clustered descriptive uncertainty."""
from collections import Counter,defaultdict
import numpy as np
from common import *
import e67_eval as ev
import reanalyze as stats
from defense import CONDITIONS,episodes

def scalar_summary(values,units):
    tids=sorted(set(u['task'] for u in units));idx={t:[i for i,u in enumerate(units) if u['task']==t] for t in tids}
    sums=np.array([sum(values[i] for i in idx[t]) for t in tids]);counts=np.array([len(idx[t]) for t in tids])
    picks=np.random.default_rng(20261021).integers(len(tids),size=(2000,len(tids)))
    return {'mean':float(sums.sum()/counts.sum()),'ci95':np.quantile(sums[picks].sum(1)/counts[picks].sum(1),[.025,.975]).tolist()}

def predict_model(Xtr,ytr,Xte,kind):
    if len(set(ytr))<2: return np.full(len(Xte),float(ytr[0]))
    model=ev.MODELS[kind]();model.fit(np.asarray(Xtr,float),ytr)
    return model.predict_proba(np.asarray(Xte,float))[:,1]

def count_rule(ctr,y,cte):
    ctr=np.asarray(ctr);cte=np.asarray(cte)
    best=(-1,0)
    for th in range(int(ctr.max(initial=0))+2):
        pred=ctr>=th
        ba=.5*(np.mean(pred[y==1])+np.mean(~pred[y==0]))
        if ba>best[0]:best=(ba,th)
    return cte.astype(float),(cte>=best[1]).astype(int),best[1]

def decoder(train):
    full=defaultdict(Counter);req=defaultdict(Counter);freq=Counter()
    for s in train:
        for c,(a,b) in zip(s['calls'],ev.exchanges(s['records'])):
            full[a,b][c['name']]+=1;req[a][c['name']]+=1;freq[c['name']]+=1
    majority=freq.most_common(1)[0][0] if freq else 'unknown'
    return ({k:v.most_common(1)[0][0] for k,v in full.items()},
            {k:v.most_common(1)[0][0] for k,v in req.items()},majority)

def decode(s,mapping):
    full,req,majority=mapping
    return [{'name':full.get((a,b),req.get(a,majority)),'resp':b} for a,b in ev.exchanges(s['records'])]

def adherence(e):
    # Mechanical compliance proxy only; never an independent authorization audit.
    calls=e['calls'];users=[i for i,c in enumerate(calls) if c['name']=='get_user_details' and not c['err']]
    related=[i for i,c in enumerate(calls) if c['name']=='get_order_details' or c['name'] in ev.WRITES-{'modify_user_address'}]
    prefix=(len(users)==1 and (not related or users[0]<min(related)))
    read_orders=set();read_before_write=True
    for c in calls:
        oid=c.get('kwargs',{}).get('order_id')
        if c['name']=='get_order_details' and not c['err']:read_orders.add(oid)
        if c['name'] in ev.WRITES and oid and oid not in read_orders:read_before_write=False
    return {'user_details_once_before_order':int(prefix),'read_before_order_write':int(read_before_write),
            'all_measured_rules':int(prefix and read_before_write)}

def main():
    split=read(HERE/'split.json');rows=read(HERE/'sessions.json');ns,tools,base,tasks=load()
    verbs=sorted(tools);S={(s['prompt'],s['condition'],s['task'],s['repeat']):s for s in rows}
    assert len(S)==len(rows)==len(tasks)*len(REPEATS)*len(PROMPTS)*len(CONDITIONS),'Missing/duplicate session'
    keys={part:[(t,r) for t in split[part] for r in REPEATS] for part in ('train','test')}
    get=lambda arm,cond,part:[S[arm,cond,t,r] for t,r in keys[part]]
    results=[];predictions=[];paired={}
    for target,(lab,verb) in ev.TARGETS.items():
        train0=get('baseline','raw','train');test0=get('baseline','raw','test')
        ytr=np.array([s[lab] for s in train0]);yte=np.array([s[lab] for s in test0])
        units=[{'task':s['user'],'task_id':s['task'],'seed':s['repeat'],'y':s[lab]} for s in test0]
        for view in ('dispatch','network'):
            feat=(lambda s:ev.disp_features(s['calls'],verbs)) if view=='dispatch' else (lambda s:ev.net_features(s['records']))
            for arm in PROMPTS:
                for cond in CONDITIONS:
                    tr=get(arm,cond,'train');te=get(arm,cond,'test')
                    Xtr=[feat(s) for s in tr];Xte=[feat(s) for s in te]
                    attacks={};details={};boot=[];aucboot=[]
                    majority=int(ytr.mean()>=.5)
                    attacks['majority']=(np.full(len(te),float(majority)),np.full(len(te),majority))
                    sc=predict_model([feat(s) for s in get(arm,'raw','train')],ytr,Xte,'gboost')
                    attacks['D0_gboost']=(sc,(sc>=.5).astype(int))
                    for model in ev.MODELS:
                        sc=predict_model(Xtr,ytr,Xte,model);attacks['D2_'+model]=(sc,(sc>=.5).astype(int))
                    if view=='dispatch':
                        ctr=[sum(c['name']==verb for c in s['calls']) for s in tr]
                        cte=[sum(c['name']==verb for c in s['calls']) for s in te]
                        sc,pr,th=count_rule(ctr,ytr,cte);attacks['D2_count_rule']=(sc,pr);details['threshold']=th
                    else:
                        mapping=decoder(tr);dtr=[decode(s,mapping) for s in tr];dte=[decode(s,mapping) for s in te]
                        sc=predict_model([ev.disp_features(c,verbs) for c in dtr],ytr,[ev.disp_features(c,verbs) for c in dte],'gboost')
                        attacks['network_decode_gboost']=(sc,(sc>=.5).astype(int))
                        sc,pr,th=count_rule([sum(c['name']==verb for c in cs) for cs in dtr],ytr,[sum(c['name']==verb for c in cs) for cs in dte])
                        attacks['network_decode_count_rule']=(sc,pr);details['threshold']=th
                        truth=[c['name'] for s in te for c in s['calls']];guess=[c['name'] for cs in dte for c in cs]
                        details['decoder_accuracy']=float(np.mean(np.array(truth)==guess)) if truth else None
                    metrics={}
                    for name,(sc,pr) in attacks.items():
                        ba,auc=stats.distributions(units,sc,pr,2000);boot.append(ba);aucboot.append(auc)
                        metrics[name]={'ba':float(ba[0]),'auroc':float(auc[0]),'ba_ci95':np.nanquantile(ba[1:],[.025,.975]).tolist()}
                        predictions.append({'target':target,'view':view,'prompt':arm,'condition':cond,'attacker':name,
                            'units':units,'scores':sc.tolist(),'predictions':pr.tolist()})
                    b=np.nanmax(boot,axis=0);a=np.nanmax(aucboot,axis=0)
                    result={'target':target,'view':view,'prompt':arm,'condition':cond,'test_tasks':len(split['test']),
                        'test_episodes':len(te),'positive_test_tasks':int(sum(s[lab] for s in te)//len(REPEATS)),
                        'test_customer_clusters':len(set(s['user'] for s in te)),
                        'positive_customer_clusters':len(set(s['user'] for s in te if s[lab])),
                        'invalid_single_class_bootstrap_draws':int(np.isnan(b[1:]).sum()),
                        'suite_ba':float(b[0]),'suite_ba_ci95':np.nanquantile(b[1:],[.025,.975]).tolist(),
                        'suite_auroc':float(a[0]),'suite_auroc_ci95':np.nanquantile(a[1:],[.025,.975]).tolist(),
                        'attackers':metrics,'details':details}
                    result['criterion']=stats.criterion(result['suite_ba'],result['suite_ba_ci95'],result['suite_auroc'])
                    results.append(result);paired[target,view,arm,cond]=b
                    print(target,view,arm,cond,round(b[0],3),result['suite_ba_ci95'],flush=True)
    differences=[]
    for target in ev.TARGETS:
        for view in ('dispatch','network'):
            for cond in CONDITIONS:
                d=paired[target,view,'rules',cond]-paired[target,view,'baseline',cond]
                differences.append({'target':target,'view':view,'condition':cond,'contrast':'rules minus baseline suite maximum',
                    'difference':float(d[0]),'ci95':np.nanquantile(d[1:],[.025,.975]).tolist()})
    eps=episodes('test');util=[]
    for arm in PROMPTS:
        es=sorted([e for e in eps if e['prompt']==arm],key=lambda e:(e['task'],e['repeat']))
        units=[{'task':e['user']} for e in es]
        for cond in CONDITIONS:
            ss=get(arm,cond,'test');raw=get(arm,'raw','test')
            rec={'prompt':arm,'condition':cond,'episodes':len(es),'status':dict(Counter(e['status'] for e in es)),
                'native_reward':scalar_summary([e['native_reward'] for e in es],units),
                'mean_calls':float(np.mean([len(s['calls']) for s in ss])),
                'call_ratio':sum(len(s['calls']) for s in ss)/max(1,sum(len(s['calls']) for s in raw)),
                'mean_wire_bytes':float(np.mean([s['application_wire_bytes'] for s in ss])),
                'wire_ratio':sum(s['application_wire_bytes'] for s in ss)/max(1,sum(s['application_wire_bytes'] for s in raw)),
                'template_overflow_rate':float(np.mean([bool(s['template_flags'] and s['template_flags']['template_overflow']) for s in ss])),
                'template_underfill_rate':float(np.mean([bool(s['template_flags'] and s['template_flags']['template_underfill']) for s in ss])),
                'framing_overflow_session_rate':float(np.mean([s['framing_overflow_messages']>0 for s in ss])),
                'cover_error_rate':float(np.mean([c['err'] for s in ss for c in s['calls'] if c['kind']=='cover'])) if cond.startswith('shape') else 0.0,
                'rule_compliance':{k:scalar_summary([adherence(e)[k] for e in es],units) for k in adherence(es[0])}}
            util.append(rec)
    er={(e['prompt'],e['task'],e['repeat']):e for e in eps}
    vals=[er['rules',t,r]['native_reward']-er['baseline',t,r]['native_reward'] for t,r in keys['test']]
    reward_delta=scalar_summary(vals,[{'task':tasks[t].user_id} for t,r in keys['test']])
    write(HERE/'predictions.json',predictions)
    write(HERE/'results.json',{'results':results,'prompt_differences':differences,'utility':util,
        'reward_rules_minus_baseline':reward_delta,'bootstrap_draws':2000,
        'interval_scope':'Descriptive conditional customer-cluster bootstrap, all tasks/repeats retained together; fixed training data/models, no retraining or unknown-attacker coverage.',
        'calibration_sha256':sha(HERE/'calibration.json'),'protocol_sha256':sha(HERE/'protocol.json')})

if __name__=='__main__': main()
