from pathlib import Path
import sys,json,hashlib,datetime
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
import numpy as np
models=['sp2027-r11-minimax','sp2027-r12-glm']
data={m:en.read(E/m/'network_sessions.json') for m in models}
split=en.read(E/models[0]/'formal_plan.json')
manifest={m:hashlib.sha256((E/m/'network_sessions.json').read_bytes()).hexdigest() for m in models}
(D/'analysis_plan.json').write_text(json.dumps({'scope':'Post hoc source-model-trained attackers evaluated on target-model held-out customers; target model defense remains locally calibrated, not calibration transfer','conditions':['raw','shape_const'],'learners':list(en.ev.MODELS),'bootstrap':2000,'sources':manifest,'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
results=[];predictions=[]
for source in models:
 for target in models:
  for cond in ['raw','shape_const']:
   tr=[s for s in data[source] if s['condition']==cond and s['task'] in split['train']]
   te=[s for s in data[target] if s['condition']==cond and s['task'] in split['test']]
   assert len(tr)==69 and len(te)==46
   for label,(field,verb) in en.ev.TARGETS.items():
    y=np.array([s[field] for s in tr]);units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[field]} for s in te]
    boots=[];details={}
    for kind in en.ev.MODELS:
     scores=en.predict_model([en.ev.net_features(s['records']) for s in tr],y,[en.ev.net_features(s['records']) for s in te],kind)
     ba,auc=en.stats.distributions(units,scores,(scores>=.5).astype(int),2000);boots.append(ba)
     details[kind]=float(ba[0]);predictions.append(dict(source=source,target=target,condition=cond,label=label,learner=kind,units=units,scores=scores.tolist()))
    # Majority is fitted using source training labels only.
    sc=np.full(len(te),float(y.mean()>=.5));ba,_=en.stats.distributions(units,sc,sc.astype(int),2000);boots.append(ba)
    b=np.nanmax(boots,axis=0)
    results.append(dict(source=source,target=target,condition=cond,label=label,suite_ba=float(b[0]),ci95=np.nanquantile(b[1:],[.025,.975]).tolist(),learners=details))
(D/'attack_transfer_results.json').write_text(json.dumps(results,indent=2))
(D/'attack_transfer_predictions.json').write_text(json.dumps(predictions))
print('TRANSFER_COMPLETE',len(results),flush=True)
