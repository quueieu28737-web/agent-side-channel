"""Reproduce the retrospective B ledger and the time-ordering audit for C.

This is documentary validation, not a rerun of external attacks or blind coding.
No third-party paper is redistributed. source-receipts.json pins inspected PDFs.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, subprocess

O = Path(__file__).resolve().parent
P = O.parents[1]
R = P.parents[1]
M = P / "manuscript"
BASE = "16f6254fca0b653b9dbd7277292a3ab6ff84c7ca"
RESULT = "8bd7380b0f1dad4479898bae370582fa2c1b678d"

def load(f): return json.loads(f.read_text(encoding="utf-8-sig"))
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f, x): f.write_text(json.dumps(x, indent=2, ensure_ascii=False)+"\n", encoding="utf8", newline="\n")
def git(*a): return subprocess.check_output(["git", *a], cwd=R)

# The study frame is fixed in protocol.json. Each row is a measurement object,
# not an independent replication. Numeric outcomes are the publications' metrics.
rows = []
def row(i, study, defense, mode, locator, items, outcome, decision, control=False):
    rows.append(dict(id=f"B{i:02d}", study=study, defense=defense, mode=mode,
                     locator=locator, items=items, published_outcome=outcome,
                     required_measurement=decision, retained_control=control))

row(1,"df2018","WTF-PAD","transformed capture","5.4 / Table 3","R4,R7",
    "DF accuracy 90.7%; strongest prior comparator 69.0% in the same table.",
    "Fit the stronger attacker on the protected distribution; retain each attack-specific result.")
row(2,"df2018","Walkie-Talkie","half-duplex capture and molding","5.4 / Table 3; 5.8","R2,R4,R7",
    "DF accuracy 49.7% under symmetric collisions; asymmetric collisions give 87.2%.",
    "Keep the symmetric-pairing condition; a new attacker alone does not imply failure.",True)
row(3,"wfdef2021","FRONT","simulation / live PT","6.2 / Table 10","R3,R9",
    "Same-parameter data overhead 52% to 75%; DF TPR 72.06% to 42.79% (FPR 2.16% to 2.49%).",
    "Measure restart behavior and live cost; preserve the improved live security outcome.",True)
row(4,"wfdef2021","Tamaraw","simulation / live PT","6.1 / Table 9","R3,R9",
    "Optimistic/pessimistic/live data overhead 207/224/179%; time 19/26/21%; DF TPR 2.59/2.74/6.43%.",
    "Bind the soft-stop implementation and costs; retain the low-TPR live result.",True)
row(5,"wfdef2021","Random-WT","simulation / live PT","6.3 / Table 11; 4.4","R3,R9",
    "DF TPR 87.47% to 83.41%; data overhead 96% to 88%; time overhead 44% to 23%.",
    "Price the live burst schedule; Random-WT is not symmetric Walkie-Talkie.")
# Standard-mode Table II is selected consistently, without selecting the most
# favorable of Standard/Safer/Safest. The original studies are not recoded blind.
mat = [
 ("DynaFlow","IV-F; Table II", "R2,R4,R6",38.3,"Test IAT-switch features; keep the workload and subpage composition."),
 ("BiMorphing","IV-A; Table II","R4,R6",81.0,"Refit a deep attacker; do not pool different datasets."),
 ("DFD","IV-D; Table II","R2,R4,R5",94.2,"Match perturbation variation in protected training/testing and include timing."),
 ("FRONT","IV-G; Table II","R4,R6",81.8,"Fit with defended variants and the staged training schedule."),
 ("HyWF","IV-B; Table II","R2,R4,R6",56.8,"Bind one-split visibility and augmented protected fitting."),
 ("TrafficSliver","IV-B; Table II","R2,R3,R4,R6",5.4,"Retain BE-TS one-split results; do not inherit them for an all-split observer."),
 ("Spring","IV-C; Table II","R2,R4",80.0,"Include rounded timing and multiple protected training variants."),
 ("Interspace","IV-C; Table II","R2,R4",76.1,"Include rounded timing and multiple protected training variants."),
 ("BANP","IV-E; Table II","R4,R5",89.6,"Refit after generating perturbations with the accessible defense generator."),
]
for i,(d,l,it,a,dec) in enumerate(mat,6):
    row(i,"mathews2023",d,"BE/BE-TS Standard",l,it,
        f"Closed-world attack accuracy {a:.1f}%.",dec,d=="TrafficSliver")
row(15,"mathews2023","DynaFlow","live PT","Appendix B","R3,R6,R9",
    "Live accuracy 63.6%; mean per-site bandwidth/time overhead 123%/379%; different URLs and crawler.",
    "Keep a separate live record; simulation and live numbers are not a matched causal contrast.")
assert len(rows)==15
save(O/"external-ledger.json",rows)
with (O/"external-ledger.csv").open("w",encoding="utf8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

# Independent of source outcomes, map the requested *object* to a measurement.
# This intentionally ties established WF practice: no novel WF attack rule.
plans={}
for x in rows:
    cost=x["id"] in {"B03","B04","B05","B15"}
    plans[x["id"]]={
      "object":"execution/cost" if cost else "protected fit/view",
      "mechanism_name_carryover":"reuse source number",
      "blanket_failure":"declare failure",
      "audit_action":"measure execution and cost" if cost else "evaluate scoped protected attacker",
      "established_wf_action":"measure execution and cost" if cost else "evaluate scoped protected attacker",
      "audit_preserves_observed_control":bool(x["retained_control"]),
    }
save(O/"decision-comparators.json",plans)
summary={"design":"retrospective, outcome-informed documentary audit",
 "records":len(rows),"defense_study_pairs":len({(x["study"],x["defense"]) for x in rows}),
 "followup_studies":len({x["study"] for x in rows}),
 "records_by_study":dict(Counter(x["study"] for x in rows)),
 "measurement_objects":dict(Counter(x["object"] for x in plans.values())),
 "retained_control_ids":[x["id"] for x in rows if x["retained_control"]],
 "established_WF_measurement_plan_agreements":sum(x["audit_action"]==x["established_wf_action"] for x in plans.values()),
 "prediction_hit_rate":None,"p_value":None,
 "inference":"All labels are outcome-informed. Agreement with established WF practice is a mapping check, not evidence of superiority or prospective accuracy. Four controls refute the blanket implication changed boundary => observed failure.",
 "frame_exclusions":["Other studies were outside the fixed three-study frame.",
  "Mathews layered combinations and non-Standard modes are not additional independent events.",
  "DynaFlow live is split because its mode, workload and cost object differ.",
  "No unreported confidence intervals, replication runs, or earlier source-only scores are imputed."]}
save(O/"external-summary.json",summary)

# Git tree ordering is independently checkable; it is not an external timestamp
# of execution or proof of outcome blinding.
prefix=(P/"experiments/sp2027-r2").relative_to(R).as_posix()+"/"
reg=prefix+"PREREGISTRATION.json"
blob=git("show",BASE+":"+reg)
assert blob==(R/reg).read_bytes()
tree=git("ls-tree","-r","--name-only",BASE,"--",prefix).decode().splitlines()
assert tree==[reg],tree
subprocess.run(["git","merge-base","--is-ancestor",BASE,RESULT],cwd=R,check=True)
timeline={"registration_commit":BASE,"result_commit":RESULT,
 "registration_commit_utc":git("show","-s","--format=%cI",BASE).decode().strip(),
 "result_commit_utc":git("show","-s","--format=%cI",RESULT).decode().strip(),
 "registration_sha256":hashlib.sha256(blob).hexdigest(),
 "registration_tree_contains_only_protocol":True,"registration_unchanged":True,
 "registration_is_ancestor_of_result":True,
 "scope":"Repository ordering: registration before archived result commit. Git metadata alone does not independently timestamp physical execution or establish blinded prediction."}
save(O/"timeline.json",timeline)
c=[
 ("P1","supported","Emitter/count and cost object", "Per-event padding leaves T1 at 100%; stream shaping uses 2.42x token-stream bytes."),
 ("P2","supported","Protected-data fitting", "D0 50% versus D2 100% in recorded batching/cover conditions."),
 ("P3","supported","Identity versus binary target", "Known-response top-1 58-62%; chance 1/48."),
 ("P4","supported","Non-target dispatch features", "Count rule 50%; suite BA 76.9%."),
 ("P5","premise_unmet","Dispatch to network", "Source dispatch protection was not established; network leakage is persistence."),
 ("P6","partial","Record framing to full session", "Bucketed return is above threshold; other framing cells inconclusive."),
 ("P7","not_established","Joint state/transport package", "No condition passes the prewritten screen on both targets."),
]
save(O/"judgments.json",[dict(id=i,status=s,object=o,evidence=e) for i,s,o,e in c])
save(O/"inputs.json",{"protocol_sha256":sha(O/"protocol.json"),
 "source_receipts_sha256":sha(O/"source-receipts.json"),
 "historical_inputs":{n:sha(P/n) for n in [
  "experiments/sp2027-r2/PREREGISTRATION.json","experiments/sp2027-r2/PREREGISTRATION_OUTCOMES.json",
  "experiments/sp2027-r2/e5_streaming_results.json","experiments/sp2027-r3/e6_dispatch_results.json",
  "experiments/sp2027-r3/e7_network_results.json","experiments/sp2027-r3/out_of_fold_predictions.json",
  "manuscript/tables/r3-transfer-predictions.tex"]}})
print(json.dumps({"B":summary,"C_status_counts":dict(Counter(x[1] for x in c)),"timeline":timeline},indent=2))
