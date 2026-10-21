"""Read-only checks for the second-round transfer tests (Python standard library only).

* raw captures and session files have the expected sizes and keys;
* E5 summary statistics recompute from the raw record-length captures;
* E6 utility/overhead fields recompute from the raw sessions;
* E7 byte ratios recompute from the raw TLS record sequences;
* the manuscript tables regenerate byte-identically from the result files;
* prediction outcomes recompute from the results and the pre-registered thresholds;
* PREREGISTRATION.json is unchanged since it was committed (hash pinned below).
"""
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAB = HERE.parents[1] / "manuscript/tables"
PREREG_SHA256 = "ea6ee11ca8df3998c7b0e2278184970de0e698983441a762e35d5d54a6118c39"


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def close(a, b, tol=1e-9):
    assert math.isclose(a, b, rel_tol=tol, abs_tol=tol), (a, b)


def main():
    assert hashlib.sha256((HERE / "PREREGISTRATION.json").read_bytes()).hexdigest() == PREREG_SHA256
    # E5
    caps = load("e5_streaming_captures.json")
    res = load("e5_streaming_results.json")
    assert len(res) == 28
    by = defaultdict(list)
    for c in caps:
        by[(c["tls"], c["target"], c["policy"], c["draw"])].append(c)
    for r in res:
        draws = range(r["draws"])
        obs = [c for d in draws for c in by[(r["tls"], r["target"], r["policy"], d)]]
        assert len(obs) == 48 * r["draws"]
        close(sum(sum(x + 5 for x in c["records"]) for c in obs) / len(obs), r["mean_wire_bytes"])
        d0 = [c for c in by[(r["tls"], r["target"], r["policy"], 0)]]
        close(sum(len(c["records"]) for c in d0) / 48, r["mean_records"])
    # E6
    sess = load("e6_sessions.json")
    assert len(sess) == 8 * 115 * 3
    e6 = load("e6_dispatch_results.json")
    assert len(e6) == 16
    for r in e6:
        S = [s for s in sess if s["cover"] == r["cover"]]
        close(sum(s["db_eq"] for s in S) / len(S), r["db_equality"])
        close(sum(s["account_eq"] for s in S) / len(S), r["account_equality"])
        nr = sum(c["kind"] == "real" for s in S for c in s["calls"])
        nc = sum(c["kind"] == "cover" for s in S for c in s["calls"])
        close(nc / nr, r["call_overhead"])
        assert r["positive_tasks"] == (18 if r["target"] == "cancel" else 32)
    # Real calls are the unchanged reference programs in every cover condition.
    ref = {(s["task"], s["seed"]): [c["name"] for c in s["calls"]] for s in sess if s["cover"] == "none"}
    for s in sess:
        assert [c["name"] for c in s["calls"] if c["kind"] == "real"] == ref[(s["task"], s["seed"])]
        if s["cover"].endswith("_shadow") or s["cover"] == "none":
            assert s["db_eq"]
    # E7
    recs = load("e7_records.json")
    assert len(recs) == 4 * 3 * 115 * 3
    e7 = load("e7_network_results.json")
    R = {(x["cover"], x["framing"], x["task"], x["seed"]): x["records"] for x in recs}
    S = {(s["cover"], s["task"], s["seed"]): s for s in sess}
    for (cov, fr, t, sd), q in R.items():
        assert sum(d == "c2s" for d, _ in q) == len(S[(cov, t, sd)]["calls"])
    base = sum(sum(n + 5 for _, n in v) for k, v in R.items() if k[:2] == ("none", "raw")) / 345
    for r in e7["results"]:
        w = sum(sum(n + 5 for _, n in v) for k, v in R.items() if k[:2] == (r["cover"], r["framing"])) / 345
        close(w, r["mean_wire_bytes"]); close(w / base, r["wire_ratio"])
    # Tables and predictions regenerate identically.
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-B", str(HERE / "make_tables.py"), tmp], check=True, capture_output=True)
        for f in ("transfer-streaming", "transfer-cover", "transfer-predictions", "supp-transfer"):
            assert (Path(tmp) / f"{f}.tex").read_bytes() == (TAB / f"{f}.tex").read_bytes(), f
    before = (HERE / "PREREGISTRATION_OUTCOMES.json").read_bytes()
    subprocess.run([sys.executable, "-B", str(HERE / "resolve_predictions.py")], check=True, capture_output=True)
    assert (HERE / "PREREGISTRATION_OUTCOMES.json").read_bytes() == before
    out = {o["id"]: o["outcome"] for o in load("PREREGISTRATION_OUTCOMES.json")["outcomes"]}
    print(json.dumps({"status": "SP2027_R2_TRANSFER_TESTS_PASS", "e5_captures": len(caps),
                      "e6_sessions": len(sess), "e7_tls_sessions": len(recs), "predictions": out,
                      "new_model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
