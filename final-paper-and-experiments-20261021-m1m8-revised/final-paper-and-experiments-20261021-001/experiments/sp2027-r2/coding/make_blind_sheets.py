"""B1 step 1: generate blinded coding sheets for independent human coders.

Sheets contain only what a coder needs to read the source: family key, result
record IDs, source URL/version, locators and the item definition. They contain no
AI-assisted or author labels, notes or adjudications. Row order is shuffled per
coder with a different seed so that coders cannot align sheets by position.

Outputs (in --out, default coding/sheets/):
  audit_<coder>.csv   20 mitigation families x R1-R9 (180 cells)
  pairs_<coder>.csv   50 record pairs x 3 judgment types (150 judgments)
  MANIFEST.json       SHA-256 of every sheet, written before distribution

  python -B make_blind_sheets.py --coders C1 C2 C3
"""
import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
ITEMS = {
    1: "R1 Target & protection polarity", 2: "R2 Receiver fields & linkage", 3: "R3 Placement & action dispatch",
    4: "R4 Protected-condition fit", 5: "R5 Matched adapted test", 6: "R6 Workloads & generator shifts",
    7: "R7 Defended inference effect", 8: "R8 Task or component utility", 9: "R9 Mechanism or protocol cost",
}


def families():
    """20 audited mitigation families: 16 baseline (m6_split_checks) + 4 additions."""
    fam = []
    for r in csv.DictReader((EXP / "revision-m1-m8/m6_split_checks.csv").open(encoding="utf-8")):
        if r["citation_key"] not in fam:
            fam.append(r["citation_key"])
    rec = json.loads((EXP / "reviewer-audit/combined_result_records.json").read_text())
    for r in rec["added_records"]:
        if r["citation_key"] not in fam:
            fam.append(r["citation_key"])
    src = defaultdict(lambda: {"units": [], "urls": set(), "locators": set()})
    for r in rec["baseline_records"] + rec["added_records"]:
        s = src[r["citation_key"]]
        s["units"].append(r["unit_id"]); s["urls"].add(r.get("source_url", ""))
        s["locators"].add(r.get("scope") or r.get("source_locator") or "")
    return fam, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coders", nargs="+", default=["C1", "C2"])
    ap.add_argument("--out", default=str(HERE / "sheets"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    fam, src = families()
    assert len(fam) == 20, len(fam)
    pairs = []
    seen = set()
    for r in csv.DictReader((EXP / "revision-m1-m8/m7_dual_coding_pairs.csv").open(encoding="utf-8")):
        k = (r["pair_index"], r["judgment_type"])
        if k not in seen:
            seen.add(k); pairs.append({"pair_index": r["pair_index"], "record_a": r["record_a"], "record_b": r["record_b"],
                                       "judgment_type": r["judgment_type"]})
    manifest = {}
    for ci, coder in enumerate(a.coders):
        rng = random.Random(f"blind-{coder}-{ci}")
        rows = [{"cell_id": f"{f}|R{i}", "family": f, "result_units": ";".join(src[f]["units"]),
                 "source_urls": ";".join(sorted(u for u in src[f]["urls"] if u)),
                 "locators_to_read": ";".join(sorted(l for l in src[f]["locators"] if l)),
                 "item": ITEMS[i], "status": "", "evidence_locator": "", "note": ""} for f in fam for i in ITEMS]
        rng.shuffle(rows)
        p = out / f"audit_{coder}.csv"
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        manifest[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        prow = [dict(x, judgment_id=f"{x['pair_index']}|{x['judgment_type']}", judgment="", note="") for x in pairs]
        rng.shuffle(prow)
        p = out / f"pairs_{coder}.csv"
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["judgment_id", "pair_index", "record_a", "record_b", "judgment_type", "judgment", "note"])
            w.writeheader(); w.writerows(prow)
        manifest[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    (out / "MANIFEST.json").write_text(json.dumps({"families": fam, "cells_per_coder": 180, "pair_judgments_per_coder": len(pairs),
                                                   "sha256": manifest}, indent=1))
    print(f"{len(a.coders)} coders x 180 audit cells and {len(pairs)} pair judgments ->", out)


if __name__ == "__main__":
    main()
