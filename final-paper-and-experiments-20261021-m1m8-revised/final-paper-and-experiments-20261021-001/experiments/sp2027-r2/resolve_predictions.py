"""Resolve the seven pre-registered transfer claims from the saved E5-E7 results.
Thresholds are the ones written in PREREGISTRATION.json before execution."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "PREREGISTRATION.json").read_text())
e5 = json.loads((HERE / "e5_streaming_results.json").read_text())
e6 = json.loads((HERE / "e6_dispatch_results.json").read_text())
e7 = json.loads((HERE / "e7_network_results.json").read_text())


def g5(tls, tgt, pol):
    return next(r for r in e5 if r["tls"] == tls and r["target"] == tgt and r["policy"] == pol)


def g6(tgt, cov):
    return next(r for r in e6 if r["target"] == tgt and r["cover"] == cov)


def g7(tgt, cov, fr):
    return next(r for r in e7["results"] if r["target"] == tgt and r["cover"] == cov and r["framing"] == fr)


def status(r):
    lo, hi = r["best_ba_ci95"]
    if lo > 0.60:
        return "not_protected"
    if hi < 0.60 and r["best_auroc"] < 0.65:
        return "protected"
    return "inconclusive"


out = []
# P1
c = [g5(v, "T1", "tok_const") for v in ("1.2", "1.3")]
cap = [g5(v, "T1", "tok_const_cap") for v in ("1.2", "1.3")]
p1 = all(x["best_D2_binary_accuracy"] >= 0.90 for x in c) and all(x["ratio_vs_token_stream"] > 2.18 for x in cap)
out.append({"id": "P1", "outcome": "confirmed" if p1 else "refuted",
            "evidence": {"tok_const_T1_D2": [x["best_D2_binary_accuracy"] for x in c],
                         "stream_cap_ratio_vs_token_stream": [x["ratio_vs_token_stream"] for x in cap],
                         "stream_cap_completion_token_intervals": [x["completion_token_intervals"] for x in cap],
                         "buffered_cap_ttfb_token_intervals": g5("1.3", "T1", "buffered_cap")["ttfb_token_intervals"]}})
# P2
b = g5("1.3", "T1", "batch8_const")
d0, d2 = b["binary_accuracy"]["D0_total_threshold"][0], b["best_D2_binary_accuracy"]
r6 = g6("cancel", "cancel_p100_shadow")
out.append({"id": "P2", "outcome": "confirmed" if d2 > d0 else "refuted",
            "evidence": {"batch8_T1_D0": d0, "batch8_T1_D2": d2,
                         "E6_cancel_p100_D0_ba": r6["attackers"]["D0_gboost"]["ba"], "E6_cancel_p100_best_ba": r6["best_ba"]}})
# P3
ids = {p: g5("1.3", "T1", p)["identification_top1"] for p in ("tok_randpad", "tok_const")}
out.append({"id": "P3", "outcome": "confirmed" if min(ids.values()) >= 0.25 else "refuted",
            "evidence": {"identification_top1": ids, "chance": 1 / 48}})
# P4
r = g6("cancel", "cancel_const2_shadow")
out.append({"id": "P4", "outcome": "confirmed" if status(r) == "not_protected" else "refuted_or_inconclusive",
            "evidence": {"best": r["best_attacker"], "ba": r["best_ba"], "ci95": r["best_ba_ci95"],
                         "count_rule_ba": r["attackers"]["count_rule"]["ba"]}})
# P5
rs = [g7(t, cv, "raw") for t in ("cancel", "return") for cv in ("cancel_const2_shadow", "decoy1_shadow")]
out.append({"id": "P5", "outcome": "confirmed" if all(status(x) == "not_protected" for x in rs) else "partially_confirmed",
            "evidence": {"request_size_to_tool_accuracy_raw": e7["tool_identification"]["raw"]["request_size_to_tool_accuracy"],
                         "cells": [{"target": x["target"], "cover": x["cover"], "ba": x["best_ba"], "ci95": x["best_ba_ci95"], "status": status(x)} for x in rs]}})
# P6
rs = [g7(t, "none", fr) for t in ("cancel", "return") for fr in ("bucket1024", "const")]
st = [status(x) for x in rs]
out.append({"id": "P6", "outcome": "confirmed" if all(s == "not_protected" for s in st) else
            ("partially_confirmed" if "not_protected" in st else "not_confirmed"),
            "evidence": [{"target": x["target"], "framing": x["framing"], "ba": x["best_ba"], "ci95": x["best_ba_ci95"], "status": status(x)} for x in rs]})
# P7
rs = [g7(t, "shape_eq_shadow", "const") for t in ("cancel", "return")]
st = [status(x) for x in rs]
out.append({"id": "P7", "outcome": "confirmed" if all(s == "protected" for s in st) and all(x["db_equality"] == 1 for x in rs) else
            ("partially_confirmed" if "protected" in st else "not_confirmed"),
            "evidence": [{"target": x["target"], "ba": x["best_ba"], "ci95": x["best_ba_ci95"], "auroc": x["best_auroc"],
                          "status": status(x), "db_equality": x["db_equality"], "wire_ratio": x["wire_ratio"],
                          "round_trip_ratio": x["round_trip_ratio"]} for x in rs]})
destination = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "PREREGISTRATION_OUTCOMES.json"
destination.write_text(json.dumps({"thresholds": pre["decision_thresholds"], "outcomes": out}, indent=1), encoding="utf-8", newline="\n")
for o in out:
    print(o["id"], o["outcome"])
