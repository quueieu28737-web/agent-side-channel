"""Post hoc customer-resampled calibration experiment; no model API calls.

Each replicate resamples source training customers, rebuilds both calibrators,
and makes fresh TLS loopback captures of all target trajectories. Two attacker
fits separate calibration sensitivity (original training customers) from joint
calibration/attacker training sensitivity (independent customer bootstrap).
"""
from pathlib import Path
import sys, json, gzip, hashlib, datetime, tempfile, argparse, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np

D=Path(__file__).resolve().parent; E=D.parent; OLD=E/'sp2027-r14-transfer-boundaries'
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import network_replay as nr
import evaluate_network as en
NAMES=['sp2027-r11-minimax','sp2027-r12-glm']
SEED=20261025; REPS=100

def save(path,obj):
    nr.write(path,obj)

def load_data():
    ns,tools,base,tasks=nr.load()
    split=nr.read(E/NAMES[0]/'formal_plan.json')
    episodes={n:[nr.read(p) for p in sorted((E/n/'formal/baseline').glob('task-*/episode.json'))] for n in NAMES}
    assert all(len(v)==115 for v in episodes.values())
    users=sorted({e['user'] for e in episodes[NAMES[0]] if e['task'] in split['train']})
    assert len(users)==29
    for n in NAMES:
        assert nr.read(E/n/'formal_plan.json')['train']==split['train']
        assert set(users).isdisjoint({e['user'] for e in episodes[n] if e['task'] in split['test']})
    return ns,tools,base,split,episodes,users

def init():
    global NS,TOOLS,BASE,SPLIT,EPISODES,USERS,VERBS,RAW,FROZEN
    NS,TOOLS,BASE,SPLIT,EPISODES,USERS=load_data();VERBS=sorted(TOOLS)
    RAW={n:sorted([s for s in nr.read(E/n/'network_sessions.json') if s['condition']=='raw'],key=lambda s:s['task']) for n in NAMES}
    FROZEN={}
    for n in NAMES:
        cal=nr.read(E/n/'network_calibration.json'); ee={e['task']:e for e in EPISODES[n]}
        ss=[nr.read(p) for p in sorted((OLD/'transfer_captures'/n/n/'transferred_joint').glob('*.json'))]
        for s in ss:s['calls']=nr.cover_episode(ee[s['task']],cal,TOOLS,BASE)[0]
        FROZEN[n]=ss

def resample(rows,draw):
    groups={u:[r for r in rows if r['user']==u] for u in USERS}
    return [r for u in draw for r in groups[u]]

def ba(pred,y,weights=None):
    pred=np.asarray(pred);y=np.asarray(y)
    w=np.ones(len(y)) if weights is None else np.asarray(weights)
    if w[y==1].sum()==0 or w[y==0].sum()==0:return float('nan')
    return float(.5*(np.sum(w*(y==1)*(pred==1))/w[y==1].sum()+np.sum(w*(y==0)*(pred==0))/w[y==0].sum()))

def fit(tr,te,clean):
    out={}; ft=lambda ss:[en.ev.net_features(s['records']) for s in ss]
    Xtr,Xte,Xclean=ft(tr),ft(te),ft(clean)
    mapping=en.decoder(tr);dtr=[en.decode(s,mapping) for s in tr];dte=[en.decode(s,mapping) for s in te]
    dXtr=[en.ev.disp_features(c,VERBS) for c in dtr];dXte=[en.ev.disp_features(c,VERBS) for c in dte]
    for label,(field,verb) in en.ev.TARGETS.items():
        y=np.array([s[field] for s in tr]);yte=np.array([s[field] for s in te]);pred={}
        pred['majority']=np.full(len(te),int(y.mean()>=.5))
        pred['D0_gboost']=(en.predict_model(Xclean,np.array([s[field] for s in clean]),Xte,'gboost')>=.5).astype(int)
        for kind in en.ev.MODELS:pred['D2_'+kind]=(en.predict_model(Xtr,y,Xte,kind)>=.5).astype(int)
        pred['network_decode_gboost']=(en.predict_model(dXtr,y,dXte,'gboost')>=.5).astype(int)
        def count(a,b):
            if len(set(y))<2:return np.full(len(b),int(y[0]))
            return en.count_rule(a,y,b)[1]
        pred['network_decode_count_rule']=count([sum(c['name']==verb for c in cs) for cs in dtr],[sum(c['name']==verb for c in cs) for cs in dte])
        pred['exchange_count_rule']=count([len(en.ev.exchanges(s['records'])) for s in tr],[len(en.ev.exchanges(s['records'])) for s in te])
        out[label]={'suite_ba':max(ba(p,yte) for p in pred.values()),'predictions':{k:p.tolist() for k,p in pred.items()},'y':yte.tolist(),'users':[s['user'] for s in te],'tasks':[s['task'] for s in te]}
    return out

def replicate(i):
    dest=D/'replicates'/f'{i:03d}.json'
    if dest.exists():return i,'cached'
    started=time.monotonic();rng=np.random.default_rng(SEED+i)
    draw=rng.choice(USERS,len(USERS),replace=True).tolist()
    attackdraw=rng.choice(USERS,len(USERS),replace=True).tolist()
    out={'replicate':i,'calibration_customers':draw,'attacker_customers':attackdraw,'calibrations':{},'results':[]};captures=[]
    with tempfile.TemporaryDirectory(prefix='r21-tls-') as tmp:
        contexts=nr.tlslab.make_contexts(Path(tmp),'1.2')
        for source in NAMES:
            train=[e for e in EPISODES[source] if e['task'] in SPLIT['train']]
            nr.HERE=E/source
            cal=nr.fit_calibration(resample(train,draw),NS,TOOLS,BASE)
            # Original helper's training_tasks is the allowed population. Record actual draw separately.
            cal['actual_sampled_tasks']=[r['task'] for r in resample(train,draw)]
            out['calibrations'][source]=cal
            for target in NAMES:
                rows=[]
                for e in EPISODES[target]:
                    calls,flags=nr.cover_episode(e,cal,TOOLS,BASE)
                    ex=[(nr.frame(c['req_text'],'const',True,cal['caps']),nr.frame(c['resp_text'],'const',False,cal['caps'])) for c in calls]
                    seq=nr.tlslab.run_session(*contexts,ex)
                    assert len(en.ev.exchanges(seq))==len(calls)
                    s={k:e[k] for k in ['task','user','has_cancel','has_return']}
                    s.update(records=seq,calls=[{'name':c['name'],'resp':c['resp']} for c in calls],application_wire_bytes=sum(n+5 for d,n in seq))
                    rows.append(s)
                captures.append({'source':source,'target':target,'sessions':rows})
                tr=[s for s in rows if s['task'] in SPLIT['train']];te=[s for s in rows if s['task'] in SPLIT['test']]
                clean=[s for s in RAW[target] if s['task'] in SPLIT['train']]
                rawtest=[s for s in RAW[target] if s['task'] in SPLIT['test']]
                cost={'bytes_ratio':sum(s['application_wire_bytes'] for s in te)/sum(s['application_wire_bytes'] for s in rawtest),'calls_ratio':sum(len(s['calls']) for s in te)/sum(len(s['calls']) for s in rawtest)}
                for regime in ['calibration_only','calibration_and_attacker']:
                    result=fit(tr,te,clean) if regime=='calibration_only' else fit(resample(tr,attackdraw),te,resample(clean,attackdraw))
                    out['results'].append(dict(source=source,target=target,regime=regime,metrics=result,**cost))
        for target in NAMES:
            rows=FROZEN[target];tr=[s for s in rows if s['task'] in SPLIT['train']];te=[s for s in rows if s['task'] in SPLIT['test']]
            clean=[s for s in RAW[target] if s['task'] in SPLIT['train']]
            out['results'].append(dict(source=target,target=target,regime='attacker_only',metrics=fit(resample(tr,attackdraw),te,resample(clean,attackdraw))))
    out['seconds']=time.monotonic()-started
    cap=D/'captures'/f'{i:03d}.json.gz';cap.parent.mkdir(exist_ok=True)
    with gzip.open(cap,'wt',encoding='utf8') as f:json.dump(captures,f,separators=(',',':'))
    out['capture_sha256']=nr.sha(cap);save(dest,out)
    return i,round(out['seconds'],1)

def freeze():
    assert not (D/'protocol.json').exists(),'Do not overwrite a frozen plan'
    ns,tools,base,split,episodes,users=load_data()
    sources={}
    for n in NAMES:
        for p in sorted((E/n/'formal/baseline').glob('task-*/episode.json')):sources[p.relative_to(E).as_posix()]=nr.sha(p)
        for name in ['network_calibration.json','network_sessions.json','formal_plan.json']:sources[f'{n}/{name}']=nr.sha(E/n/name)
    for p in (E/'sp2027-r12-glm').glob('*.py'):sources[p.relative_to(E).as_posix()]=nr.sha(p)
    sources['sp2027-r14-transfer-boundaries/full_suite_results.json']=nr.sha(OLD/'full_suite_results.json')
    save(D/'protocol.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'post_hoc_design_frozen_before_new_results','replicates':REPS,'seed':SEED,'calibration_sample':'29 training customer clusters with replacement, all tasks per selected customer; identical draw across source endpoints; duplicated episodes weight caps, donor dedup preserved','attacker_sample':'Independent draw of 29 training customers, shared across endpoints/conditions. Single-class fits use constant predictions, never silently redraw.','test':'Original 46 tasks/24 customers held fixed for stability spreads; optional 20 paired test-customer resamples per training replicate for joint sampling intervals; invalid one-class test draws counted, not replaced','suite':['majority','D0_gboost','D2_logreg','D2_gboost','network_decode_gboost','network_decode_count_rule','exchange_count_rule'],'regimes':['calibration_only','calibration_and_attacker','attacker_only_frozen_local_calibration'],'null':'Original eight conditional contrasts: exchangeability of condition prediction vectors within each held-out customer, whole suite swapped together; max reselected, two-sided absolute statistic; 99999 MC permutations, plus-one p, Holm family of eight','inference':'Stability under observed training-customer empirical distribution; neither new customers nor new model generations. Source-calibration bootstrap is paired by customer ID. Does not identify a population-level causal model effect.','kill_criterion':'Withdraw resolved directional/model-source attribution if multiplicity or resampled variability does not support it. Nonmonotonicity alone is not evidence of source-specific transfer failure.','sources':sources,'run_sha256':nr.sha(Path(__file__))})
    print('FROZEN',len(sources))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','run']);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int,default=REPS);a=ap.parse_args()
    if a.action=='freeze':freeze()
    else:
        protocol=nr.read(D/'protocol.json');assert protocol['run_sha256']==nr.sha(Path(__file__))
        for rel,h in protocol['sources'].items():assert nr.sha(E/rel)==h,rel
        with ProcessPoolExecutor(max_workers=a.workers,initializer=init) as pool:
            for i,elapsed in pool.map(replicate,range(a.limit)):
                print('REPLICATE',i,elapsed,flush=True)
                save(D/'status.json',{'completed':len(list((D/'replicates').glob('*.json'))),'planned':REPS,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
