"""Label-only customer-fold feasibility; no traffic or prediction inputs."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
rows=read(H/"actual_attribute_instances.json")
p=H.parent/"sp2027-r7-crossfit/protocol.json"
folds=read(p)["fold_of_customer"]
out=[]
for verb in ["return_delivered_order_items","modify_pending_order_items","exchange_delivered_order_items"]:
 for prompt in ["pooled","baseline","rules"]:
  rr=[r for r in rows if r["verb"]==verb and r["single_requested_item"] and (prompt=="pooled" or r["prompt"]==prompt)]
  fd=[]
  for k in range(5):
   d={"fold":k}
   for scope in ["train","test"]:
    q=[r for r in rr if (folds[r["user"]]==k)==(scope=="test")]
    pos={r["user"] for r in q if r["selected_has_digital_device"]};neg={r["user"] for r in q if not r["selected_has_digital_device"]}
    d[scope]={"customers":len(pos|neg),"positive_customers":len(pos),"negative_customers":len(neg),"mixed_customers":len(pos&neg),"call_rows":len(q)}
   fd.append(d)
  native={n:len({r["user"] for r in rr if n in r["product_names"]}) for n in sorted({n for r in rr for n in r["product_names"]})}
  out.append({"verb":verb,"prompt":prompt,"folds":fd,"native_product_name_customer_support":native})
(H/"fold_feasibility.json").write_text(json.dumps({"fold_source":"../sp2027-r7-crossfit/protocol.json:fold_of_customer","fold_source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"reports":out},indent=2))
for r in out:
 if r["prompt"]=="pooled": print(r["verb"],[(x["test"]["positive_customers"],x["test"]["negative_customers"]) for x in r["folds"]], "train",[(x["train"]["positive_customers"],x["train"]["negative_customers"]) for x in r["folds"]])
