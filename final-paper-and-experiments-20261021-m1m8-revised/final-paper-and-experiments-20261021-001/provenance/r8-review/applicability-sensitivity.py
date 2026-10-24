import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "evidence/retained-release007/history-release006/decision-audit/six-checks.csv"
OUT = Path(__file__).with_name("applicability-sensitivity.json")
rows = list(csv.DictReader(SRC.open(encoding="utf-8-sig")))
families = {}
for r in rows:
    families.setdefault(r["citation_key"], {})[r["check"]] = r
assert len(families) == 16 and all(len(x) == 6 for x in families.values())

# Applicability sensitivity: check 4 in the historical audit asks whether
# protected-condition fitting/matched testing is at issue. Treat that explicit
# applicability screen as the conservative denominator for the later R5 item.
applicable = [k for k,v in families.items() if v["4"]["status"] != "NA"]
strict_na = [k for k,v in families.items() if v["4"]["status"] == "NA"]
counts = {}
for k in applicable:
    s=families[k]["4"]["status"]
    counts[s]=counts.get(s,0)+1

# R8 scope sensitivity distinguishes objective-task utility from component utility.
# This is a classification lens, not a recoding of frozen rows.
component_only = [k for k,v in families.items() if "NA_component_scope" in v["6"].get("utility_subfield", "") or "SAT_component_" in v["6"].get("utility_subfield", "")]
OUT.write_text(json.dumps({
 "source": str(SRC.relative_to(ROOT)).replace('\\','/'),
 "unit": "16 historical VERIFIED_EVALUATION families; 6 source-audit rows each",
 "r5_applicability_sensitivity_using_historical_C4": {"rationale":"C4 explicitly conditions protected fitting/matched testing on adaptation being at issue; using its NA status as the applicability screen avoids requiring adaptive refits for fixed/non-learning mitigations. Status counts are C4 baseline values, not recoded nine-item R5 outcomes.","applicable_n":len(applicable),"not_applicable_n":len(strict_na),"status_counts":counts,"applicable_family_ids":applicable,"NA_family_ids":strict_na},
 "r8_check6_component_vs_objective_lens": {"families_with_explicit_component_utility_scope":component_only,"n":len(component_only),"interpretation":"These remain in broad component-utility R8; the lens separates component outcome from deployment task utility and does not mark them globally NA."},
 "caution":"Historical source rows are read-only. This calculation covers the 16-family baseline only; the expanded manuscript table separately reports 20 families."
},indent=2),encoding="utf-8")
print(OUT.read_text(encoding="utf-8"))
