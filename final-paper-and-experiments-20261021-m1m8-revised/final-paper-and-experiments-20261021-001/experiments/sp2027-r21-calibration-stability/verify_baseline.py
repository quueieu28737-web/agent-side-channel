"""Verify resampling implementation against all original seven-attack points."""
import run as r
import numpy as np
from itertools import product
from sklearn.metrics import balanced_accuracy_score
from analyze import cluster_contributions
r.init();checked=0
old=[x for x in r.nr.read(r.OLD/'full_suite_results.json') if x['study']=='calibration_transfer']
for source in r.NAMES:
    r.nr.HERE=r.E/source
    tr=[e for e in r.EPISODES[source] if e['task'] in r.SPLIT['train']]
    cal=r.nr.fit_calibration(tr,r.NS,r.TOOLS,r.BASE);original=r.nr.read(r.E/source/'network_calibration.json')
    for key in ['template','caps','donors','calibration_lengths','shape_emit_probability']:
        assert cal[key]==original[key],(source,key)
for folder in sorted((r.OLD/'transfer_captures').glob('*/*/*')):
    source,target,condition=folder.parts[-3:];cal=r.nr.read(r.E/source/'network_calibration.json');ee={e['task']:e for e in r.EPISODES[target]};rows=[]
    for path in sorted(folder.glob('*.json')):
        s=r.nr.read(path);e=ee[s['task']]
        s['calls']=r.nr.cover_episode(e,cal,r.TOOLS,r.BASE)[0] if condition=='transferred_joint' else e['calls']
        rows.append(s)
    tr=[s for s in rows if s['task'] in r.SPLIT['train']];te=[s for s in rows if s['task'] in r.SPLIT['test']]
    clean=[s for s in r.RAW[target] if s['task'] in r.SPLIT['train']]
    new=r.fit(tr,te,clean)
    for label,m in new.items():
        o=next(x for x in old if x['source']==source and x['target']==target and x['condition']==condition and x['label']==label)
        assert abs(m['suite_ba']-o['suite_ba'])<1e-12
        for a,p in m['predictions'].items():assert p==o['attacks'][a]['predictions'],(source,target,condition,label,a)
        assert abs(max(balanced_accuracy_score(m['y'],p) for p in m['predictions'].values())-m['suite_ba'])<1e-12
        checked+=1
# Enumerate every exchangeability swap in a small clustered two-attacker example.
y=[0,1,1,0,1,0];users=['a','a','b','b','c','c']
ap=np.array([[0,1,0,0,1,1],[1,1,1,0,0,0]])
bp=np.array([[1,1,1,0,0,1],[0,0,1,1,1,0]])
def row(p):return {'units':[{'task':u,'y':v} for u,v in zip(users,y)],'attacks':{str(i):{'predictions':a.tolist()} for i,a in enumerate(p)}}
A=cluster_contributions(row(ap));B=cluster_contributions(row(bp))
for bits in product([0,1],repeat=3):
    delta=np.array(bits)@(B-A);fast=(B.sum(0)-delta).max()-(A.sum(0)+delta).max()
    swap=np.array([bits[['a','b','c'].index(u)] for u in users],bool)
    pa=np.where(swap,bp,ap);pb=np.where(swap,ap,bp)
    slow=max(balanced_accuracy_score(y,p) for p in pb)-max(balanced_accuracy_score(y,p) for p in pa)
    assert abs(fast-slow)<1e-12
r.nr.write(r.D/'baseline_verification.json',{'passed':True,'original_calibrators_exact':2,'original_endpoint_rows_exact':checked,'original_attacker_prediction_arrays_exact':checked*7,'permutation_exhaustive_synthetic_checks':8})
print('BASELINE_AND_PERMUTATION_VERIFIED',checked)
