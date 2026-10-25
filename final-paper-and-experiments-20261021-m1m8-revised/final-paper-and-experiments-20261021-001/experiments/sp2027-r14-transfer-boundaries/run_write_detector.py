from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
from sklearn.metrics import balanced_accuracy_score,precision_score,recall_score
out=[]
for name in ['sp2027-r11-minimax','sp2027-r12-glm']:
 split=en.read(E/name/'formal_plan.json');sessions=[s for s in en.read(E/name/'network_sessions.json') if s['condition']=='raw']
 tr=[s for s in sessions if s['task'] in split['train']];te=[s for s in sessions if s['task'] in split['test']]
 def exchanges(ss):
  X=[];y=[]
  for s in ss:
   pairs=en.ev.exchanges(s['records']);assert len(pairs)==len(s['calls'])
   for pair,c in zip(pairs,s['calls']):X.append(pair);y.append(int(c['name'] in en.ev.WRITES))
  return np.array(X),np.array(y)
 X,y=exchanges(tr);Xt,yt=exchanges(te)
 model=en.ev.MODELS['logreg']();model.fit(X,y);pred=(model.predict_proba(Xt)[:,1]>=.5).astype(int)
 result=dict(model=name,exchange_ba=balanced_accuracy_score(yt,pred),precision=precision_score(yt,pred,zero_division=0),recall=recall_score(yt,pred,zero_division=0),test_exchanges=len(yt),downstream={})
 def feat(ss):
  features=[]
  for s in ss:
   pairs=np.array(en.ev.exchanges(s['records']))
   selected=pairs[model.predict_proba(pairs)[:,1]>=.5] if len(pairs) else np.zeros((0,2))
   features.append([len(selected),*(np.sum(selected,axis=0) if len(selected) else [0,0]),*(np.mean(selected,axis=0) if len(selected) else [0,0])])
  return features
 for target,(lab,_) in en.ev.TARGETS.items():
  scores=en.predict_model(feat(tr),np.array([s[lab] for s in tr]),feat(te),'logreg')
  units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[lab]} for s in te]
  ba,_=en.stats.distributions(units,scores,(scores>=.5).astype(int),2000)
  result['downstream'][target]={'ba':float(ba[0]),'ci95':np.nanquantile(ba[1:],[.025,.975]).tolist(),'scores':scores.tolist(),'units':units}
 out.append(result)
(D/'write_detector_results.json').write_text(json.dumps(out,indent=2))
print('NON_ORACLE_COMPLETE')
