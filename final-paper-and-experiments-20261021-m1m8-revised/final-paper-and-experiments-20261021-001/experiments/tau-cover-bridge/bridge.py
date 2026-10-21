"""Original tau-bench tools/reward; controlled gold-program cover routing."""
import argparse
import ast
import copy
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
SEEDS = [20261021, 20261022, 20261023]
ARMS = ["baseline", "discard", "shadow", "read_only", "live_mutation"]


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def path(name):
    return VENDOR / name.replace("/", "__")


def load():
    manifest = json.loads((ROOT / "sources.json").read_bytes())
    for item in manifest["files"]:
        if hashlib.sha256((VENDOR / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Source mismatch " + item["file"])
    ns = {"__name__": "tau_cover_pinned"}
    def execute(name):
        tree = ast.parse(path(name).read_bytes(), filename=name)
        tree.body = [node for node in tree.body if not
                     (isinstance(node, ast.ImportFrom) and (node.module or "").startswith("tau_bench"))]
        exec(compile(tree, name, "exec"), ns)
    execute("tau_bench/types.py")
    execute("tau_bench/envs/tool.py")
    ns.update(load_user=lambda **kw: None, UserStrategy=str)
    execute("tau_bench/envs/base.py")
    classes = {}
    for file in sorted(VENDOR.glob("tau_bench__envs__retail__tools__*.py")):
        if file.name.endswith("____init__.py"):
            continue
        before = set(ns)
        execute(file.name.replace("__", "/"))
        for key in set(ns) - before:
            item = ns[key]
            if isinstance(item, type) and issubclass(item, ns["Tool"]):
                classes[item.get_info()["function"]["name"]] = item
    execute("tau_bench/envs/retail/tasks_test.py")
    data = {name: json.loads(path(f"tau_bench/envs/retail/data/{name}.json").read_bytes()) for name in ["orders", "users", "products"]}
    return ns, classes, data, ns["TASKS_TEST"]


class User:
    def step(self, text):
        return "ACK"
    def get_total_cost(self):
        return 0


def env(ns, tools, base, task):
    item = ns["Env"].__new__(ns["Env"])
    item.data_load_func = lambda: copy.deepcopy(base)
    item.data = copy.deepcopy(base)
    item.tools_map = tools
    item.terminate_tools = []
    item.actions = []
    item.task = task
    item.user = User()
    return item


def delta(before, after):
    changes = {}
    for collection in before.keys() | after.keys():
        a, b = before.get(collection, {}), after.get(collection, {})
        changed = {key: {"before": copy.deepcopy(a.get(key)), "after": copy.deepcopy(b.get(key))} for key in a.keys() | b.keys() if a.get(key) != b.get(key)}
        if changed:
            changes[collection] = changed
    return changes


def finish_outputs(ns, item, task):
    for output in task.outputs:
        item.actions.append(ns["Action"](name="respond", kwargs={"content": output}))


def execute_program(item, task):
    observations = []
    for action in task.actions:
        result = item.step(action)
        observations.append({"action": action.model_dump(), "observation": result.observation})
    return observations


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    ns, tools, base, tasks = load()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    deadline = time.monotonic() + 900
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / "PROTOCOL.txt", ROOT / "bridge.py", ROOT / "sources.json"]}
    (out / "launch.json").write_text(json.dumps({"started_utc": started, "command": sys.argv, "source_hashes": hashes,
        "tasks": len(tasks), "seeds": SEEDS, "positions": ["before", "after"], "arms": ARMS,
        "model_calls": 0, "hard_deadline_s": 900}, indent=2), encoding="utf-8")
    rows = []
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        for task_id, task in enumerate(tasks):
            baseline = env(ns, tools, base, task)
            baseline_obs = execute_program(baseline, task)
            finish_outputs(ns, baseline, task)
            expected = baseline.data
            expected_hash = digest(expected)
            gold_changes = delta(base, expected)
            base_errors = sum(x["observation"].startswith(("Error:", "Unknown action")) for x in baseline_obs)
            baseline_reward = baseline.calculate_reward().reward
            for seed in SEEDS:
                candidates = sorted(key for key, value in base["orders"].items() if value["user_id"] == task.user_id and value["status"] == "pending")
                rng = random.Random(seed + task_id * 1009)
                order = rng.choice(candidates) if candidates else None
                for position in ["before", "after"]:
                    for arm in ARMS:
                        if time.monotonic() > deadline:
                            raise TimeoutError("Frozen 900 second deadline")
                        item = env(ns, tools, base, task)
                        cover_before, cover_after, observation = None, None, None
                        wall_start = time.perf_counter_ns()
                        if position == "after":
                            real_obs = execute_program(item, task)
                        invoke_start = time.perf_counter_ns()
                        if order is not None and arm != "baseline":
                            if arm == "discard":
                                observation = "DISCARDED"
                            elif arm == "shadow":
                                shadow = copy.deepcopy(item.data)
                                observation = tools["cancel_pending_order"].invoke(shadow, order_id=order, reason="no longer needed")
                            elif arm == "read_only":
                                observation = tools["get_order_details"].invoke(item.data, order_id=order)
                            elif arm == "live_mutation":
                                cover_before = copy.deepcopy(item.data)
                                observation = tools["cancel_pending_order"].invoke(item.data, order_id=order, reason="no longer needed")
                                cover_after = item.data
                        invoke_ns = time.perf_counter_ns() - invoke_start
                        cover_delta = delta(cover_before, cover_after) if cover_before is not None else {}
                        if position == "before":
                            real_obs = execute_program(item, task)
                        finish_outputs(ns, item, task)
                        final_hash = digest(item.data)
                        final_changes = delta(expected, item.data)
                        touched_equal = all(item.data[collection].get(key) == expected[collection].get(key)
                                            for collection, changes in gold_changes.items() for key in changes)
                        elapsed_ns = time.perf_counter_ns() - wall_start
                        native_reward = item.calculate_reward().reward
                        row = {"task_id": task_id, "task_user": task.user_id, "seed": seed,
                            "position": position, "arm": arm, "eligible_cover_orders": len(candidates),
                            "cover_order": order, "cover_overlaps_gold_order": any(a.kwargs.get("order_id") == order for a in task.actions) if order else False,
                            "baseline_reward": baseline_reward, "native_reward": native_reward,
                            "baseline_tool_errors": base_errors,
                            "real_tool_errors": sum(x["observation"].startswith(("Error:", "Unknown action")) for x in real_obs),
                            "live_state_equal_baseline": final_hash == expected_hash,
                            "gold_touched_state_equal": touched_equal if gold_changes else None,
                            "unconfirmed_live_write_attempt": bool(order and arm == "live_mutation"),
                            "unconfirmed_live_write_effect": bool(cover_delta),
                            "cover_result_error": str(observation).startswith("Error:"),
                            "cover_result_bytes": len((observation or "").encode()),
                            "cover_invocation_ns": invoke_ns, "local_elapsed_ns": elapsed_ns,
                            "baseline_state_hash": expected_hash, "final_state_hash": final_hash,
                            "cover_state_changes": cover_delta, "final_deviation": final_changes,
                            "real_observations": real_obs, "cover_observation": observation}
                        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                        stream.flush()
                        rows.append(row)
            (out / "progress.json").write_text(json.dumps({"closed_tasks": task_id + 1, "total_tasks": len(tasks), "episodes": len(rows)}), encoding="utf-8")
            print(f"task {task_id + 1}/{len(tasks)}; episodes {len(rows)}", flush=True)
    (out / "final.json").write_text(json.dumps({"status": "COMPLETED", "started_utc": started,
        "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "tasks": len(tasks), "episodes": len(rows),
        "model_calls": 0, "source_hashes": hashes}, indent=2), encoding="utf-8")
    analyze(out)


def analyze(out):
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    task_ids = sorted({row["task_id"] for row in rows})
    metrics = ["native_reward", "live_state_equal_baseline", "gold_touched_state_equal", "unconfirmed_live_write_attempt", "unconfirmed_live_write_effect", "real_tool_errors"]
    result = []
    rng = np.random.default_rng(20261021)
    samples = rng.integers(0, len(task_ids), size=(10000, len(task_ids)))
    for position in ["before", "after"]:
        for arm in ARMS:
            selected = [row for row in rows if row["position"] == position and row["arm"] == arm]
            for metric in metrics:
                values = []
                for task_id in task_ids:
                    task_rows = [row for row in selected if row["task_id"] == task_id and row[metric] is not None]
                    if not task_rows:
                        values.append(np.nan)
                    else:
                        values.append(np.mean([float(row[metric]) for row in task_rows]))
                values = np.asarray(values)
                draws = np.nanmean(values[samples], axis=1)
                low, high = np.quantile(draws, [.025, .975])
                result.append({"position": position, "arm": arm, "metric": metric,
                    "task_denominator": int(np.sum(~np.isnan(values))), "mean": float(np.nanmean(values)),
                    "ci_low": float(low), "ci_high": float(high), "interval": "whole-task percentile bootstrap, 10000 draws"})
    pairs = []
    for position in ["before", "after"]:
        for arm in ARMS[1:]:
            for metric in ["native_reward", "live_state_equal_baseline", "gold_touched_state_equal"]:
                differences = []
                for tid in task_ids:
                    treated = [r[metric] for r in rows if r["position"] == position and r["arm"] == arm and r["task_id"] == tid and r[metric] is not None]
                    control = [r[metric] for r in rows if r["position"] == position and r["arm"] == "baseline" and r["task_id"] == tid and r[metric] is not None]
                    differences.append(np.mean(treated) - np.mean(control) if treated and control else np.nan)
                values = np.asarray(differences)
                low, high = np.quantile(np.nanmean(values[samples], axis=1), [.025, .975])
                pairs.append({"position": position, "arm": arm, "metric": metric, "paired_difference": float(np.nanmean(values)), "ci_low": float(low), "ci_high": float(high)})
    for name, data in [("summary.csv", result), ("paired-effects.csv", pairs)]:
        with (out / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    summary = {"tasks": len(task_ids), "episodes": len(rows), "eligible_tasks": len({r["task_id"] for r in rows if r["cover_order"]}),
        "reference_error_tasks": sorted({r["task_id"] for r in rows if r["baseline_tool_errors"]}),
        "scope": "fixed gold-program execution; no autonomous model or privacy inference", "metrics": result, "paired_effects": pairs}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ["metrics", "paired_effects"]}))


def test():
    ns, tools, base, tasks = load()
    before = digest(base)
    eligible = next(key for key, value in base["orders"].items() if value["status"] == "pending")
    read = tools["get_order_details"].invoke(base, order_id=eligible)
    assert digest(base) == before
    shadow = copy.deepcopy(base)
    tools["cancel_pending_order"].invoke(shadow, order_id=eligible, reason="no longer needed")
    assert digest(shadow) != before and digest(base) == before
    native = env(ns, tools, base, tasks[0])
    execute_program(native, tasks[0])
    finish_outputs(ns, native, tasks[0])
    assert native.calculate_reward().reward == 1
    print(json.dumps({"status": "OFFLINE_TESTS_PASSED", "tasks": len(tasks), "tools": len(tools), "read_only_pure": True, "shadow_isolated": True, "native_reward": 1}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["test", "run", "analyze"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "test":
        test()
    elif args.command == "run":
        run(args.out)
    else:
        analyze(args.out)


if __name__ == "__main__":
    main()
