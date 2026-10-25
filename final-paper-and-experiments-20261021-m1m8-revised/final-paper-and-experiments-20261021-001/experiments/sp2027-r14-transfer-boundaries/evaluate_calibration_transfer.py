from pathlib import Path
import sys,json
import numpy as np
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
split=en.read(E/'sp2027-r12-glm/formal_plan.json');out=[]
for folder in sorted((D/'transfer_captures').glob('*/*/*')):
 rows=[en.read(p) for p in folder.glob('*.json')];assert len(rows)==115
 tr=[s for s in rows if s['task'] in split['train']];te=[s for s in rows if s['task'] in split['test']]
 source,target,condition=folder.parts[-3:]
 base={s['task']:s for s in en.read(E/target/'network_sessions.json') if s['condition']=='raw'}
 cost=sum(s['application_wire_bytes'] for s in te)/sum(base[s['task']]['application_wire_bytes'] for s in te)
 for targetlabel,(label,_) in en.ev.TARGETS.items():
  y=np.array([s[label] for s in tr]);units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[label]} for s in te]
  boots=[];predictions={}
  for kind in en.ev.MODELS:
   sc=en.predict_model([en.ev.net_features(s['records']) for s in tr],y,[en.ev.net_features(s['records']) for s in te],kind)
   ba,_=en.stats.distributions(units,sc,(sc>=.5).astype(int),2000);boots.append(ba);predictions[kind]=sc.tolist()
  sc=np.full(len(te),float(y.mean()>=.5));ba,_=en.stats.distributions(units,sc,sc.astype(int),2000);boots.append(ba)
  b=np.fmax.reduce(boots)
  out.append(dict(source=source,target=target,condition=condition,label=targetlabel,suite_ba=float(b[0]),ci95=np.nanquantile(b[1:],[.025,.975]).tolist(),invalid_draws=int(np.isnan(b[1:]).sum()),bytes_ratio=cost,units=units,scores=predictions))
(D/'calibration_transfer_results.json').write_text(json.dumps(out,indent=2,allow_nan=False))
print('CALIBRATION_EVAL',len(out))
