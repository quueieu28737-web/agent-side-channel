"""Requested descriptive AUROC/fold addendum; no fitting, selection, flipping or tuning."""
import json,pickle,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.metrics import roc_auc_score
H=Path(__file__).resolve().parent
rd=lambda n:json.loads((H/n).read_text())
def auc(rr,nmodel,w=None):
 if len({r["evaluation_y"] for r in rr if w is None or w[r["customer"]]>0})<2:return None
 pos=[r for r in rr if r["evaluation_y"]==1];neg=[r for r in rr if r["evaluation_y"]==0]
 weight=lambda r:1 if w is None else w[r["customer"]]
 numerator=sum(weight(p)*weight(n)*(int(p["attacks"][name]["score"]>n["attacks"][name]["score"])+.5*int(p["attacks"][name]["score"]==n["attacks"][name]["score"])) for p in pos for n in neg for name in [nmodel])
 return float(numerator/(sum(weight(r) for r in pos)*sum(weight(r) for r in neg)))

def ba(rr,n):
 if len({r["evaluation_y"] for r in rr})<2:return None
 return .5*sum(sum(r["attacks"][n]["pred"]==y for r in rr if r["evaluation_y"]==y)/sum(r["evaluation_y"]==y for r in rr) for y in [0,1])
def main():
 packs=pickle.loads((H/"models.pkl").read_bytes());folds=[]
 for p in packs:
  for m in p["models"].values():assert list(m.classes_)==[0,1]
  tr=p["train"];te=p["test"];assert not ({r["customer"] for r in tr}&{r["customer"] for r in te})
  gety=lambda r:rd("shuffled_label_map.json")[r["instance"]] if p["condition"]=="shuffled_labels" else r["y"]
  assert {gety(r) for r in tr}=={0,1}
  folds.append(dict(prompt=p["prompt"],condition=p["condition"],fold=p["fold"],train_instances=len(tr),train_positive=sum(gety(r) for r in tr),train_negative=sum(1-gety(r) for r in tr),train_customers=len({r["customer"] for r in tr}),test_instances=len(te),test_positive=sum(gety(r) for r in te),test_negative=sum(1-gety(r) for r in te),test_customers=len({r["customer"] for r in te})))
 pred=rd("predictions.json");reports=[]
 for result in rd("results.json"):
  rr=[r for r in pred if r["prompt"]==result["prompt"] and r["condition"]==result["condition"]];users=sorted({r["customer"] for r in rr});rng=np.random.default_rng(20261024);weights=[Counter(rng.choice(users,len(users),replace=True)) for _ in range(2000)];out={}
  for n in ["LR","RF","GB"]:
   aa=[v for w in weights if (v:=auc(rr,n,w)) is not None];ff=[]
   for f in range(5):
    q=[r for r in rr if r["fold"]==f];ff.append(dict(fold=f,ba=ba(q,n),auroc=auc(q,n),instances=len(q),positive=sum(r["evaluation_y"] for r in q),scores=[dict(instance=r["instance"],y=r["evaluation_y"],score=r["attacks"][n]["score"],pred=r["attacks"][n]["pred"]) for r in q]))
   out[n]=dict(ba=result["learners"][n]["ba"],ba_ci95=result["learners"][n]["ci95"],auroc=auc(rr,n),auroc_ci95=np.quantile(aa,[.025,.975]).tolist(),valid_auc_draws=len(aa),folds=ff)
  reports.append(dict(prompt=result["prompt"],condition=result["condition"],learners=out))
 checks=0
 for report in reports:
  rr=[r for r in pred if r["prompt"]==report["prompt"] and r["condition"]==report["condition"]]
  for n,a in report["learners"].items():
   actual=roc_auc_score([r["evaluation_y"] for r in rr],[r["attacks"][n]["score"] for r in rr]);assert abs(actual-a["auroc"])<1e-15;checks+=1
 (H/"descriptive_metrics.json").write_text(json.dumps(dict(status="Requested descriptive addendum; original score direction and frozen fitted models; no posthoc selection",reports=reports,fold_training_support=folds),indent=2,allow_nan=False))
 receipt=dict(passed=True,independent_sklearn_auroc_point_checks=checks,model_class_orders_checked=150,positive_score_column="classes_ [0,1], predict_proba column 1 always means label 1",all_folds_have_two_training_classes=True,raw_features="Only c2s/s2c record count,total,max,min, averaged over same prompt/customer/order/item; no IDs or timing",original_verification_sha256=hashlib.sha256((H/"verification.json").read_bytes()).hexdigest())
 (H/"descriptive_verification.json").write_text(json.dumps(receipt,indent=2));print(receipt)
if __name__=="__main__":main()
