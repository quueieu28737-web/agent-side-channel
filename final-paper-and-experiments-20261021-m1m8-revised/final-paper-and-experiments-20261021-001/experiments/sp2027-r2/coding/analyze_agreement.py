"""B1 step 2: agreement analysis for returned blinded coding sheets.

Computes Krippendorff's alpha (nominal) across any number of coders, a
family-cluster bootstrap interval (cells of one family resampled together, which
the earlier cell-level intervals did not do), per-item alpha, and agreement of the
adjudicated labels with the manuscript's audit labels.

  python -B analyze_agreement.py --audit sheets/audit_C1.csv sheets/audit_C2.csv \
         [--adjudicated adjudicated_audit.csv] --out agreement_results.json
  python -B analyze_agreement.py --selftest     # runs on the two supplied historical
                                                # columns; validates the code only
"""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
STATES = {"Bound", "Partial", "NR-R", "NR-V", "NA"}
# Historical check codes in m6/m7 CSVs -> current item numbers R1-R9.
OLD2R = {"1": 1, "2": 2, "3": 3, "4a": 4, "4b": 5, "5": 6, "6a": 7, "6b": 8, "6c": 9}


def alpha_nominal(units):
    """units: list of lists of labels (one list per cell, missing labels omitted)."""
    pairs = Counter(); n = 0
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        for i, a in enumerate(vals):
            for j, b in enumerate(vals):
                if i != j:
                    pairs[(a, b)] += 1 / (m - 1)
        n += m
    if n == 0:
        return float("nan")
    marg = Counter()
    for (a, _b), w in pairs.items():
        marg[a] += w
    do = sum(w for (a, b), w in pairs.items() if a != b)
    de = sum(marg[a] * marg[b] for a in marg for b in marg if a != b) / (n - 1)
    return 1.0 if de == 0 else 1 - do / de


def cluster_ci(cells, n=5000, seed=20261021):
    by = defaultdict(list)
    for fam, vals in cells:
        by[fam].append(vals)
    fams = sorted(by); rng = random.Random(seed); bs = []
    for _ in range(n):
        pick = [rng.choice(fams) for _ in fams]
        bs.append(alpha_nominal([v for f in pick for v in by[f]]))
    bs.sort()
    return [bs[int(.025 * n)], bs[int(.975 * n) - 1]]


def read_sheet(p, key="cell_id", val="status"):
    out = {}
    for r in csv.DictReader(open(p, encoding="utf-8")):
        v = r[val].strip()
        if v:
            if val == "status" and v not in STATES:
                raise SystemExit(f"{p}: invalid status {v!r} in {r[key]}")
            out[r[key]] = v
    return out


def summarize(sheets, family_of):
    keys = sorted(set().union(*sheets))
    cells = [(family_of(k), [s[k] for s in sheets if k in s]) for k in keys]
    by_item = defaultdict(list)
    for k, (_, v) in zip(keys, cells):
        by_item[k.split("|")[-1]].append(v)
    a = alpha_nominal([v for _, v in cells])
    return {"cells": len(keys), "coders": len(sheets), "alpha": a, "alpha_family_cluster_ci95": cluster_ci(cells),
            "raw_pairwise_agreement": sum(len(set(v)) == 1 for _, v in cells if len(v) > 1) / max(1, sum(len(v) > 1 for _, v in cells)),
            "alpha_by_item": {i: alpha_nominal(v) for i, v in sorted(by_item.items())}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", nargs="*", default=[])
    ap.add_argument("--pairs", nargs="*", default=[])
    ap.add_argument("--adjudicated")
    ap.add_argument("--out", default=str(HERE / "agreement_results.json"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    res = {}
    if a.selftest:
        rows = list(csv.DictReader((EXP / "revision-m1-m8/m7_dual_coding_checks.csv").open(encoding="utf-8")))
        s1 = {f"{r['citation_key']}|R{OLD2R[r['check_id']]}": r["coder1_workflow"] for r in rows}
        s2 = {f"{r['citation_key']}|R{OLD2R[r['check_id']]}": r["coder2_independent_expert"] for r in rows}
        res["selftest_supplied_columns"] = summarize([s1, s2], lambda k: k.split("|")[0])
        res["note"] = "Self-test on the two historical supplied columns; validates the computation, not independence."
        a.out = str(HERE / "selftest_results.json")
    if a.audit:
        sheets = [read_sheet(p) for p in a.audit]
        res["audit"] = summarize(sheets, lambda k: k.split("|")[0])
        if a.adjudicated:
            adj = read_sheet(a.adjudicated)
            ref = {f"{r['citation_key']}|R{OLD2R[r['check_id']]}": r["status"]
                   for r in csv.DictReader((EXP / "revision-m1-m8/m6_split_checks.csv").open(encoding="utf-8"))}
            common = sorted(set(adj) & set(ref))
            res["adjudicated_vs_manuscript_labels"] = {"cells": len(common), "agreement": sum(adj[k] == ref[k] for k in common) / max(1, len(common)),
                                                       "changed_cells": [k for k in common if adj[k] != ref[k]]}
    if a.pairs:
        sheets = [read_sheet(p, "judgment_id", "judgment") for p in a.pairs]
        res["pairs"] = summarize(sheets, lambda k: k.split("|")[0])
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1)[:1500])


if __name__ == "__main__":
    main()
