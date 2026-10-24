"""Refit all E14 new learners, compare saved test scores; no model/API collection."""
from pathlib import Path
import sys, json, hashlib
O=Path(__file__).resolve().parent;D=O.parents[1]/'experiments/sp2027-r7-robustness'
sys.path.insert(0,str(D))
from run import model, feature, tabular, SequenceAttack
from r7common import rows, read, sha, source_hashes, CONDITIONS, write, now
import numpy as np

frozen=read(D/'freeze.json');assert frozen['source_sha256']==source_hashes()
tr=rows('train');te=rows('test');pred=read(D/'predictions.json');completed=[]
for arm in ('baseline','rules'):
 for cond in CONDITIONS:
  a=[r for r in tr if r['prompt']==arm and r['condition']==cond]
  b=[r for r in te if r['prompt']==arm and r['condition']==cond]
  X=[feature(r) for r in a];Z=[feature(r) for r in b]
  for target in ('cancel','return'):
   k='|'.join((arm,cond,target));y=np.array([r['has_'+target] for r in a])
   old=model(k.replace('|','-')+'.joblib');new=tabular()
   for m in new.values():m.fit(X,y)
   new['D2_sequence_CNN']=SequenceAttack().fit(a,y)
   for name,m in new.items():
    inp=b if name=='D2_sequence_CNN' else Z
    s=m.predict_proba(inp)[:,1]
    assert np.array_equal(s,np.array(pred[k]['models'][name]['scores'])),('Refit differs',k,name)
    assert np.array_equal(s,old['models'][name].predict_proba(inp)[:,1]),('Archived model differs',k,name)
    assert np.array_equal((s>=.5).astype(int),pred[k]['models'][name]['predictions'])
   completed.append(k);print('EXACT_REFIT',k,flush=True)
result={'status':'ALL_312_NEW_LEARNERS_EXACTLY_REFIT_AND_RELOADED','completed_cells':len(completed),
 'learners_per_cell':6,'test_predictions_per_cell':138,'utc':now(),'source_sha256':source_hashes(),
 'freeze_sha256':sha(D/'freeze.json'),'predictions_sha256':sha(D/'predictions.json'),
 'model_archive_sha256':sha(D/'models.zip'),'script_sha256':sha(Path(__file__))}
assert len(completed)==52
write(D/'retraining_validation.json',result);print(json.dumps(result),flush=True)
