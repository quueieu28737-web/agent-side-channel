"""Independent posthoc R7 oracle localization; run only after crossfit verification."""
import os,sys,json,hashlib,time,pickle,zipfile,inspect
from pathlib import Path,PureWindowsPath
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
HERE=Path(__file__).resolve().parent;PACKAGE=HERE.parents[1];CROSS=HERE.parent/'sp2027-r7-crossfit'
sys.path.insert(0,str(HERE.parent/'sp2027-r5-crossfit'))
import r5lib as L
from e10_crossfit import folds_of
from e12_localization import session,VIEWS
sys.path.insert(0,str(HERE.parent/'sp2027-r7-robustness'))
from learners import SequenceAttack,LeafKNN,feature
import numpy as np
from collections import defaultdict

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf8')
def key(s):return f"{s['prompt']}-t{s['task']:03d}-r{s['repeat']}"
def adapt(s):return dict(s,records=[(1 if d=='c2s' else -1,n,0) for d,n in s['records']])
def relative(p):return Path(p).resolve().relative_to(PACKAGE).as_posix()
def main():
 assert json.loads((CROSS/'verification.json').read_text())['passed']
 rows,_=L.all_episodes();assert len(rows)==690;fold=folds_of(rows);_,tools,_,_=L.load();verbs=sorted(tools)
 files=[Path(__file__),HERE/'PLAN.md',HERE.parent/'sp2027-r5-crossfit/r5lib.py',HERE.parent/'sp2027-r5-crossfit/e10_crossfit.py',HERE.parent/'sp2027-r5-crossfit/e12_localization.py',HERE.parent/'sp2027-r7-robustness/learners.py',HERE.parent/'sp2027-r7-robustness/r7common.py']
 files += [CROSS/n for n in ['protocol.json','predictions.json','detailed_results.json','verification.json']]
 files += [p for p in (HERE.parent/'sp2027-r6-timing').glob('*.py')]
 files += [CROSS/'inputs_manifest.json',CROSS/'portable-path-map.json']
 prefix=PureWindowsPath(json.loads((CROSS/'portable-path-map.json').read_text(encoding='utf-8-sig'))['original_package_root'])
 for oldpath,digest in json.loads((CROSS/'inputs_manifest.json').read_text())['sha256'].items():
  p=PACKAGE.joinpath(*PureWindowsPath(oldpath).relative_to(prefix).parts);assert sha(p)==digest;files.append(p)
 protocol={'status':'posthoc known original Sol cohort; not preregistered or confirmatory','episodes':690,'fold_of_customer':fold,'views':['writes_only','no_writes'],'filter':'Exactly original E12 session/VIEWS; oracle removal or retention of complete raw write exchanges using true call names, before TLS reconstruction. Not a deployable observer defense.','calibration':'No defense calibration applies to undefended oracle ablation. Every attack fits only training customers.','timing':'Direction and length only. c2s/s2c map +1/-1; third timing channel exactly zero; presence mask only records existence.','learners':'9 complete legacy extended network attacks + fixed 50-epoch 512 head/tail CNN + 200-tree leaf-fingerprint 3NN k-FP-style','bootstrap':'2000 common customer cluster draws; reselect 11-attack maximum on every draw; paired full minus ablation; conditional on fitted attacks','full_reference':'Same original R5 folds and raw sessions from completed R7 crossfit undefended OOF; all 11 attacks','source_hashes':{relative(p):sha(p) for p in files}}
 if (HERE/'protocol.json').exists():assert json.loads((HERE/'protocol.json').read_text())==protocol
 else:write(HERE/'protocol.json',protocol)
 sessions={v:{key(e):session(e,VIEWS[v]) for e in rows} for v in ['writes_only','no_writes']}
 for v,ss in sessions.items():
  for e in rows:
   s=ss[key(e)];expected=[c for c in e['calls'] if VIEWS[v](c)];assert len(expected)==len(s['calls'])
   assert all(c['name'] in L.ev.WRITES for c in s['calls']) if v=='writes_only' else all(c['name'] not in L.ev.WRITES for c in s['calls'])
 oof=defaultdict(lambda:defaultdict(lambda:[[],[]]));order=defaultdict(list)
 for k in range(5):
  for view in ['writes_only','no_writes']:
   for arm in ['baseline','rules']:
    tr=[sessions[view][key(e)] for e in rows if e['prompt']==arm and fold[e['user']]!=k];te=[sessions[view][key(e)] for e in rows if e['prompt']==arm and fold[e['user']]==k]
    for target,(lab,verb) in L.ev.TARGETS.items():
     t=time.time();tag=f'f{k}-{view}-{arm}-{target}';path=HERE/(tag+'.zip')
     if path.exists():
      with zipfile.ZipFile(path) as z:b=pickle.loads(z.read('bundle.pkl'))
      att=b['attacks']
     else:
      ns=dict(L.__dict__);ns['AUDIT_MODELS']=[];source=inspect.getsource(L.attack_suite).replace('mdl.fit(np.asarray(Xa, float), ya)','mdl.fit(np.asarray(Xa, float), ya); AUDIT_MODELS.append((mdl,np.asarray(Xb,float)))');exec(source,ns)
      att=ns['attack_suite'](tr,te,tr,lab,verb,'network',verbs,True);y=np.array([s[lab] for s in tr]);atr=list(map(adapt,tr));ate=list(map(adapt,te));cnn=SequenceAttack().fit(atr,y);fp=LeafKNN().fit(list(map(feature,atr)),y)
      for name,model,x in [('ext_D2_cnn',cnn,ate),('ext_D2_kfp_style',fp,list(map(feature,ate)))]:
       sc=model.predict_proba(x)[:,1];att[name]=(sc,(sc>=.5).astype(int))
      b=dict(attacks=att,old_models=ns['AUDIT_MODELS'],cnn=cnn,fp=fp,test=te,train=tr,lab=lab,verb=verb,verbs=verbs,fold=k,view=view,target=target)
      with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('bundle.pkl',pickle.dumps(b,protocol=5))
     cell=(target,arm,view);order[cell]+=te
     for name,(sc,pr) in att.items():oof[cell][name][0].extend(map(float,sc));oof[cell][name][1].extend(map(int,pr))
     print(tag,'seconds',round(time.time()-t,1),flush=True)
 predictions=[]
 for (target,arm,view),att in oof.items():
  for i,s in enumerate(order[target,arm,view]):predictions.append(dict(episode=key(s),customer=s['user'],task=s['task'],repeat=s['repeat'],fold=fold[s['user']],target=target,prompt=arm,view=view,y=int(s[L.ev.TARGETS[target][0]]),attacks={n:dict(score=v[0][i],pred=v[1][i]) for n,v in att.items()}))
 write(HERE/'predictions.json',predictions)
 retained=[]
 for arm in ['baseline','rules']:
  full=[e for e in rows if e['prompt']==arm];fullcalls=sum(len(e['calls']) for e in full);fullwire=sum(sum(n+5 for d,n in session(e,VIEWS['full'])['records']) for e in full)
  for view in ['writes_only','no_writes']:
   ss=[sessions[view][key(e)] for e in full];retained.append(dict(prompt=arm,view=view,calls=sum(len(s['calls']) for s in ss),wire=sum(sum(n+5 for d,n in s['records']) for s in ss),calls_fraction=sum(len(s['calls']) for s in ss)/fullcalls,wire_fraction=sum(sum(n+5 for d,n in s['records']) for s in ss)/fullwire))
 write(HERE/'retained_fraction.json',retained);write(HERE/'run_complete.json',dict(protocol_sha256=sha(HERE/'protocol.json'),bundles=40,prediction_rows=len(predictions)))
if __name__=='__main__':main()


