"""Read-only checks of collection, training-only calibration and saved statistics."""
from collections import defaultdict
import zipfile
import numpy as np
from sklearn.metrics import balanced_accuracy_score,roc_auc_score
from common import *
from defense import episodes,fit_calibration,validate_calibration,CONDITIONS,cover_episode
from evaluate import scalar_summary
import e67_eval as ev
import reanalyze as stats

def check_close(a,b):
    assert np.allclose(a,b,rtol=0,atol=1e-12,equal_nan=True),(a,b)

def verify():
    split=read(HERE/'analysis_split.json');ns,tools,base,tasks=load()
    train=episodes('train');test=episodes('test');eps=train+test
    assert len(eps)==660
    trainusers={tasks[t].user_id for t in split['train']};testusers={tasks[t].user_id for t in split['test']}
    assert not trainusers&testusers
    cal=validate_calibration();assert fit_calibration(train,ns,tools,base)==cal
    for ds in cal['donors'].values():assert all(d['task'] in split['train'] for d in ds)
    S=read(HERE/'sessions.json');assert len(S)==2640
    lookup={(s['prompt'],s['condition'],s['task'],s['repeat']):s for s in S}
    assert len(lookup)==len(S)
    model_calls=0;model_usage=defaultdict(int)
    for e in eps:
        assert e['protocol_sha256']==sha(HERE/'protocol.json')
        assert e['inference_fingerprint']==inference_fingerprint()
        assert e['native_reward']==int(e['db_eq'] and e['r_outputs'])
        assert e['r_outputs']==all(any(m.get('role')=='assistant' and o.lower() in m.get('content','').lower().replace(',','') for m in e['agent_messages']) for o in tasks[e['task']].outputs)
        model_calls+=e['model_calls']
        for k,v in e['usage'].items():model_usage[k]+=v
        gold=old.make_env(ns,tools,base,tasks[e['task']])
        for c in e['calls']:
            if c['name'] in tools:
                # Independent tool execution state check; respond changes no data.
                try:gold.step(ns['Action'](name=c['name'],kwargs=c['kwargs']))
                except Exception:pass
        ref=old.make_env(ns,tools,base,tasks[e['task']])
        for a in tasks[e['task']].actions:ref.step(a)
        # Direct structured-state equality independently checks the collector hash criterion.
        assert (gold.data==ref.data)==e['db_eq']
        shape,flags=cover_episode(e,cal,tools,base)
        for cond in CONDITIONS:
            s=lookup[e['prompt'],cond,e['task'],e['repeat']]
            assert s['calibration_sha256']==sha(HERE/'calibration.json')
            assert s['native_reward']==e['native_reward']
            assert s['application_wire_bytes']==sum(n+5 for d,n in s['records'])
            assert sum(d=='c2s' for d,n in s['records'])==len(s['calls'])
            expect=shape if cond.startswith('shape') else e['calls']
            for a,b in zip(expect,s['calls']):
                for k in ('name','req','resp','err'):assert a[k]==b[k]
            assert len(expect)==len(s['calls'])
            if cond.startswith('shape'):assert flags==s['template_flags']
            assert [c['name'] for c in s['calls'] if c['kind']=='real']==[c['name'] for c in e['calls']]
            for c in s['calls']:
                if c['kind']=='cover':assert c['donor_task'] in split['train']
    preds=read(HERE/'predictions.json');groups=defaultdict(dict);bootgroups=defaultdict(dict)
    for p in preds:
        units=p['units'];assert len(units)==123
        assert set(u['task_id'] for u in units)==set(split['test'])
        assert all(u['task']==tasks[u['task_id']].user_id for u in units)
        y=[u['y'] for u in units];sc=p['scores'];pr=p['predictions']
        b,a=stats.distributions(units,sc,pr,2000)
        check_close(b[0],balanced_accuracy_score(y,pr));check_close(a[0],roc_auc_score(y,sc))
        key=(p['target'],p['view'],p['prompt'],p['condition'])
        assert p['attacker'] not in groups[key]
        groups[key][p['attacker']]={'ba':b[0],'auroc':a[0]};bootgroups[key][p['attacker']]=(b,a)
    res=read(HERE/'results.json');assert len(res['results'])==32
    suite={}
    for r in res['results']:
        key=(r['target'],r['view'],r['prompt'],r['condition'])
        assert set(r['attackers'])==set(groups[key])
        for name,val in groups[key].items():
            for metric,number in val.items():check_close(r['attackers'][name][metric],number)
        b=np.nanmax([v[0] for v in bootgroups[key].values()],axis=0)
        a=np.nanmax([v[1] for v in bootgroups[key].values()],axis=0);suite[key]=b
        check_close(r['suite_ba'],b[0]);check_close(r['suite_ba_ci95'],np.nanquantile(b[1:],[.025,.975]))
        check_close(r['suite_auroc'],a[0]);check_close(r['suite_auroc_ci95'],np.nanquantile(a[1:],[.025,.975]))
        assert r['invalid_single_class_bootstrap_draws']==np.isnan(b[1:]).sum()
    for d in res['prompt_differences']:
        delta=suite[d['target'],d['view'],'rules',d['condition']]-suite[d['target'],d['view'],'baseline',d['condition']]
        check_close(d['difference'],delta[0]);check_close(d['ci95'],np.nanquantile(delta[1:],[.025,.975]))
    # Validate request provenance whether raw caches or sealed per-arm archives exist.
    records=0
    for arm in PROMPTS:
        archive=HERE/('model-records-'+arm+'.zip')
        if archive.exists():
            with zipfile.ZipFile(archive) as z:
                assert z.testzip() is None
                paths=[n for n in z.namelist() if n.endswith('/request.json')]
                entries=[json.loads(z.read(n)) for n in paths]
        else:entries=[read(p) for p in (HERE/'runs'/arm).glob('*/**/request.json')]
        for q in entries:
            assert q['inference_fingerprint']==inference_fingerprint()
            assert set(q)=={'role','messages','tools','inference_fingerprint'}
        records+=len(entries)
    assert records==model_calls,(records,model_calls)
    return {'status':'VERIFIED','episodes':len(eps),'training_tasks':len(split['train']),
        'test_tasks':len(split['test']),'test_customers':len(testusers),'tls_sessions':len(S),
        'prediction_sets':len(preds),'model_calls':model_calls,'model_usage':dict(model_usage),
        'protocol_sha256':sha(HERE/'protocol.json'),'calibration_sha256':sha(HERE/'calibration.json'),
        'checks':['group disjointness','episode grid and versions','training-only calibration refit',
            'sandbox state replay','online cover reconstruction','TLS record counts/byte totals',
            'independent sklearn point metrics','customer-cluster suite intervals','paired contrasts','model request provenance']}

if __name__=='__main__':
    result=verify();print(json.dumps(result,indent=1))
