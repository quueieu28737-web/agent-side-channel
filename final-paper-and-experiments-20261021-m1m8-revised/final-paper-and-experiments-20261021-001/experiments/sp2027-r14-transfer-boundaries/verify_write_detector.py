"""Reproduce non-oracle exchange selection and retain held-out predictions."""
from pathlib import Path
import json,sys,numpy as np
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
from sklearn.metrics import balanced_accuracy_score,precision_score,recall_score
saved=en.read(D/'write_detector_results.json');output=[]
for old in saved:
 n=old['model'];split=en.read(E/n/'formal_plan.json')
 sessions=[s for s in en.read(E/n/'network_sessions.json') if s['condition']=='raw']
 def values(part):
  X=[];y=[];units=[]
  for s in sessions:
   if s['task'] not in split[part]:continue
   pairs=en.ev.exchanges(s['records']);assert len(pairs)==len(s['calls'])
   for i,(pair,c) in enumerate(zip(pairs,s['calls'])):
    X.append(pair);y.append(int(c['name'] in en.ev.WRITES));units.append({'customer':s['user'],'task':s['task'],'exchange':i})
  return np.array(X),np.array(y),units
 X,y,_=values('train');Xt,yt,units=values('test')
 model=en.ev.MODELS['logreg']();model.fit(X,y);score=model.predict_proba(Xt)[:,1];pred=(score>=.5).astype(int)
 for metric,fn in [('exchange_ba',balanced_accuracy_score),('precision',precision_score),('recall',recall_score)]:
  assert abs(old[metric]-fn(yt,pred))<1e-12
 for target,v in old['downstream'].items():
  b,_=en.stats.distributions(v['units'],np.array(v['scores']),(np.array(v['scores'])>=.5).astype(int),2000)
  assert abs(b[0]-v['ba'])<1e-12 and np.allclose(np.nanquantile(b[1:],[.025,.975]),v['ci95'])
 output.append(dict(model=n,units=units,labels=yt.tolist(),scores=score.tolist(),predictions=pred.tolist(),exchange_ba=old['exchange_ba'],precision=old['precision'],recall=old['recall']))
en.write(D/'write_detector_predictions.json',output)
en.write(D/'write_detector_verification.json',dict(passed=True,models=2,fit='Training customers only; threshold 0.5',source_results_sha256=en.sha(D/'write_detector_results.json'),predictions_sha256=en.sha(D/'write_detector_predictions.json'),downstream_point_and_intervals_recomputed=True))
print('WRITE_DETECTOR_VERIFIED')
