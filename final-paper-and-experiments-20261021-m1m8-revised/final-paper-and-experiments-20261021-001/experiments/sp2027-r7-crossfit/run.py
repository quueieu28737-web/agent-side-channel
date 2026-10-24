import os,sys,json,hashlib,time,pickle,zipfile,inspect
from pathlib import Path
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'sp2027-r5-crossfit'))
import r5lib as L
from e10_crossfit import folds_of
sys.path.insert(0,str(HERE.parent/'sp2027-r7-robustness'))
from learners import SequenceAttack,LeafKNN,feature
import numpy as np
from collections import defaultdict

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf8')
def key(s):return f"{s['prompt']}-t{s['task']:03d}-r{s['repeat']}"
def adapt(s):return dict(s,records=[(1 if d=='c2s' else -1,n,0) for d,n in s['records']])
def main():
 rows,_=L.all_episodes();fold=folds_of(rows);_,tools,base,_=L.load();verbs=sorted(tools)
 frozen=HERE/'protocol.json'
 protocol={'status':'posthoc known cohort; not preregistered or confirmatory','cohort_episodes':len(rows),'fold_of_customer':fold,'views':['network'],'conditions':['undefended','jointconstant','jointbucket1024'],'targets':['cancel','return'],'arms':['baseline','rules'],'timing':'All R5 records have direction,length only. Third column is constant zero; no measured or synthetic timing signal.','new_attacks':'Fixed imported 1D CNN 50 epochs head/tail 512 + aggregate pooling; k-FP-style 200-tree leaf fingerprint 3NN.','bootstrap':'2000 common customer cluster draws; reselect max across full old extended suite and both new attacks in every draw; conditional on trained models','source_hashes':{str(p):sha(p) for p in [Path(__file__),Path(L.__file__),HERE.parent/'sp2027-r5-crossfit/e10_crossfit.py',HERE.parent/'sp2027-r7-robustness/learners.py',HERE.parent/'sp2027-r7-robustness/r7common.py']}}
 if frozen.exists():assert json.loads(frozen.read_text())==protocol
 else:write(frozen,protocol)
 oof=defaultdict(lambda:defaultdict(lambda:[[],[]]));order=defaultdict(list);cost=defaultdict(lambda:dict(wire=0,calls=0,raw_wire=0,raw_calls=0));calibrations=[]
 for k in range(5):
  train=[e for e in rows if fold[e['user']]!=k];test=[e for e in rows if fold[e['user']]==k]
  for cfg in L.FRONTIER[:2]:
   condition='jointconstant' if cfg['name']=='r4' else 'jointbucket1024'
   cal=L.fit_calibration(train,tools,base,cfg)
   calibrations.append(dict(fold=k,config=cfg['name'],calibration=cal,train_customers=sorted({e['user'] for e in train}),test_customers=sorted({e['user'] for e in test})))
   sess={key(e):L.make_sessions(e,cal,cfg,tools,base,['raw','shape_const']) for e in rows}
   conditions=[('shape_const',condition)]+([('raw','undefended')] if cfg['name']=='r4' else [])
   for oldcond,cond in conditions:
    for arm in ['baseline','rules']:
     tr=[sess[key(e)][oldcond] for e in train if e['prompt']==arm];te=[sess[key(e)][oldcond] for e in test if e['prompt']==arm];raw=[sess[key(e)]['raw'] for e in train if e['prompt']==arm]
     c=cost[arm,cond]
     for e in test:
      if e['prompt']==arm:
       s=sess[key(e)][oldcond];r=sess[key(e)]['raw'];c['wire']+=s['wire'];c['calls']+=len(s['calls']);c['raw_wire']+=r['wire'];c['raw_calls']+=len(r['calls'])
     for target,(lab,verb) in L.ev.TARGETS.items():
      t=time.time();tag=f'f{k}-{cond}-{arm}-{target}';out=HERE/(tag+'.zip')
      if out.exists():
       with zipfile.ZipFile(out) as z:bundle=pickle.loads(z.read('bundle.pkl'))
       att=bundle['attacks']
      else:
       ns=dict(L.__dict__);ns['AUDIT_MODELS']=[]
       source=inspect.getsource(L.attack_suite).replace('mdl.fit(np.asarray(Xa, float), ya)','mdl.fit(np.asarray(Xa, float), ya); AUDIT_MODELS.append((mdl,np.asarray(Xb,float)))')
       exec(source,ns);att=ns['attack_suite'](tr,te,raw,lab,verb,'network',verbs,True)
       y=np.array([s[lab] for s in tr]);atr=list(map(adapt,tr));ate=list(map(adapt,te))
       cnn=SequenceAttack().fit(atr,y);fp=LeafKNN().fit(list(map(feature,atr)),y)
       for name,model,x in [('ext_D2_cnn',cnn,ate),('ext_D2_kfp_style',fp,list(map(feature,ate)))]:
        sc=model.predict_proba(x)[:,1];att[name]=(sc,(sc>=.5).astype(int))
       bundle=dict(attacks=att,old_models=ns['AUDIT_MODELS'],cnn=cnn,fp=fp,test=te,train=tr,raw=raw,lab=lab,verb=verb,verbs=verbs,fold=k)
       with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('bundle.pkl',pickle.dumps(bundle,protocol=5))
      cell=(target,arm,cond);order[cell]+=te
      for name,(sc,pr) in att.items():oof[cell][name][0].extend(map(float,sc));oof[cell][name][1].extend(map(int,pr))
      print(tag,'seconds',round(time.time()-t,1),flush=True)
 results=[];draws={};predictions=[]
 for cell,att in oof.items():
  target,arm,cond=cell;units=L.units_of(order[cell],L.ev.TARGETS[target][0]);summary,cb,eb=L.summarize(units,att);draws[cell]=eb
  c=cost[arm,cond];results.append(dict(target=target,prompt=arm,condition=cond,n=len(units),customers=len({x['task'] for x in units}),bytes_ratio=c['wire']/c['raw_wire'],calls_ratio=c['calls']/c['raw_calls'],**summary))
  for i,s in enumerate(order[cell]):predictions.append(dict(episode=key(s),customer=s['user'],fold=fold[s['user']],target=target,prompt=arm,condition=cond,y=int(s[L.ev.TARGETS[target][0]]),attacks={a:dict(score=v[0][i],pred=v[1][i]) for a,v in att.items()}))
 contrasts=[]
 for target in L.ev.TARGETS:
  for arm in ['baseline','rules']:
   for cond in ['jointconstant','jointbucket1024']:
    d=draws[target,arm,'undefended']-draws[target,arm,cond];contrasts.append(dict(target=target,prompt=arm,contrast='undefended minus '+cond,ba_decrease=float(d[0]),ci95=list(map(float,np.nanquantile(d[1:],[.025,.975])))))
 write(HERE/'results.json',dict(protocol_sha256=sha(frozen),results=results,paired_decreases=contrasts));write(HERE/'predictions.json',predictions);write(HERE/'calibrations.json',calibrations)
 lines=['|Target|Arm|Condition|Suite max BA (95% CI)|AUROC|Wire ×|Calls ×|','|---|---|---|---|---|---|---|']
 for r in results:lines.append(f"|{r['target']}|{r['prompt']}|{r['condition']}|{r['ext_ba']:.6f} [{r['ext_ba_ci95'][0]:.6f}, {r['ext_ba_ci95'][1]:.6f}]|{r['ext_auroc']:.6f}|{r['bytes_ratio']:.6f}|{r['calls_ratio']:.6f}|")
 (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
if __name__=='__main__':main()

