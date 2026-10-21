"""Frozen pre-treatment subsets, retaining the complete census beside them."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def main(out):
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    all_ids = sorted({r["task_id"] for r in rows})
    clean_ids = sorted({r["task_id"] for r in rows if r["baseline_tool_errors"] == 0})
    eligible_ids = sorted({r["task_id"] for r in rows if r["eligible_cover_orders"] > 0})
    groups = {"all_tasks": all_ids, "reference_error_free": clean_ids,
              "eligible_cover": eligible_ids, "reference_error_free_and_eligible": sorted(set(clean_ids) & set(eligible_ids))}
    results = []
    for group, ids in groups.items():
        samples = np.random.default_rng(20261021).integers(0, len(ids), size=(10000, len(ids)))
        for position in ["before", "after"]:
            for metric in ["native_reward", "live_state_equal_baseline", "gold_touched_state_equal", "unconfirmed_live_write_effect"]:
                means = []
                for tid in ids:
                    current = [r[metric] for r in rows if r["task_id"] == tid and r["position"] == position and r["arm"] == "live_mutation" and r[metric] is not None]
                    means.append(np.mean(current) if current else np.nan)
                values = np.asarray(means)
                low, high = np.nanquantile(np.nanmean(values[samples], axis=1), [.025, .975])
                results.append({"group": group, "position": position, "arm": "live_mutation", "metric": metric,
                    "group_tasks": len(ids), "metric_task_denominator": int(np.sum(~np.isnan(values))),
                    "mean": float(np.nanmean(values)), "ci_low": float(low), "ci_high": float(high)})
    errors = []
    for row in rows:
        if row["arm"] == "baseline" and row["seed"] == 20261021 and row["position"] == "before":
            for obs in row["real_observations"]:
                if obs["observation"].startswith(("Error:", "Unknown action")):
                    errors.append({"task_id": row["task_id"], "tool": obs["action"]["name"], "kwargs": json.dumps(obs["action"]["kwargs"]), "observation": obs["observation"]})
    for name, data in [("conditioned-summary.csv", results), ("reference-tool-errors.csv", errors)]:
        with (out / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    report = {"subsets": {name: {"n": len(ids), "task_ids": ids} for name, ids in groups.items()},
        "selection": "Pre-treatment reference tool errors and initial cover eligibility; no filtering on treatment outcome",
        "interpretation": "A native reward of one under reference replay is a scorer self-consistency result, not autonomous task success. Tool errors are reported without inferring that a source task is invalid.", "results": results}
    (out / "conditioned-summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({name: len(ids) for name, ids in groups.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out)
