"""Read-only verification of the documentary ledger and current C interpretation."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, sys
O=Path(__file__).resolve().parent;P=O.parents[1]
def read(f):return json.loads(f.read_text(encoding="utf-8-sig"))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
a=read(O/"inputs.json")
assert sha(O/"protocol.json")==a["protocol_sha256"]
assert sha(O/"source-receipts.json")==a["source_receipts_sha256"]
for n,h in a["historical_inputs"].items():assert sha(P/n)==h,n
rows=read(O/"external-ledger.json");s=read(O/"external-summary.json")
assert [x["id"] for x in rows]==[f"B{i:02d}" for i in range(1,16)]
assert dict(Counter(x["study"] for x in rows))==s["records_by_study"]=={"df2018":2,"wfdef2021":3,"mathews2023":10}
assert len({(x["study"],x["defense"]) for x in rows})==s["defense_study_pairs"]==14
assert [x["id"] for x in rows if x["retained_control"]]==s["retained_control_ids"]==["B02","B03","B04","B11"]
assert s["prediction_hit_rate"] is None and s["p_value"] is None
cs=list(csv.DictReader((O/"external-ledger.csv").open(encoding="utf8",newline="")))
assert len(cs)==15
for j,k in zip(rows,cs):
 for n,v in j.items():assert str(v)==k[n]
plans=read(O/"decision-comparators.json")
assert dict(Counter(x["object"] for x in plans.values()))==s["measurement_objects"]
assert sum(x["audit_action"]==x["established_wf_action"] for x in plans.values())==15
c=read(O/"judgments.json")
assert Counter(x["status"] for x in c)=={"supported":4,"partial":1,"premise_unmet":1,"not_established":1}
e6=read(P/"experiments/sp2027-r3/e6_dispatch_results.json")
e7=read(P/"experiments/sp2027-r3/e7_network_results.json")["results"]
e5=read(P/"experiments/sp2027-r2/e5_streaming_results.json")
padded=[x for x in e5 if x["tls"]=="1.2" and x["target"]=="T1" and x["policy"] in ["tok_randpad","tok_const"]]
assert len(padded)==2 and all(x["best_D2_binary_accuracy"]==1.0 for x in padded)
assert {round(x["identification_top1"]*100) for x in padded}=={58,62}
assert all(abs(x["identification_chance"]-1/48)<1e-12 for x in padded)
p2=next(x for x in e6 if x["target"]=="cancel" and x["cover"]=="cancel_p100_shadow")
assert p2["attackers"]["D0_gboost"]["ba"]==.5 and p2["attackers"]["D2_gboost"]["ba"]==1.0
p4=next(x for x in e6 if x["target"]=="cancel" and x["cover"]=="cancel_const2_shadow")
assert round(100*p4["best_ba"],1)==76.9 and p4["attackers"]["count_rule"]["ba"]==.5
for cover in ["cancel_const2_shadow","decoy1_shadow","decoy2_shadow"]:
 assert next(x for x in e6 if x["target"]=="cancel" and x["cover"]==cover)["criterion"]=="above_threshold"
p6=[x for x in e7 if x["cover"]=="none" and x["framing"]!="raw"]
assert sum(x["criterion"]=="above_threshold" for x in p6)==1
assert next(x for x in p6 if x["criterion"]=="above_threshold")["target"]=="return"
for cover,frame in {(x["cover"],x["framing"]) for x in e7}:
 group=[x for x in e7 if x["cover"]==cover and x["framing"]==frame]
 assert len(group)==2 and not all(x["criterion"]=="meets_evaluated_suite_criterion" for x in group)
checked=[]
if "--source-dir" in sys.argv:
 from pypdf import PdfReader
 folder=Path(sys.argv[sys.argv.index("--source-dir")+1])
 tokens={"df2018":["90.7","49.7","87.2"],
         "wfdef2021":["72.06","42.79","207","224","179","6.43","87.47","83.41"],
         "mathews2023":["38.3","81.0","94.2","81.8","56.8","5.4","80.0","76.1","89.6","63.6","379"]}
 for rec in read(O/"source-receipts.json"):
  f=folder/(rec["id"]+".pdf");assert sha(f)==rec["sha256"],f
  text="\n".join(p.extract_text() for p in PdfReader(f).pages)
  for v in tokens[rec["id"]]:assert v in text,(f,v)
  checked.append(rec["id"])
print(json.dumps({"status":"R28_BC_PASS","external_records":15,"study_clusters":3,
 "original_source_blinding":False,"predictive_significance_claim":False,
 "current_C_tally":dict(Counter(x["status"] for x in c)),
 "historical_input_hashes":len(a["historical_inputs"]),"source_pdf_checks":checked,
 "new_model_calls":0},indent=2))
