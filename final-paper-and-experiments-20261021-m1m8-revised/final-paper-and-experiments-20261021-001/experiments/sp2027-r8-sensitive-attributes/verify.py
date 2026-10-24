"""Separate implementation checks source binding, membership, model reload and metrics."""
import json,pickle,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
H=Path(__file__).resolve().parent;E=H.parent
rd=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol=rd(H/"protocol.json")
 for rel,digest in protocol["source_hashes"].items():assert sha(H/rel)==digest
 alignment=rd(H/"alignment.json")
 for rel,digest in alignment["source_hashes"].items():assert sha(E/rel)==digest
 rows=rd(H/"aligned_calls.json");instances=rd(H/"instances.json");pred=rd(H/"predictions.json");shuffled=rd(H/"shuffled_label_map.json");folds=rd(E/"sp2027-r7-crossfit/protocol.json")["fold_of_customer"]
 orders=rd(E/"tau-cover-bridge/vendor/tau_bench__envs__retail__data__orders.json");names=set(protocol["positive_native_names"])
 groups=defaultdict(list)
 for r in rows:
  assert r["verb"]=="return_delivered_order_items" and r["request_item_list_length"]==1
  o=orders[r["order_id"]];assert o["user_id"]==r["user"]
  selected=[i for i in o["items"] if i["item_id"] in r["item_ids"]];assert r["selected_has_digital_device"]==int(any(i["name"] in names for i in selected))
  p=E/r["episode_path"];assert sha(p)==r["episode_sha256"]
  c=rd(p)["calls"][r["call_index"]];assert c["name"]==r["verb"] and c["kwargs"]["item_ids"]==r["item_ids"]
  records=[]
  for direction,k in [("c2s","req"),("s2c","resp")]:
   n=len(c[k+"_text"].encode())+4
   while n: q=min(n,16384);records.append([direction,q+24]);n-=q
  assert records==r["records"]
  groups[r["prompt"],r["user"],r["order_id"],tuple(r["item_ids"])].append(r)
 assert len(groups)==len(instances)
 for r in instances:
  g=groups[r["prompt"],r["customer"],r["order"],tuple(r["items"])];assert r["call_rows"]==len(g) and r["fold"]==folds[r["customer"]]
  features=[]
  for q in g:
   v=[]
   for d in ["c2s","s2c"]:
    ns=[n for dd,n in q["records"] if dd==d];v += [len(ns),sum(ns),max(ns),min(ns)]
   features.append(v)
  assert np.array_equal(np.mean(features,axis=0),r["x"])
 index={(r["prompt"],r["condition"],r["instance"]):r for r in pred};checked=0
 for p in pickle.loads((H/"models.pkl").read_bytes()):
  assert not ({r["customer"] for r in p["train"]}&{r["customer"] for r in p["test"]})
  assert all(r["fold"]!=p["fold"] for r in p["train"]) and all(r["fold"]==p["fold"] for r in p["test"])
  condition=p["condition"]
  xx=lambda r:r["x"] if condition in ["raw","shuffled_labels"] else ([r["order_count"]] if condition=="order_count_only" else [0.]*8)
  for n,m in p["models"].items():
   if not p["test"]:continue
   scores=m.predict_proba([xx(r) for r in p["test"]])[:,1]
   for r,sc in zip(p["test"],scores):
    saved=index[p["prompt"],condition,r["instance"]];assert saved["attacks"][n]["score"]==float(sc);assert saved["attacks"][n]["pred"]==int(sc>=.5);assert saved["evaluation_y"]==(shuffled[r["instance"]] if condition=="shuffled_labels" else r["y"]);checked+=1
 for report in rd(H/"results.json"):
  rr=[r for r in pred if r["prompt"]==report["prompt"] and r["condition"]==report["condition"]]
  assert len(rr)==report["instances"] and len({r["customer"] for r in rr})==report["customers"]
  for n,s in report["learners"].items():
   rates=[]
   for y in [0,1]:
    q=[r for r in rr if r["evaluation_y"]==y];rates.append(sum(r["attacks"][n]["pred"]==y for r in q)/len(q))
   assert abs(sum(rates)/2-s["ba"])<1e-15
  customers=sorted({r["customer"] for r in rr});rng=np.random.default_rng(20261024);draws=defaultdict(list);maxima=[]
  for _ in range(2000):
   weights=Counter(rng.choice(customers,len(customers),replace=True));den={y:sum(weights[r["customer"]] for r in rr if r["evaluation_y"]==y) for y in [0,1]}
   if not all(den.values()):continue
   vals=[]
   for n in report["learners"]:
    ba=sum(sum(weights[r["customer"]] for r in rr if r["evaluation_y"]==y and r["attacks"][n]["pred"]==y)/den[y] for y in [0,1])/2;draws[n].append(ba);vals.append(ba)
   maxima.append(max(vals))
  for n in draws:assert np.allclose(np.quantile(draws[n],[.025,.975]),report["learners"][n]["ci95"],rtol=0,atol=1e-15)
  assert np.allclose(np.quantile(maxima,[.025,.975]),report["suite_max_ci95"],rtol=0,atol=1e-15)
 conf=[]
 for arm in ["baseline","rules"]:
  rr=[r for r in instances if r["prompt"]==arm]
  for count in sorted({r["order_count"] for r in rr}):
   q=[r for r in rr if r["order_count"]==count];conf.append(dict(prompt=arm,initial_order_item_rows=count,instances=len(q),positive_instances=sum(r["y"] for r in q),negative_instances=sum(not r["y"] for r in q),customers=len({r["customer"] for r in q})))
 (H/"confounding_support.json").write_text(json.dumps(conf,indent=2))
 receipt=dict(passed=True,exact_reloaded_scores=checked,aligned_calls=len(rows),aggregated_instances=len(instances),models=150,bootstrap_recomputed=True,group_disjoint=True,source_hashes_verified=True,output_sha256={n:sha(H/n) for n in ["instances.json","predictions.json","results.json","models.pkl","confounding_support.json"]})
 (H/"verification.json").write_text(json.dumps(receipt,indent=2));print(receipt)
if __name__=="__main__":main()
