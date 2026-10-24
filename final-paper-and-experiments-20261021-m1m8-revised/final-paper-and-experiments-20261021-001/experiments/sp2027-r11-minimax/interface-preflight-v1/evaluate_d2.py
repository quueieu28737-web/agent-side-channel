"""Prospective second-model D2 dispatch ablations; fit train only, customer cluster bootstrap."""
from common import *
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r3'/'deps'))
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r7-agent-deps'))
import numpy as np
import e67_eval as ev
import reanalyze as stats

def suite_metrics(boot,aucboot):
 b=np.nanmax(np.asarray(boot),axis=0);a=np.nanmax(np.asarray(aucboot),axis=0)
 return {'suite_ba':float(b[0]),'suite_auroc':float(a[0]),'suite_ba_ci95':np.nanquantile(b[1:],[.025,.975]).tolist(),'suite_auroc_ci95':np.nanquantile(a[1:],[.025,.975]).tolist(),'bootstrap_draws':2000,'valid_ba_draws':int(np.isfinite(b[1:]).sum()),'valid_auroc_draws':int(np.isfinite(a[1:]).sum()),'selection':'maximum reselected separately in every shared customer bootstrap draw; conditional on fitted predictions'}

def main():
 p=read(HERE/'formal_plan.json');ns,tools,base,tasks=load();verbs=sorted(tools);out=[];preds=[];suites=[]
 for arm in PROMPTS:
  samples={part:[read(HERE/'formal'/arm/f'task-{t:03d}-repeat-0'/'episode.json') for t in p[part]] for part in ['train','test']}
  for view in ['all','writes-only','writes-removed']:
   def feat(s):
    calls=s['calls']
    if view=='writes-only':calls=[c for c in calls if c['name'] in ev.WRITES]
    if view=='writes-removed':calls=[c for c in calls if c['name'] not in ev.WRITES]
    return ev.disp_features(calls,verbs)
   Xtr=np.asarray([feat(s) for s in samples['train']],float);Xte=np.asarray([feat(s) for s in samples['test']],float)
   for target,(label,verb) in ev.TARGETS.items():
    ytr=np.array([s[label] for s in samples['train']]);yte=np.array([s[label] for s in samples['test']]);boot=[];aucboot=[]
    units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[label]} for s in samples['test']]
    majority=int(ytr.mean()>=.5);attacks={'majority':np.full(len(yte),float(majority))}
    for model_name,make in ev.MODELS.items():
     if len(set(ytr))<2:score=np.full(len(yte),float(ytr[0]))
     else:
      model=make();model.fit(Xtr,ytr);score=model.predict_proba(Xte)[:,1]
     attacks['D2_'+model_name]=score
    for model_name,score in attacks.items():
     pred=(score>=.5).astype(int);ba,auc=stats.distributions(units,score,pred,2000);boot.append(ba);aucboot.append(auc)
     out.append({'prompt':arm,'view':view,'target':target,'attacker':model_name,'ba':float(ba[0]),'auroc':float(auc[0]),'ba_ci95':np.nanquantile(ba[1:],[.025,.975]).tolist(),'test_customer_clusters':len(set(s['user'] for s in samples['test'])),'positive_customer_clusters':len(set(s['user'] for s in samples['test'] if s[label])),'fit':'train-only; fixed classifier defaults; threshold .5','valid_ba_draws':int(np.isfinite(ba[1:]).sum()),'bootstrap':'customer grouped, 2000; descriptive, few positive clusters'})
     preds.append({'prompt':arm,'view':view,'target':target,'attacker':model_name,'units':units,'scores':score.tolist(),'predictions':pred.tolist()})
    suites.append(dict(prompt=arm,view=view,target=target,attackers=list(attacks),**suite_metrics(boot,aucboot)))
 write(HERE/'D2_results.json',out);write(HERE/'D2_predictions.json',preds);write(HERE/'D2_suite.json',suites)
if __name__=='__main__':main()
