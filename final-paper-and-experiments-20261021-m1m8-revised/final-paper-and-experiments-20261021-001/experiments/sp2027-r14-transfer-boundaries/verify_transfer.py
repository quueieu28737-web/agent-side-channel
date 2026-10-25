"""Recompute saved transfer metrics, costs and source bindings without model calls."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
D=Path(__file__).resolve().parent; E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
from sklearn.metrics import balanced_accuracy_score,roc_auc_score
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['sp2027-r11-minimax','sp2027-r12-glm']; hashes={}; checks=0
split=en.read(E/names[0]/'formal_plan.json')
for n in names:
 assert en.read(E/n/'formal_plan.json')['train']==split['train']
 assert en.read(E/n/'formal_plan.json')['test']==split['test']
 for fn in ['formal_plan.json','network_calibration.json','network_sessions.json']:
  hashes[f'{n}/{fn}']=sha(E/n/fn)
 trainusers={en.read(p)['user'] for p in (E/n/'formal/baseline').glob('*/episode.json') if en.read(p)['task'] in split['train']}
 testusers={en.read(p)['user'] for p in (E/n/'formal/baseline').glob('*/episode.json') if en.read(p)['task'] in split['test']}
 assert not trainusers&testusers
for row in en.read(D/'full_suite_results.json'):
 units=row['units'];y=[u['y'] for u in units]
 assert set(u['task_id'] for u in units)==set(split['test']) and len(units)==46
 assert len(row['attacks'])==7
 bas=[];aucs=[]
 for name,a in row['attacks'].items():
  assert len(a['scores'])==len(a['predictions'])==46
  assert abs(balanced_accuracy_score(y,a['predictions'])-row['individual_ba'][name])<1e-12
  b,c=en.stats.distributions(units,np.array(a['scores']),np.array(a['predictions']),2000)
  bas.append(b);aucs.append(c);checks+=1
 b=np.fmax.reduce(bas);c=np.fmax.reduce(aucs)
 assert abs(b[0]-row['suite_ba'])<1e-12 and abs(c[0]-row['suite_auroc'])<1e-12
 assert np.allclose(np.nanquantile(b[1:],[.025,.975]),row['ci95'])
 if row['study']=='calibration_transfer':
  folder=D/'transfer_captures'/row['source']/row['target']/row['condition']
  captures=[en.read(p) for p in folder.glob('*.json')];assert len(captures)==115
  assert all(s['calibration_sha256']==hashes[row['source']+'/network_calibration.json'] for s in captures)
  numerator=sum(s['application_wire_bytes'] for s in captures if s['task'] in split['test'])
  raw=en.read(E/row['target']/'network_sessions.json')
  denominator=sum(s['application_wire_bytes'] for s in raw if s['condition']=='raw' and s['task'] in split['test'])
  assert abs(numerator/denominator-row['bytes_ratio'])<1e-12
  assert all(s['application_wire_bytes']==sum(n+5 for d,n in s['records']) for s in captures)
 checks+=4
for p in (D/'transfer_captures').glob('*/*/*/*.json'):hashes[p.relative_to(E).as_posix()]=sha(p)
assert len(list((D/'transfer_captures').glob('*/*/*/*.json')))==690
for name in ['full_suite_results.json','write_detector_results.json','request_field_accounting.json']:
 hashes['sp2027-r14-transfer-boundaries/'+name]=sha(D/name)
en.write(D/'verification.json',dict(passed=True,rows=28,captures=690,checks=checks,source_hashes=hashes,scope='Saved point metrics, customer intervals, test membership, calibration hashes and wire costs; no new model collection'))
print('TRANSFER_VERIFIED',checks)
