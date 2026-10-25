"""Customer paired suite-max permutation, multiplicity and stability analysis."""
import run as r
import numpy as np
import json,sys,gzip
D=r.D; nr=r.nr

def holm(p):
    p=np.asarray(p,float);order=np.argsort(p)
    adjusted=np.empty(len(p));adjusted[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return adjusted

def cluster_contributions(row):
    units=row['units'];y=np.array([u['y'] for u in units]);names=sorted(row['attacks'])
    pred=np.array([row['attacks'][k]['predictions'] for k in names]);users=sorted({u['task'] for u in units})
    w=np.where(y==1,.5/(y==1).sum(),.5/(y==0).sum())
    return np.array([((pred[:,[u['task']==c for u in units]]==y[[u['task']==c for u in units]])*w[[u['task']==c for u in units]]).sum(1) for c in users])

def conditional():
    data=[a for a in nr.read(r.OLD/'full_suite_results.json') if a['study']=='calibration_transfer'];out=[]
    for target in r.NAMES:
        for label in r.en.ev.TARGETS:
            local=next(x for x in data if x['target']==target and x['source']==target and x['condition']=='transferred_joint' and x['label']==label)
            A=cluster_contributions(local)
            for row in data:
                if row['target']!=target or row['label']!=label or row is local:continue
                assert row['units']==local['units'] and sorted(row['attacks'])==sorted(local['attacks'])
                B=cluster_contributions(row);delta=float(B.sum(0).max()-A.sum(0).max())
                assert abs(delta-(row['suite_ba']-local['suite_ba']))<1e-12
                rng=np.random.default_rng(r.SEED);exceed=0;N=99999
                for start in range(0,N,1000):
                    swap=rng.integers(2,size=(min(1000,N-start),len(A)))
                    diff=swap@(B-A);permuted=(B.sum(0)-diff).max(1)-(A.sum(0)+diff).max(1)
                    exceed+=int((np.abs(permuted)>=abs(delta)-1e-12).sum())
                out.append({'target':target,'source':row['source'],'condition':row['condition'],'label':label,'delta':delta,'permutation_p':(exceed+1)/(N+1),'permutations':N,'exchangeability_unit':'whole condition prediction vector for each customer; fixed attackers'})
    assert len(out)==8
    adjusted=holm([x['permutation_p'] for x in out])
    for x,p in zip(out,adjusted):x['holm_p']=float(p)
    nr.write(D/'conditional_tests.json',out)
    print(json.dumps(out,indent=2))

def summary(v):
    a=np.asarray(v,float);valid=a[np.isfinite(a)]
    return dict(n=len(a),valid=len(valid),invalid=len(a)-len(valid),mean=float(valid.mean()),sd=float(valid.std(ddof=1)),median=float(np.median(valid)),range=[float(valid.min()),float(valid.max())],percentiles95=np.quantile(valid,[.025,.975]).tolist())

def boot_metric(m,picks):
    users=sorted(set(m['users']));w=np.array([list(picks).count(u) for u in m['users']]);y=np.array(m['y'])
    if w[y==1].sum()==0 or w[y==0].sum()==0:return float('nan')
    return max(r.ba(p,y,w) for p in m['predictions'].values())

def aggregate():
    files=sorted((D/'replicates').glob('*.json'));assert len(files)==r.REPS
    reps=[nr.read(p) for p in files];groups={};contrasts={};joint={};hashes={};costs={}
    for rep in reps:
        i=rep['replicate'];cap=D/'captures'/f'{i:03d}.json.gz';assert nr.sha(cap)==rep['capture_sha256'];hashes[cap.name]=nr.sha(cap)
        with gzip.open(cap,'rt',encoding='utf8') as f:cs=json.load(f)
        assert len(cs)==4 and all(len(c['sessions'])==115 for c in cs)
        for row in rep['results']:
            if row['regime']=='calibration_only':
                costs.setdefault((row['target'],row['source']),{'bytes':[],'calls':[]})['bytes'].append(row['bytes_ratio'])
                costs[row['target'],row['source']]['calls'].append(row['calls_ratio'])
            for label,m in row['metrics'].items():
                assert len(m['tasks'])==46 and len(set(m['users']))==24 and len(m['predictions'])==7
                assert abs(max(r.ba(p,m['y']) for p in m['predictions'].values())-m['suite_ba'])<1e-12
                key=(row['target'],row['source'],row['regime'],label)
                groups.setdefault(key,[]).append(m['suite_ba'])
        for target in r.NAMES:
            for regime in ['calibration_only','calibration_and_attacker']:
                rows=[x for x in rep['results'] if x['target']==target and x['regime']==regime]
                local=next(x for x in rows if x['source']==target);other=next(x for x in rows if x['source']!=target)
                for label in local['metrics']:
                    key=(target,regime,label);lm=local['metrics'][label];om=other['metrics'][label]
                    assert lm['tasks']==om['tasks'] and lm['users']==om['users'] and lm['y']==om['y']
                    contrasts.setdefault(key,[]).append(om['suite_ba']-lm['suite_ba'])
                    rng=np.random.default_rng(r.SEED+10000+i);users=sorted(set(lm['users']))
                    for _ in range(20):
                        picks=rng.choice(users,len(users),replace=True)
                        joint.setdefault(key,[]).append(boot_metric(om,picks)-boot_metric(lm,picks))
    out={'replicates':len(reps),'sessions':len(reps)*460,'conditional_tests':nr.read(D/'conditional_tests.json'),'stability':[dict(target=k[0],source=k[1],regime=k[2],label=k[3],**summary(v)) for k,v in groups.items()],'contrasts':[dict(target=k[0],regime=k[1],label=k[2],fixed_test=summary(v),joint_train_test=summary(joint[k])) for k,v in contrasts.items()],'scope':'Fixed-test percentiles are training-sensitivity spreads, not confidence intervals. Joint percentiles mix 100 training draws x20 held-out customer draws, paired suite maxima; post hoc finite empirical-population bootstrap, not independent validation or multiplicity-adjusted inference.','capture_hashes':hashes}
    out['costs']=[dict(target=k[0],source=k[1],bytes_ratio=summary(v['bytes']),calls_ratio=summary(v['calls'])) for k,v in costs.items()]
    out['calibrator_variation']={n:{
        'unique_templates':len({json.dumps(rep['calibrations'][n]['template'],sort_keys=True) for rep in reps}),
        'request_caps':sorted({rep['calibrations'][n]['caps']['req'] for rep in reps}),
        'response_caps':sorted({rep['calibrations'][n]['caps']['resp'] for rep in reps}),
        'sampled_episode_occurrences_range':[min(len(rep['calibrations'][n]['actual_sampled_tasks']) for rep in reps),max(len(rep['calibrations'][n]['actual_sampled_tasks']) for rep in reps)]
    } for n in r.NAMES}
    out['analysis_sha256']=nr.sha(r.Path(__file__))
    nr.write(D/'summary.json',out)
    nr.write(D/'verification.json',{'passed':True,'replicates':len(reps),'sessions':len(reps)*460,'prediction_metrics_recomputed':len(reps)*20,'seven_attacks_per_fit':True,'summary_sha256':nr.sha(D/'summary.json'),'protocol_sha256':nr.sha(D/'protocol.json')})
    print(json.dumps({k:v for k,v in out.items() if k!='capture_hashes'},indent=2))

if __name__=='__main__':
    {'conditional':conditional,'aggregate':aggregate}[sys.argv[1]]()
