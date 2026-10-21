"""Continue unexecuted deterministic cells, caching identical native score states.

The original native scorer is unchanged. Duplicate whole-state/output contexts
reuse its exact saved result. Previously started cells are never executed again.
"""
import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import bridge as original

ROOT = Path(__file__).resolve().parent


def key(row):
    return (row["task_id"], row["seed"], row["position"], row["arm"])


def main(prior, out):
    raw = (prior / "episodes.jsonl").read_bytes()
    lines = raw.splitlines()
    carried = [json.loads(line) for line in lines if line.strip()]
    index = {key(row): row for row in carried}
    if len(index) != len(carried):
        raise ValueError("Duplicate prior cells")
    out.mkdir(parents=True, exist_ok=False)
    ns, tools, base, tasks = original.load()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    (out / "launch.json").write_text(json.dumps({"started_utc": started, "prior": str(prior),
        "prior_raw_sha256": hashlib.sha256(raw).hexdigest(), "carried_cells": len(carried),
        "protocol_sha256": hashlib.sha256((ROOT / "PROTOCOL.txt").read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_runner_sha256": hashlib.sha256((ROOT / "bridge.py").read_bytes()).hexdigest(),
        "change": "native-scoring result memoization by complete final-state hash within each fixed task; skip all prior cells",
        "model_calls": 0, "hard_deadline_s": 900}, indent=2), encoding="utf-8")
    deadline = time.monotonic() + 900
    actual_native_scores, cache_hits = 0, 0
    with (out / "new-cells.jsonl").open("x", encoding="utf-8") as stream:
        for task_id, task in enumerate(tasks):
            baseline = original.env(ns, tools, base, task)
            baseline_obs = original.execute_program(baseline, task)
            original.finish_outputs(ns, baseline, task)
            expected = baseline.data
            expected_hash = original.digest(expected)
            gold_changes = original.delta(base, expected)
            base_errors = sum(x["observation"].startswith(("Error:", "Unknown action")) for x in baseline_obs)
            baseline_reward = baseline.calculate_reward().reward
            actual_native_scores += 1
            cache = {expected_hash: baseline_reward}
            for row in carried:
                if row["task_id"] == task_id:
                    if row["baseline_state_hash"] != expected_hash:
                        raise ValueError("Prior baseline lineage mismatch")
                    if row["final_state_hash"] in cache and cache[row["final_state_hash"]] != row["native_reward"]:
                        raise ValueError("Inconsistent native scorer cache")
                    cache[row["final_state_hash"]] = row["native_reward"]
            for seed in original.SEEDS:
                candidates = sorted(order for order, value in base["orders"].items() if value["user_id"] == task.user_id and value["status"] == "pending")
                rng = random.Random(seed + task_id * 1009)
                order = rng.choice(candidates) if candidates else None
                for position in ["before", "after"]:
                    for arm in original.ARMS:
                        identity = (task_id, seed, position, arm)
                        if identity in index:
                            continue
                        if time.monotonic() > deadline:
                            raise TimeoutError("Continuation 900 second deadline")
                        item = original.env(ns, tools, base, task)
                        observation, cover_before, cover_after = None, None, None
                        wall_start = time.perf_counter_ns()
                        if position == "after":
                            real_obs = original.execute_program(item, task)
                        invoke_start = time.perf_counter_ns()
                        if order is not None and arm != "baseline":
                            if arm == "discard":
                                observation = "DISCARDED"
                            elif arm == "shadow":
                                shadow = copy.deepcopy(item.data)
                                observation = tools["cancel_pending_order"].invoke(shadow, order_id=order, reason="no longer needed")
                            elif arm == "read_only":
                                observation = tools["get_order_details"].invoke(item.data, order_id=order)
                            else:
                                cover_before = copy.deepcopy(item.data)
                                observation = tools["cancel_pending_order"].invoke(item.data, order_id=order, reason="no longer needed")
                                cover_after = item.data
                        invoke_ns = time.perf_counter_ns() - invoke_start
                        cover_delta = original.delta(cover_before, cover_after) if cover_before is not None else {}
                        if position == "before":
                            real_obs = original.execute_program(item, task)
                        original.finish_outputs(ns, item, task)
                        final_hash = original.digest(item.data)
                        final_changes = original.delta(expected, item.data)
                        touched_equal = all(item.data[collection].get(obj) == expected[collection].get(obj) for collection, changes in gold_changes.items() for obj in changes)
                        elapsed_ns = time.perf_counter_ns() - wall_start
                        if final_hash in cache:
                            native_reward = cache[final_hash]
                            cache_hits += 1
                        else:
                            native_reward = item.calculate_reward().reward
                            cache[final_hash] = native_reward
                            actual_native_scores += 1
                        row = {"task_id": task_id, "task_user": task.user_id, "seed": seed,
                            "position": position, "arm": arm, "eligible_cover_orders": len(candidates),
                            "cover_order": order, "cover_overlaps_gold_order": any(a.kwargs.get("order_id") == order for a in task.actions) if order else False,
                            "baseline_reward": baseline_reward, "native_reward": native_reward,
                            "baseline_tool_errors": base_errors,
                            "real_tool_errors": sum(x["observation"].startswith(("Error:", "Unknown action")) for x in real_obs),
                            "live_state_equal_baseline": final_hash == expected_hash,
                            "gold_touched_state_equal": touched_equal if gold_changes else None,
                            "unconfirmed_live_write_attempt": bool(order and arm == "live_mutation"),
                            "unconfirmed_live_write_effect": bool(cover_delta), "cover_result_error": str(observation).startswith("Error:"),
                            "cover_result_bytes": len((observation or "").encode()), "cover_invocation_ns": invoke_ns,
                            "local_elapsed_ns": elapsed_ns, "baseline_state_hash": expected_hash,
                            "final_state_hash": final_hash, "cover_state_changes": cover_delta,
                            "final_deviation": final_changes, "real_observations": real_obs, "cover_observation": observation}
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        stream.flush()
                        index[identity] = row
            (out / "progress.json").write_text(json.dumps({"closed_tasks": task_id+1, "total_tasks": len(tasks), "total_cells": len(index),
                "carried_cells": len(carried), "native_score_executions": actual_native_scores, "native_score_cache_hits": cache_hits}), encoding="utf-8")
            print(f"task {task_id+1}/{len(tasks)}; cells {len(index)}", flush=True)
    expected_keys = {(task_id, seed, pos, arm) for task_id in range(len(tasks)) for seed in original.SEEDS for pos in ["before", "after"] for arm in original.ARMS}
    if set(index) != expected_keys:
        raise ValueError("Incomplete or extra cell inventory")
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        for identity in sorted(index):
            stream.write(json.dumps(index[identity], ensure_ascii=False)+"\n")
    (out / "final.json").write_text(json.dumps({"status": "COMPLETED", "started_utc": started,
        "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "tasks": len(tasks), "episodes": len(index),
        "carried_cells": len(carried), "new_cells": len(index)-len(carried),
        "native_score_executions": actual_native_scores, "native_score_cache_hits": cache_hits,
        "prior_raw_sha256": hashlib.sha256(raw).hexdigest(), "model_calls": 0}, indent=2), encoding="utf-8")
    original.analyze(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    main(args.prior, args.out)
