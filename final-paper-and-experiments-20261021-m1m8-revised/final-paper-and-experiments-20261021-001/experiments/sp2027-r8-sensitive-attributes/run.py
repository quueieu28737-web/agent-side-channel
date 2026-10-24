"""Fixed exploratory R8 fits; execute only against frozen protocol."""
import os
for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"):os.environ[k]="1"
import json,hashlib,pickle
from pathlib import Path
from collections import defaultdict
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
H=Path(__file__).resolve().parent;E=H.parent
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
def write(n,x):(H/n).write_text(json.dumps(x,indent=2,allow_nan=False),encoding="utf8")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def feature(r):
 out=[]
 for d in ["c2s","s2c"]:
  v=[n for dd,n in r["records"] if dd==d]
  out += [len(v),sum(v),max(v),min(v)]
 return out

def dataset():
 rr=read(H/"aligned_calls.json");fold=read(E/"sp2027-r7-crossfit/protocol.json")["fold_of_customer"];groups=defaultdict(list)
 for r in rr:groups[r["prompt"],r["user"],r["order_id"],tuple(r["item_ids"])].append(r)
 ds=[]
 for (arm,u,o,items),rs in sorted(groups.items()):
  assert len({r["selected_has_digital_device"] for r in rs})==1
  ds.append(dict(prompt=arm,customer=u,order=o,items=list(items),instance="|".join([u,o,*items]),y=rs[0]["selected_has_digital_device"],fold=fold[u],x=np.mean([feature(r) for r in rs],axis=0).tolist(),order_count=rs[0]["order_item_rows"],call_rows=len(rs),episodes=len({r["episode"] for r in rs}),tasks=sorted({r["task"] for r in rs}),repeats=sorted({r["repeat"] for r in rs})))
 return ds

def learners():return {"LR":make_pipeline(StandardScaler(),LogisticRegression(C=1.,class_weight="balanced",solver="liblinear",random_state=20261024,max_iter=1000)),"RF":RandomForestClassifier(n_estimators=200,max_depth=3,min_samples_leaf=2,class_weight="balanced",random_state=20261024,n_jobs=1),"GB":GradientBoostingClassifier(n_estimators=50,max_depth=1,learning_rate=.05,random_state=20261024)}

def metric(y,p,w):
 p=np.array(p);y=np.array(y);w=np.array(w)
 a=w[y==1].sum();b=w[y==0].sum()
 if not a or not b:return None
 return float(.5*((w*((y==1)&(p==1))).sum()/a+(w*((y==0)&(p==0))).sum()/b))

def summarize(pred):
 results=[]
 for arm in ["baseline","rules"]:
  for condition in ["raw","operation_constant","constant_size","order_count_only","shuffled_labels"]:
   r=[x for x in pred if x["prompt"]==arm and x["condition"]==condition];customers=sorted({x["customer"] for x in r});rng=np.random.default_rng(20261024);bs=[]
   for _ in range(2000):
    draw=rng.choice(customers,len(customers),replace=True);ct={u:int(sum(draw==u)) for u in customers};bs.append([ct[x["customer"]] for x in r])
   y=[x["evaluation_y"] for x in r];att={n:[x["attacks"][n]["pred"] for x in r] for n in ["LR","RF","GB"]};points={n:metric(y,p,[1]*len(r)) for n,p in att.items()};stats={}
   draws={n:[z for w in bs if (z:=metric(y,p,w)) is not None] for n,p in att.items()}
   for n in att:stats[n]={"ba":points[n],"ci95":np.quantile(draws[n],[.025,.975]).tolist(),"valid_bootstrap":len(draws[n])}
   maxdraw=[max(v) for w in bs if (v:=[z for p in att.values() if (z:=metric(y,p,w)) is not None])]
   results.append(dict(prompt=arm,condition=condition,instances=len(r),customers=len(customers),positive_instances=sum(y),negative_instances=len(y)-sum(y),positive_customers=len({x["customer"] for x in r if x["evaluation_y"]}),negative_customers=len({x["customer"] for x in r if not x["evaluation_y"]}),learners=stats,suite_max=max(points.values()),winner=max(points,key=points.get),suite_max_ci95=np.quantile(maxdraw,[.025,.975]).tolist(),bootstrap="2000 fixed-prediction customer draws, one-class draws omitted; suite max reselected per draw, no refitting"))
 return results

def main():
 protocol=read(H/"protocol.json")
 for rel,digest in protocol["source_hashes"].items():assert sha(H/rel)==digest,rel
 ds=dataset();write("instances.json",ds)
 label={r["instance"]:r["y"] for r in ds};byfold=defaultdict(list)
 for r in ds:
  if r["instance"] not in byfold[r["fold"]]:byfold[r["fold"]].append(r["instance"])
 rng=np.random.default_rng(20261024);shuffled={}
 for f,ids in sorted(byfold.items()):
  ids=sorted(ids);vals=rng.permutation([label[i] for i in ids]);shuffled.update({i:int(v) for i,v in zip(ids,vals)})
 write("shuffled_label_map.json",shuffled);pred=[];models=[]
 for arm in ["baseline","rules"]:
  rs=[r for r in ds if r["prompt"]==arm]
  for condition in ["raw","operation_constant","constant_size","order_count_only","shuffled_labels"]:
   for fold in range(5):
    tr=[r for r in rs if r["fold"]!=fold];te=[r for r in rs if r["fold"]==fold]
    def xx(r):return r["x"] if condition in ["raw","shuffled_labels"] else ([r["order_count"]] if condition=="order_count_only" else [0.]*8)
    yy=lambda r:shuffled[r["instance"]] if condition=="shuffled_labels" else r["y"]
    assert len({yy(r) for r in tr})==2
    pack=learners()
    out={}
    for n,m in pack.items():
     m.fit([xx(r) for r in tr],[yy(r) for r in tr]);sc=m.predict_proba([xx(r) for r in te])[:,1] if te else [];out[n]=sc
    models.append(dict(prompt=arm,condition=condition,fold=fold,models=pack,train=tr,test=te))
    for i,r in enumerate(te):pred.append(dict(r,condition=condition,evaluation_y=yy(r),attacks={n:{"score":float(out[n][i]),"pred":int(out[n][i]>=.5)} for n in pack}))
 (H/"models.pkl").write_bytes(pickle.dumps(models,protocol=5));write("predictions.json",pred);write("results.json",summarize(pred));print(json.dumps(read(H/"results.json"),indent=2))
if __name__=="__main__":main()
