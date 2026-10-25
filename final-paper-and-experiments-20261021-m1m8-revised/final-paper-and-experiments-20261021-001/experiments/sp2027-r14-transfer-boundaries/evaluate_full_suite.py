from pathlib import Path
import sys,json,datetime,hashlib
import numpy as np
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
import network_replay as nr
ns,tools,base,tasks=nr.load();verbs=sorted(tools)
names=['sp2027-r11-minimax','sp2027-r12-glm'];split=en.read(E/names[0]/'formal_plan.json')
raw={n:en.read(E/n/'network_sessions.json') for n in names}
plan={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'type':'post hoc suite expansion; earlier small-suite results retained','suite':['majority','D0_gboost','D2_logreg','D2_gboost','network_decode_gboost','network_decode_count_rule','exchange_count_rule'],'fit':'Attack transfer: source model train only. Calibration transfer: target model train only under source-calibrated defense. Never fit target test.','bootstrap':2000,'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
en.write(D/'full_suite_plan.json',plan)
def get(n,c,part):return sorted([s for s in raw[n] if s['condition']==c and s['task'] in split[part]],key=lambda s:s['task'])
def assess(tr,te,clean,metadata):
 out=[]
 for label,(field,verb) in en.ev.TARGETS.items():
  y=np.array([s[field] for s in tr]);units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[field]} for s in te]
  f=lambda ss:[en.ev.net_features(s['records']) for s in ss]
  attacks={};sc=np.full(len(te),float(y.mean()>=.5));attacks['majority']=(sc,sc.astype(int))
  sc=en.predict_model(f(clean),np.array([s[field] for s in clean]),f(te),'gboost');attacks['D0_gboost']=(sc,(sc>=.5).astype(int))
  for kind in en.ev.MODELS:
   sc=en.predict_model(f(tr),y,f(te),kind);attacks['D2_'+kind]=(sc,(sc>=.5).astype(int))
  mapping=en.decoder(tr);dtr=[en.decode(s,mapping) for s in tr];dte=[en.decode(s,mapping) for s in te]
  sc=en.predict_model([en.ev.disp_features(c,verbs) for c in dtr],y,[en.ev.disp_features(c,verbs) for c in dte],'gboost');attacks['network_decode_gboost']=(sc,(sc>=.5).astype(int))
  sc,pr,th=en.count_rule([sum(c['name']==verb for c in cs) for cs in dtr],y,[sum(c['name']==verb for c in cs) for cs in dte]);attacks['network_decode_count_rule']=(sc,pr)
  sc,pr,_=en.count_rule([len(en.ev.exchanges(s['records'])) for s in tr],y,[len(en.ev.exchanges(s['records'])) for s in te]);attacks['exchange_count_rule']=(sc,pr)
  boots=[];aucs=[];scores={};metrics={}
  for name,(sc,pr) in attacks.items():
   ba,auc=en.stats.distributions(units,sc,pr,2000);boots.append(ba);aucs.append(auc);scores[name]={'scores':sc.tolist(),'predictions':pr.tolist()};metrics[name]=float(ba[0])
  b=np.fmax.reduce(boots);a=np.fmax.reduce(aucs)
  out.append(dict(**metadata,label=label,suite_ba=float(b[0]),suite_auroc=float(a[0]),ci95=np.nanquantile(b[1:],[.025,.975]).tolist(),invalid_draws=int(np.isnan(b[1:]).sum()),units=units,attacks=scores,individual_ba=metrics))
 return out
out=[]
for source in names:
 for target in names:
  for c in ['raw','shape_const']:
   out+=assess(get(source,c,'train'),get(target,c,'test'),get(source,'raw','train'),dict(study='attacker_transfer',source=source,target=target,condition=c))
for folder in sorted((D/'transfer_captures').glob('*/*/*')):
 source,target,cond=folder.parts[-3:];rows=[];cal=en.read(E/source/'network_calibration.json')
 for path in sorted(folder.glob('*.json')):
  s=en.read(path);e=en.read(E/target/'formal/baseline'/f"task-{s['task']:03d}-repeat-0/episode.json")
  calls=nr.cover_episode(e,cal,tools,base)[0] if cond=='transferred_joint' else e['calls']
  assert len(en.ev.exchanges(s['records']))==len(calls)
  s['calls']=calls;rows.append(s)
 tr=[s for s in rows if s['task'] in split['train']];te=[s for s in rows if s['task'] in split['test']]
 cost=sum(s['application_wire_bytes'] for s in te)/sum(s['application_wire_bytes'] for s in get(target,'raw','test'))
 out+=assess(tr,te,get(target,'raw','train'),dict(study='calibration_transfer',source=source,target=target,condition=cond,bytes_ratio=cost))
en.write(D/'full_suite_results.json',out)
# Independently recompute every saved point metric from saved predictions.
from sklearn.metrics import balanced_accuracy_score
for row in out:
 truth=[u['y'] for u in row['units']]
 assert abs(max(balanced_accuracy_score(truth,a['predictions']) for a in row['attacks'].values())-row['suite_ba'])<1e-12
 assert len(set(u['task_id'] for u in row['units']))==46
 assert set(u['task_id'] for u in row['units'])==set(split['test'])
en.write(D/'full_suite_verification.json',{'passed':True,'rows':len(out),'point_metrics_recomputed':True,'test_ids_checked':True,'plan_sha256':en.sha(D/'full_suite_plan.json'),'results_sha256':en.sha(D/'full_suite_results.json')})
print('FULL_SUITE_VERIFIED',len(out),flush=True)
