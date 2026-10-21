"""Read-only statistical evaluation of static human/expert dual-coding tables
and the 24-scenario retrospective deployment-transfer benchmark.

Loads saved annotation CSVs (`m1_validity_benchmark.csv`, `m7_dual_coding_screening.csv`,
`m7_dual_coding_checks.csv`, `m7_dual_coding_pairs.csv`, `m6_split_checks.csv`) and
computes Cohen's kappa, 10,000-draw percentile bootstrap confidence intervals,
and exact accuracy/recall metrics.
"""
import csv
import json
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent


def cohen_kappa(y1, y2, labels=None):
    assert len(y1) == len(y2) and len(y1) > 0
    if labels is None:
        labels = sorted(set(y1) | set(y2))
    n = len(y1)
    po = sum(1 for a, b in zip(y1, y2) if a == b) / float(n)
    c1 = {lbl: sum(1 for a in y1 if a == lbl) / float(n) for lbl in labels}
    c2 = {lbl: sum(1 for b in y2 if b == lbl) / float(n) for lbl in labels}
    pe = sum(c1[lbl] * c2[lbl] for lbl in labels)
    if abs(1.0 - pe) < 1e-12:
        return 1.0, po, pe
    return (po - pe) / (1.0 - pe), po, pe


def bootstrap_kappa(y1, y2, labels=None, seed=20261021, n_draws=10000):
    k_est, po, pe = cohen_kappa(y1, y2, labels=labels)
    rng = np.random.default_rng(seed)
    n = len(y1)
    idx = rng.integers(0, n, size=(n_draws, n))
    y1_arr = np.asarray(y1, dtype=object)
    y2_arr = np.asarray(y2, dtype=object)
    ks = [cohen_kappa(y1_arr[row_idx], y2_arr[row_idx], labels=labels)[0] for row_idx in idx]
    lo, hi = np.quantile(ks, [0.025, 0.975])
    return {
        "n": n,
        "raw_agreement": float(po),
        "expected_agreement": float(pe),
        "cohen_kappa": float(k_est),
        "kappa_ci95": [float(lo), float(hi)],
        "exact_matches": int(round(po * n)),
        "disagreements": int(n - round(po * n)),
    }


def evaluate_m1():
    with (OUT / "m1_validity_benchmark.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    labels = ["Compatible", "Incompatible", "Unresolved"]
    k_stats = bootstrap_kappa(
        [r["expert1_3check_pred"] for r in rows],
        [r["expert2_3check_pred"] for r in rows],
        labels=labels,
    )
    h_corr = [int(r["headline_baseline_pred"] == r["ground_truth"]) for r in rows]
    c1_corr = [int(r["expert1_3check_pred"] == r["ground_truth"]) for r in rows]
    c2_corr = [int(r["expert2_3check_pred"] == r["ground_truth"]) for r in rows]
    inc_rows = [r for r in rows if r["ground_truth"] == "Incompatible"]

    summary = {
        "benchmark_cases": len(rows),
        "baseline_rule": "Deterministic headline-metric rule: predict Compatible whenever source paper reports attack reduction or <10% component overhead",
        "ground_truth_distribution": {
            lbl: sum(1 for r in rows if r["ground_truth"] == lbl) for lbl in labels
        },
        "headline_score_baseline_accuracy": float(np.mean(h_corr)),
        "headline_score_correct_count": int(sum(h_corr)),
        "expert1_3check_accuracy": float(np.mean(c1_corr)),
        "expert1_correct_count": int(sum(c1_corr)),
        "expert2_3check_accuracy": float(np.mean(c2_corr)),
        "expert2_correct_count": int(sum(c2_corr)),
        "mean_expert_accuracy": float(0.5 * (np.mean(c1_corr) + np.mean(c2_corr))),
        "accuracy_gain_over_headline_baseline": float(0.5 * (np.mean(c1_corr) + np.mean(c2_corr)) - np.mean(h_corr)),
        "known_failure_detection_recall": {
            "n_incompatible_failures": len(inc_rows),
            "headline_baseline": float(np.mean([int(r["headline_baseline_pred"] == r["ground_truth"]) for r in inc_rows])),
            "expert1_3check": float(np.mean([int(r["expert1_3check_pred"] == r["ground_truth"]) for r in inc_rows])),
            "expert2_3check": float(np.mean([int(r["expert2_3check_pred"] == r["ground_truth"]) for r in inc_rows])),
        },
        "inter_annotator_agreement": k_stats,
    }
    (OUT / "m1_validity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def evaluate_m7():
    with (OUT / "m7_dual_coding_screening.csv").open(encoding="utf-8") as f:
        scr = list(csv.DictReader(f))
    with (OUT / "m7_dual_coding_checks.csv").open(encoding="utf-8") as f:
        chk = list(csv.DictReader(f))
    with (OUT / "m7_dual_coding_pairs.csv").open(encoding="utf-8") as f:
        prs = list(csv.DictReader(f))

    scr_3 = bootstrap_kappa(
        [r["coder1_workflow"] for r in scr],
        [r["coder2_independent_expert"] for r in scr],
        labels=["Core", "Adjacent", "Excluded/Background"],
    )
    scr_bin = bootstrap_kappa(
        ["Core" if r["coder1_workflow"] == "Core" else "Non-Core" for r in scr],
        ["Core" if r["coder2_independent_expert"] == "Core" else "Non-Core" for r in scr],
        labels=["Core", "Non-Core"],
    )
    chk_stats = bootstrap_kappa(
        [r["coder1_workflow"] for r in chk],
        [r["coder2_independent_expert"] for r in chk],
        labels=["Bound", "Partial", "NR-R", "NR-V", "NA"],
    )
    pair_stats = bootstrap_kappa(
        [r["coder1_workflow"] for r in prs],
        [r["coder2_independent_expert"] for r in prs],
        labels=["COMPATIBLE", "INCOMPATIBLE", "UNRESOLVED", "NOT_APPLICABLE"],
    )
    summary = {
        "screening_100_subsample": {
            "three_class_routing": scr_3,
            "binary_core_inclusion": scr_bin,
        },
        "split_check_audit_144_cells": chk_stats,
        "pairwise_comparability_50_pairs_150_judgments": pair_stats,
    }
    (OUT / "m7_dual_coding_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    m1 = evaluate_m1()
    m7 = evaluate_m7()
    print("=== M1 VALIDITY BENCHMARK (DETERMINISTIC RULE BASELINE) ===")
    print(json.dumps(m1, indent=2))
    print("=== M7 DUAL CODING SUMMARY ===")
    print(json.dumps(m7, indent=2))


if __name__ == "__main__":
    main()
