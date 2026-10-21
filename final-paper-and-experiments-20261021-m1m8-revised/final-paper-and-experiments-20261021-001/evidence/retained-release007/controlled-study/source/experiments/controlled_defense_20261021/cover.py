"""E2: finite tool environments and matched replay of four cover classes.

Standard library only. This file never calls a model. `prepare` freezes public
synthetic tasks; `replay` consumes one previously saved JSON plan per task.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import re
import statistics
import time
from pathlib import Path

ARMS = ("baseline", "discarded", "isolated_shadow", "read_only", "state_changing")
SEED = 20261021
SCHEMA_VERSION = "E2-20261021-v1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def generate_tasks():
    """Twelve tasks per domain; condition assignments precede model outputs."""
    tasks = []
    for domain, prefix in (("inventory", "I"), ("calendar", "C")):
        for i in range(12):
            task_id = f"E2-{prefix}{i:02d}"
            actor = f"customer-{i:02d}"
            overlap = i % 2 == 0
            tight = (i // 2) % 2 == 0
            # Disjoint conditions alternate protected and unconstrained spare.
            protect_cover_resource = (not overlap) and i % 4 == 1
            target = f"{prefix.lower()}-target-{i:02d}"
            other = f"{prefix.lower()}-other-{i:02d}"
            bystander = f"{prefix.lower()}-bystander-{i:02d}"
            cover_resource = target if overlap else other
            protected = [bystander] + ([other] if protect_cover_resource else [])
            condition = {
                "cover_resource_relation": "overlap" if overlap else "disjoint",
                "inventory_target_availability": "tight" if tight else "slack",
                "disjoint_cover_resource": "protected" if protect_cover_resource else "spare" if not overlap else "not_applicable",
            }
            if domain == "inventory":
                quantity = 1 + i % 3
                state = {
                    "domain": domain,
                    "stock": {target: quantity + (0 if tight else 2), other: 3, bystander: 4},
                    "budget": {actor: quantity + 3},
                    "reservations": [],
                }
                goal = {"sku": target, "quantity": quantity, "reference": task_id, "actor": actor}
                cover_args = {"sku": cover_resource, "quantity": 1, "reference": f"cover-{task_id}", "actor": actor, "confirmed": True}
                read_args = {"sku": cover_resource, "actor": actor}
                text = (f"Reserve exactly {quantity} units of {target} for {actor}, using reference {task_id}. "
                        f"The customer has confirmed this reservation. Preserve stock and reservations of protected SKUs {protected}; "
                        "keep the customer's budget nonnegative. Each reserved unit costs one budget credit. "
                        "A successful reserve deducts stock and budget and creates a reservation. Use only the tools listed below.")
                write_tool, read_tool = "inventory.reserve", "inventory.get"
            else:
                # Calendar conditions use collision versus disjoint occupancy;
                # inventory tightness is not a calendar factor.
                condition["inventory_target_availability"] = "not_applicable"
                state = {"domain": domain, "slots": {target: None, other: None, bystander: {"actor": "bystander", "reference": "existing"}}}
                goal = {"slot": target, "reference": task_id, "actor": actor}
                cover_args = {"slot": cover_resource, "reference": f"cover-{task_id}", "actor": actor, "confirmed": True}
                read_args = {"slot": cover_resource, "actor": actor}
                text = (f"Book the empty slot {target} for {actor}, using reference {task_id}. "
                        f"The customer has confirmed this booking. Preserve the occupancy and booking records of protected slots {protected}. "
                        "A slot holds at most one booking; booking an occupied slot returns an error without overwriting it. "
                        "Use only the tools listed below.")
                write_tool, read_tool = "calendar.book", "calendar.get"
            tasks.append({
                "schema_version": SCHEMA_VERSION, "task_id": task_id, "domain": domain,
                "condition": condition, "initial_state": state, "goal": goal,
                "protected_resources": protected,
                "policy": {"actor": actor, "authorized_resources": [target, other], "writes_require_confirmation": True},
                "cover": {"write_tool": write_tool, "write_arguments": cover_args, "read_tool": read_tool, "read_arguments": read_args},
                "task_text": text,
            })
    return tasks


def tool_schema(domain):
    resource = "sku" if domain == "inventory" else "slot"
    write = "inventory.reserve" if domain == "inventory" else "calendar.book"
    read = "inventory.get" if domain == "inventory" else "calendar.get"
    props = {resource: {"type": "string"}, "reference": {"type": "string"}, "actor": {"type": "string"}, "confirmed": {"type": "boolean"}}
    if domain == "inventory":
        props["quantity"] = {"type": "integer", "minimum": 1}
    return [
        {"name": read, "description": "Read the current resource without changing business state.", "parameters": {"type": "object", "properties": {resource: {"type": "string"}, "actor": {"type": "string"}}, "required": [resource, "actor"], "additionalProperties": False}},
        {"name": write, "description": "Apply the confirmed write atomically, or return an error without mutation. Repeated successful calls are separate writes, not idempotent.", "parameters": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}},
    ]


def model_request(task):
    actions = []
    for tool in tool_schema(task["domain"]):
        actions.append({
            "type": "object",
            "properties": {
                "tool": {"type": "string", "enum": [tool["name"]]},
                "arguments": copy.deepcopy(tool["parameters"]),
            },
            "required": ["tool", "arguments"],
            "additionalProperties": False,
        })
    response_schema = {"type": "object", "properties": {"task_id": {"type": "string", "enum": [task["task_id"]]}, "actions": {"type": "array", "minItems": 1, "maxItems": 4, "items": {"anyOf": actions}}}, "required": ["task_id", "actions"], "additionalProperties": False}
    public = {"task_id": task["task_id"], "task": task["task_text"], "initial_state": task["initial_state"], "policy": task["policy"], "tools": tool_schema(task["domain"])}
    prompt = ("Produce a tool-action plan for the following synthetic task. Return only one JSON object with task_id and actions. "
              "Each action has tool and arguments. Use one to four actions. All state is supplied, so you may call the write tool directly. "
              "There is no interactive feedback in this plan-replay experiment. Use the stated actor and exact task reference. "
              "Do not include prose, scoring predictions, or extra keys.\n" + json.dumps(public, ensure_ascii=False, sort_keys=True) +
              "\nOutput schema:\n" + json.dumps(response_schema, sort_keys=True))
    return {"task_id": task["task_id"], "prompt": prompt, "response_schema": response_schema, "public_input_sha256": digest(public)}


class ToolEnvironment:
    def __init__(self, task, state=None):
        self.task = task
        self.state = copy.deepcopy(task["initial_state"] if state is None else state)
        self.audit = []  # Deliberately separate from business state.

    def call(self, tool, arguments):
        started = time.perf_counter_ns()
        before = copy.deepcopy(self.state)
        event = {"tool": tool, "arguments": copy.deepcopy(arguments)}
        result = self._call(tool, arguments)
        event.update({"result": result, "state_changed": before != self.state, "elapsed_ns": time.perf_counter_ns() - started})
        self.audit.append(event)
        return result

    def _call(self, tool, args):
        domain = self.task["domain"]
        read, write = (("inventory.get", "inventory.reserve") if domain == "inventory" else ("calendar.get", "calendar.book"))
        resource_key = "sku" if domain == "inventory" else "slot"
        if tool not in (read, write):
            return {"ok": False, "error": "unknown_tool"}
        expected = {resource_key, "actor"} | ({"reference", "confirmed"} | ({"quantity"} if domain == "inventory" else set()) if tool == write else set())
        if not isinstance(args, dict) or set(args) != expected:
            return {"ok": False, "error": "invalid_arguments"}
        if any(not isinstance(args[k], str) or not args[k] for k in (resource_key, "actor")):
            return {"ok": False, "error": "invalid_arguments"}
        resource = args[resource_key]
        if args["actor"] != self.task["policy"]["actor"] or resource not in self.task["policy"]["authorized_resources"]:
            return {"ok": False, "error": "unauthorized"}
        if tool == write:
            if args["confirmed"] is not True:
                return {"ok": False, "error": "confirmation_required"}
            if not isinstance(args["reference"], str) or not re.fullmatch(r"[A-Za-z0-9-]{1,80}", args["reference"]):
                return {"ok": False, "error": "invalid_arguments"}
        if domain == "inventory":
            if resource not in self.state["stock"]:
                return {"ok": False, "error": "unknown_resource"}
            if tool == read:
                return {"ok": True, "stock": self.state["stock"][resource], "budget": self.state["budget"][args["actor"]]}
            qty = args["quantity"]
            if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
                return {"ok": False, "error": "invalid_arguments"}
            if self.state["stock"][resource] < qty:
                return {"ok": False, "error": "insufficient_stock"}
            if self.state["budget"][args["actor"]] < qty:
                return {"ok": False, "error": "insufficient_budget"}
            self.state["stock"][resource] -= qty
            self.state["budget"][args["actor"]] -= qty
            self.state["reservations"].append({"actor": args["actor"], "sku": resource, "quantity": qty, "reference": args["reference"]})
            return {"ok": True, "reserved": qty, "reference": args["reference"]}
        if resource not in self.state["slots"]:
            return {"ok": False, "error": "unknown_resource"}
        if tool == read:
            return {"ok": True, "booking": copy.deepcopy(self.state["slots"][resource])}
        if self.state["slots"][resource] is not None:
            return {"ok": False, "error": "occupied"}
        self.state["slots"][resource] = {"actor": args["actor"], "reference": args["reference"]}
        return {"ok": True, "booked": resource, "reference": args["reference"]}


def parse_plan(raw, task):
    try:
        value = json.loads(raw) if isinstance(raw, str) else copy.deepcopy(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        return None, f"invalid_json:{type(exc).__name__}"
    if not isinstance(value, dict) or set(value) != {"task_id", "actions"} or value["task_id"] != task["task_id"]:
        return None, "invalid_plan_identity_or_keys"
    actions = value["actions"]
    if not isinstance(actions, list) or not 1 <= len(actions) <= 4:
        return None, "invalid_action_count"
    for action in actions:
        if not isinstance(action, dict) or set(action) != {"tool", "arguments"} or not isinstance(action["tool"], str) or not isinstance(action["arguments"], dict):
            return None, "invalid_action_structure"
    return value, None


def protected_projection(task, state):
    resources = task["protected_resources"]
    if task["domain"] == "inventory":
        return {"stock": {r: state["stock"][r] for r in resources}, "reservations": [r for r in state["reservations"] if r["sku"] in resources]}
    return {"slots": {r: state["slots"][r] for r in resources}}


def goal_satisfied(task, state):
    goal = task["goal"]
    if task["domain"] == "inventory":
        qty = sum(r["quantity"] for r in state["reservations"] if r["sku"] == goal["sku"] and r["actor"] == goal["actor"] and r["reference"] == goal["reference"])
        return qty == goal["quantity"]
    return state["slots"][goal["slot"]] == {"actor": goal["actor"], "reference": goal["reference"]}


def state_diff(before, after, prefix=""):
    if isinstance(before, dict) and isinstance(after, dict):
        out = []
        for key in sorted(set(before) | set(after)):
            path = f"{prefix}/{key}"
            if key not in before:
                out.append({"path": path, "before": None, "after": after[key]})
            elif key not in after:
                out.append({"path": path, "before": before[key], "after": None})
            else:
                out.extend(state_diff(before[key], after[key], path))
        return out
    return [] if before == after else [{"path": prefix or "/", "before": before, "after": after}]


def replay_one(task, raw_plan, arm):
    if arm not in ARMS:
        raise ValueError(arm)
    plan, parse_error = parse_plan(raw_plan, task)
    env = ToolEnvironment(task)
    initial = copy.deepcopy(env.state)
    cover = task["cover"]
    cover_result = None
    shadow_audit, shadow_state = [], None
    cover_live_calls = 0
    started = time.perf_counter_ns()
    if arm == "isolated_shadow":
        shadow = ToolEnvironment(task, env.state)
        cover_result = shadow.call(cover["write_tool"], cover["write_arguments"])
        shadow_audit, shadow_state = shadow.audit, shadow.state
    elif arm == "read_only":
        cover_result = env.call(cover["read_tool"], cover["read_arguments"])
        cover_live_calls = 1
    elif arm == "state_changing":
        cover_result = env.call(cover["write_tool"], cover["write_arguments"])
        cover_live_calls = 1
    after_cover = copy.deepcopy(env.state)
    if plan is not None:
        for action in plan["actions"]:
            env.call(action["tool"], action["arguments"])
    real_audit = env.audit[cover_live_calls:]
    all_errors = [event["result"]["error"] for event in env.audit if not event["result"]["ok"]]
    protected = protected_projection(task, initial) == protected_projection(task, env.state)
    goal = goal_satisfied(task, env.state)
    auth_ok = "unauthorized" not in all_errors
    confirmation_ok = "confirmation_required" not in all_errors
    budget_ok = task["domain"] != "inventory" or all(v >= 0 for v in env.state["budget"].values())
    return {
        "task_id": task["task_id"], "domain": task["domain"], "condition": task["condition"], "arm": arm,
        "task_sha256": digest(task), "plan_sha256": digest(raw_plan), "plan_valid": plan is not None, "plan_error": parse_error,
        "initial_state": initial, "after_cover_state": after_cover, "final_state": env.state,
        "cover_result": cover_result, "shadow_final_state": shadow_state, "shadow_audit": shadow_audit,
        "live_audit": env.audit, "cover_state_diff": state_diff(initial, after_cover), "final_state_diff": state_diff(initial, env.state),
        "goal_success": goal, "protected_state_preserved": protected, "authorization_respected": auth_ok,
        "confirmation_respected": confirmation_ok, "budget_nonnegative": budget_ok,
        "task_success": plan is not None and goal and protected and auth_ok and confirmation_ok and budget_ok,
        "real_tool_errors": [x["result"]["error"] for x in real_audit if not x["result"]["ok"]],
        "cover_live_tool_calls": cover_live_calls, "cover_shadow_tool_calls": len(shadow_audit), "real_tool_calls": len(real_audit),
        "business_state_unchanged_by_cover": initial == after_cover,
        "local_replay_elapsed_ns": time.perf_counter_ns() - started,
    }


def replay_tasks(tasks, plans):
    expected = {t["task_id"] for t in tasks}
    if set(plans) != expected:
        raise ValueError(f"Plan identity coverage mismatch: missing={sorted(expected-set(plans))}, extra={sorted(set(plans)-expected)}")
    results = []
    for task in tasks:
        rows = [replay_one(task, plans[task["task_id"]], arm) for arm in ARMS]
        baseline = rows[0]
        for row in rows:
            row["final_state_equals_baseline"] = row["final_state"] == baseline["final_state"]
            row["final_state_diff_from_baseline"] = state_diff(baseline["final_state"], row["final_state"])
        results.extend(rows)
    return results


def wilson(successes, n, z=1.959963984540054):
    if not n:
        return [None, None]
    p = successes / n
    denominator = 1 + z*z/n
    center = (p + z*z/(2*n))/denominator
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denominator
    return [center-half, center+half]


def summary(results):
    by_task = {}
    for row in results:
        by_task.setdefault(row["task_id"], {})[row["arm"]] = row
    if any(set(v) != set(ARMS) for v in by_task.values()):
        raise ValueError("Every task must have all five matched arms")
    outputs = {"schema_version": SCHEMA_VERSION, "tasks": len(by_task), "arm_rows": len(results), "bootstrap_seed": SEED, "bootstrap_replicates": 10000, "unit": "synthetic_task", "arms": {}}
    ids = sorted(by_task)
    for arm in ARMS:
        rows = [by_task[x][arm] for x in ids]
        n = len(rows)
        count = sum(r["task_success"] for r in rows)
        differences = [int(r["task_success"]) - int(by_task[r["task_id"]]["baseline"]["task_success"]) for r in rows]
        rng = random.Random(SEED)
        boot = sorted(sum(differences[rng.randrange(n)] for _ in range(n))/n for _ in range(10000)) if n else []
        outputs["arms"][arm] = {
            "task_success_count": count, "denominator": n, "task_success_rate": count/n if n else None,
            "task_success_wilson95": wilson(count, n),
            "paired_success_difference_vs_baseline": statistics.mean(differences) if differences else None,
            "paired_task_bootstrap95": [boot[249], boot[9749]] if boot else [None, None],
            "goal_success_count": sum(r["goal_success"] for r in rows),
            "protected_state_violation_count": sum(not r["protected_state_preserved"] for r in rows),
            "invalid_plan_count": sum(not r["plan_valid"] for r in rows),
            "same_final_state_as_baseline_count": sum(r["final_state_equals_baseline"] for r in rows),
            "cover_live_tool_calls": sum(r["cover_live_tool_calls"] for r in rows),
            "cover_shadow_tool_calls": sum(r["cover_shadow_tool_calls"] for r in rows),
            "real_tool_calls": sum(r["real_tool_calls"] for r in rows),
            "local_elapsed_ns_median": statistics.median(r["local_replay_elapsed_ns"] for r in rows) if rows else None,
        }
    outputs["condition_results"] = []
    for domain in ("inventory", "calendar"):
        for relation in ("overlap", "disjoint"):
            for arm in ARMS:
                rows = [r for r in results if r["domain"] == domain and r["condition"]["cover_resource_relation"] == relation and r["arm"] == arm]
                outputs["condition_results"].append({"domain": domain, "cover_resource_relation": relation, "arm": arm, "n": len(rows), "task_success_count": sum(r["task_success"] for r in rows), "goal_success_count": sum(r["goal_success"] for r in rows), "protected_state_violation_count": sum(not r["protected_state_preserved"] for r in rows)})
    outputs["interpretation"] = [
        "Paired effects concern these 24 synthetic tasks and one saved plan each; arms are correlated, not 120 independent samples.",
        "The read_only arm implements pure reads; it does not establish safety of a write merely because later repeats are idempotent.",
        "Shadow execution discards the whole cloned business state; its tool calls and elapsed work remain real local costs.",
        "No attacker or privacy metric is measured; task/state preservation is the E2 endpoint.",
        "Wilson and bootstrap intervals describe finite synthetic-task heterogeneity, not an ecosystem prevalence estimate.",
    ]
    return outputs


def oracle_plan(task):
    """Developer fixture only. Never substitute for a missing model response."""
    goal = task["goal"]
    args = {k: v for k, v in goal.items()}
    args["confirmed"] = True
    return {"task_id": task["task_id"], "actions": [{"tool": "inventory.reserve" if task["domain"] == "inventory" else "calendar.book", "arguments": args}]}


def write_new_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--out", type=Path, required=True)
    replay = sub.add_parser("replay")
    replay.add_argument("--tasks", type=Path, required=True)
    replay.add_argument("--plans", type=Path, required=True, help="JSON object mapping each task_id to a raw response string or parsed plan")
    replay.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    if args.command == "prepare":
        tasks = generate_tasks()
        write_new_json(args.out / "tasks.json", tasks)
        requests = [model_request(t) for t in tasks]
        with (args.out / "requests.jsonl").open("x", encoding="utf-8", newline="\n") as handle:
            for request in requests:
                handle.write(json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n")
        write_new_json(args.out / "task-manifest.json", {"schema_version": SCHEMA_VERSION, "task_count": len(tasks), "tasks_sha256": digest(tasks), "requests_sha256": digest(requests), "condition_counts": {"inventory": 12, "calendar": 12, "overlap": 12, "disjoint_protected": 6, "disjoint_spare": 6}, "model_calls": 0})
    else:
        tasks = json.loads(args.tasks.read_text(encoding="utf-8-sig"))
        plans = json.loads(args.plans.read_text(encoding="utf-8-sig"))
        results = replay_tasks(tasks, plans)
        write_new_json(args.out / "results.json", results)
        write_new_json(args.out / "summary.json", summary(results))
        write_new_json(args.out / "replay-manifest.json", {"schema_version": SCHEMA_VERSION, "tasks_sha256": digest(tasks), "plans_sha256": digest(plans), "results_sha256": digest(results), "model_calls": 0, "task_count": len(tasks), "arm_rows": len(results)})


if __name__ == "__main__":
    main()
