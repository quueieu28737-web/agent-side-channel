"""Verify saved lineage and rescore unique saved business states, no model calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import bridge as original


def main(out):
    final = json.loads((out / "final.json").read_bytes())
    launch = json.loads((out / "launch.json").read_bytes())
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    ns, tools, base, tasks = original.load()
    expected = {(tid, seed, pos, arm) for tid in range(len(tasks)) for seed in original.SEEDS for pos in ["before", "after"] for arm in original.ARMS}
    index = {(r["task_id"], r["seed"], r["position"], r["arm"]): r for r in rows}
    if set(index) != expected or len(index) != len(rows):
        raise ValueError("Cell census or uniqueness failed")
    prior = Path(launch["prior"])
    prior_raw = (prior / "episodes.jsonl").read_bytes()
    if hashlib.sha256(prior_raw).hexdigest() != launch["prior_raw_sha256"]:
        raise ValueError("Prior raw hash changed")
    prior_rows = [json.loads(line) for line in prior_raw.splitlines() if line.strip()]
    for row in prior_rows:
        identity = (row["task_id"], row["seed"], row["position"], row["arm"])
        if index[identity] != row:
            raise ValueError("Carried row modified")
    checked, seen = 0, set()
    baseline_cache = {}
    for row in rows:
        tid = row["task_id"]
        identity = (tid, row["final_state_hash"])
        if identity in seen:
            continue
        seen.add(identity)
        task = tasks[tid]
        if tid not in baseline_cache:
            reference = original.env(ns, tools, base, task)
            original.execute_program(reference, task)
            baseline_cache[tid] = reference.data
        actual = copy.deepcopy(baseline_cache[tid])
        if original.digest(actual) != row["baseline_state_hash"]:
            raise ValueError("Baseline lineage mismatch")
        for collection, objects in row["final_deviation"].items():
            for obj, values in objects.items():
                if actual[collection].get(obj) != values["before"]:
                    raise ValueError("Saved deviation does not join to baseline")
                if values["after"] is None:
                    actual[collection].pop(obj, None)
                else:
                    actual[collection][obj] = values["after"]
        if original.digest(actual) != row["final_state_hash"]:
            raise ValueError("Reconstructed final state mismatch")
        scorer = original.env(ns, tools, base, task)
        scorer.data = actual
        scorer.actions = [ns["Action"](**item["action"]) for item in row["real_observations"]]
        original.finish_outputs(ns, scorer, task)
        reward = scorer.calculate_reward().reward
        if reward != row["native_reward"]:
            raise ValueError("Native saved reward mismatch")
        checked += 1
    invariants = {}
    for arm in original.ARMS:
        selected = [r for r in rows if r["arm"] == arm]
        invariants[arm] = {"cells": len(selected), "baseline_equal": sum(r["live_state_equal_baseline"] for r in selected),
            "unconfirmed_write_effects": sum(r["unconfirmed_live_write_effect"] for r in selected)}
    result = {"status": "VERIFIED_SAVED_CENSUS_AND_NATIVE_RESCORING", "tasks": len(tasks), "cells": len(rows),
        "unique_task_final_states_rescored": checked, "carried_cells_unchanged": len(prior_rows),
        "new_cells": len(rows)-len(prior_rows), "arms": invariants,
        "model_calls": 0, "replayed_task_collection": False,
        "scope": "Saved deterministic task-state/reward checks, not independent human review or a privacy attack evaluation"}
    (out / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out)
