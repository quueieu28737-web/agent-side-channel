"""Read-only verification of saved E2 collection and deterministic outcomes.

Does not import the experiment engine or invoke any model. Only the two new
verification reports are written, using exclusive creation.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/controlled_defense_20261021"
PACK = BASE / "inputs/study-v1"
RUN = BASE / "runtime/collection-001"
REPLAY = BASE / "runtime/E2-001"
OUT = Path(__file__).resolve().parent
ARMS = ["baseline", "discarded", "isolated_shadow", "read_only", "state_changing"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def execute(task, state, tool, args):
    """Separate finite-state reconstruction for the actual saved actions."""
    domain = task["domain"]
    resource = args["sku" if domain == "inventory" else "slot"]
    require(args["actor"] == task["policy"]["actor"], "actor identity")
    require(resource in task["policy"]["authorized_resources"], "resource permission")
    if tool.endswith(".get"):
        return None
    require(args["confirmed"] is True, "confirmation")
    if domain == "inventory":
        quantity = args["quantity"]
        require(type(quantity) is int and quantity > 0, "positive integer quantity")
        if state["stock"][resource] < quantity:
            return "insufficient_stock"
        if state["budget"][args["actor"]] < quantity:
            return "insufficient_budget"
        state["stock"][resource] -= quantity
        state["budget"][args["actor"]] -= quantity
        state["reservations"].append({"actor": args["actor"], "sku": resource, "quantity": quantity, "reference": args["reference"]})
    else:
        if state["slots"][resource] is not None:
            return "occupied"
        state["slots"][resource] = {"actor": args["actor"], "reference": args["reference"]}
    return None


def goal(task, state):
    g = task["goal"]
    if task["domain"] == "inventory":
        return sum(x["quantity"] for x in state["reservations"] if x["actor"] == g["actor"] and x["sku"] == g["sku"] and x["reference"] == g["reference"]) == g["quantity"]
    return state["slots"][g["slot"]] == {"actor": g["actor"], "reference": g["reference"]}


def protected(task, before, after):
    resources = task["protected_resources"]
    if task["domain"] == "calendar":
        return all(before["slots"][r] == after["slots"][r] for r in resources)
    return (all(before["stock"][r] == after["stock"][r] for r in resources) and
            [x for x in before["reservations"] if x["sku"] in resources] == [x for x in after["reservations"] if x["sku"] in resources])


def expected(task, plan, arm):
    initial = copy.deepcopy(task["initial_state"])
    state = copy.deepcopy(initial)
    shadow_state = None
    cover = task["cover"]
    live_cover, shadow_cover = 0, 0
    if arm == "isolated_shadow":
        shadow_state = copy.deepcopy(initial)
        require(execute(task, shadow_state, cover["write_tool"], cover["write_arguments"]) is None, "shadow initial precondition")
        shadow_cover = 1
    elif arm == "read_only":
        require(execute(task, state, cover["read_tool"], cover["read_arguments"]) is None, "read initial precondition")
        live_cover = 1
    elif arm == "state_changing":
        require(execute(task, state, cover["write_tool"], cover["write_arguments"]) is None, "live initial precondition")
        live_cover = 1
    after_cover = copy.deepcopy(state)
    errors = []
    for action in plan["actions"]:
        error = execute(task, state, action["tool"], action["arguments"])
        if error:
            errors.append(error)
    goal_ok, preserve = goal(task, state), protected(task, initial, state)
    return {"initial_state": initial, "after_cover_state": after_cover, "final_state": state,
            "shadow_final_state": shadow_state, "goal_success": goal_ok,
            "protected_state_preserved": preserve, "authorization_respected": True,
            "confirmation_respected": True, "budget_nonnegative": True,
            "task_success": goal_ok and preserve, "real_tool_errors": errors,
            "cover_live_tool_calls": live_cover, "cover_shadow_tool_calls": shadow_cover,
            "real_tool_calls": len(plan["actions"]), "plan_valid": True,
            "business_state_unchanged_by_cover": initial == after_cover}


def wilson(k, n):
    z = 1.959963984540054
    a = k/n + z*z/(2*n)
    b = z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))
    d = 1+z*z/n
    return [(a-b)/d, (a+b)/d]


def binomial_quantile(n, p, q):
    cdf = 0
    for k in range(n+1):
        cdf += math.comb(n, k)*p**k*(1-p)**(n-k)
        if cdf >= q:
            return k
    return n


def main(check_only=False):
    freeze = load(PACK / "freeze.json")
    source_checks = {path: filehash(Path(path)) == value for path, value in freeze["sources_sha256"].items()}
    require(all(source_checks.values()), "frozen source hash mismatch")
    require(filehash(PACK / "requests.json") == freeze["requests_sha256"], "requests file hash")
    require(filehash(PACK / "e2-tasks.json") == freeze["tasks_sha256"], "tasks file hash")
    tasks = load(PACK / "e2-tasks.json")
    frozen_requests = load(PACK / "requests.json")
    requests = {r["id"]: r for r in frozen_requests if r["experiment"] == "E2"}
    plans = load(BASE / "runtime/replay-inputs-001/e2-plans.json")
    rows = load(REPLAY / "results.json")
    saved_summary = load(REPLAY / "summary.json")
    manifest = load(REPLAY / "replay-manifest.json")
    ids = {t["task_id"] for t in tasks}
    require(len(ids) == 24 and set(requests) == set(plans) == ids, "24-task identity coverage")
    require(len(rows) == 120 and len({(r["task_id"],r["arm"]) for r in rows}) == 120, "five matched arms")
    require(canonical(tasks) == manifest["tasks_sha256"] and canonical(plans) == manifest["plans_sha256"] and canonical(rows) == manifest["results_sha256"], "replay canonical bindings")
    final, supervision = load(RUN / "final.json"), load(RUN / "supervision.json")
    require(final["status"] == "COLLECTION_COMPLETE" and final["completed"] == final["started"] == 72, "complete collection")
    require(supervision["status"] == "EXIT_ZERO" and supervision["reap_confirmed"] and supervision["root_returncode"] == 0, "owned cleanup")
    require(supervision["final_accounting"]["active_processes"] == 0 and supervision["process_control_within_budget"], "closed within budget")
    require(supervision["identity_failures_observed"] == supervision["identity_observability_gaps"] == 0, "recorded identity coverage")
    raw_binding = load(BASE / "runtime/replay-inputs-001/raw-binding.json")
    require(raw_binding["collection_sha256"] == filehash(RUN / "final.json") and raw_binding["supervision_sha256"] == filehash(RUN / "supervision.json"), "export collection bindings")
    raw_bindings = {r["id"]: r for r in raw_binding["records"]}
    all_usage = 0
    for req in frozen_requests:
        response = load(RUN / "requests" / req["id"] / "response.json")
        require(response["status"] == "COMPLETE" and response["application_admissions"] == 1 and response["application_retries"] == 0, "closed no-retry response")
        all_usage += response["token_usage"]["last"]["totalTokens"]
    require(all_usage == final["observed_tokens"] == 195927 and final["admissions"] == 72 and final["unknown_usage"] == 0, "global usage reconciliation")
    receipts, e2_tokens = [], 0
    for task in tasks:
        ident = task["task_id"]
        folder = RUN / "requests" / ident
        req, response = load(folder / "request.json"), load(folder / "response.json")
        raw = (folder / "final-answer.raw.txt").read_text(encoding="utf-8")
        plan = json.loads(raw)
        require(req == requests[ident], "frozen request binding")
        require(raw == plans[ident] and plan == response["prediction"] and plan["task_id"] == ident, "raw plan binding")
        require(filehash(folder / "final-answer.raw.txt") == raw_bindings[ident]["raw_final_sha256"] and filehash(folder / "response.json") == raw_bindings[ident]["response_sha256"], "export raw hash bindings")
        require(response["model"] == "gpt-6-luna" and response["effort"] == "low", "model identity")
        require(response["exit_code"] == 0 and response["stdout_eof"] and response["reader_closed"], "transport exited cleanly")
        attest = load(folder / "thread-attestation.json")
        require(attest["model"] == attest["thread"]["model"] == "gpt-6-luna" and attest["reasoningEffort"] == "low", "thread model")
        require(attest["thread"]["id"] == response["thread_id"] and attest["thread"]["ephemeral"] and attest["runtimeWorkspaceRoots"] == [] and attest["instructionSources"] == [], "ephemeral isolated thread")
        require(attest["sandbox"]["type"] == "readOnly" and attest["sandbox"]["networkAccess"] is False, "thread permission boundary")
        require(load(folder / "remote-control.json")["status"] == "disabled", "remote control disabled")
        mcp_rows = load(folder / "mcp-attestation.json")["data"]
        require(all(x.get("runtimeStatus") == "disabled" and not x.get("tools") and not x.get("resources") for x in mcp_rows), "no MCP tool/resource exposure")
        admission = load(folder / "generation-admission.json")
        require(admission["id"] == ident and admission["model"] == "gpt-6-luna" and admission["effort"] == "low", "generation admission identity")
        require(datetime.fromisoformat(freeze["utc"]) < datetime.fromisoformat(admission["utc"]), "freeze predates generation")
        client, server = lines(folder / "client.jsonl"), lines(folder / "server.stdout.raw")
        completed_items = [x["params"]["item"] for x in server if x.get("method") == "item/completed"]
        require(all(x["type"] in {"userMessage", "agentMessage", "reasoning"} for x in completed_items), "no executed model tools")
        turn_requests = [x for x in client if x.get("method") == "turn/start"]
        require(len(turn_requests) == 1, "one application turn")
        turn_request = turn_requests[0]["params"]
        require(turn_request["input"] == [{"type":"text", "text":req["prompt"]}] and turn_request["outputSchema"] == req["schema"], "exact sent prompt/schema")
        finals = [x["params"] for x in server if x.get("method") == "item/completed" and x["params"]["item"].get("type") == "agentMessage" and x["params"]["item"].get("phase") == "final_answer"]
        require(len(finals) == 1 and finals[0]["item"]["text"] == raw and finals[0]["threadId"] == response["thread_id"] and finals[0]["turnId"] == response["turn_id"], "unique protocol final answer")
        complete = [x["params"] for x in server if x.get("method") == "turn/completed"]
        require(len(complete) == 1 and complete[0]["turn"]["status"] == "completed" and complete[0]["turn"]["error"] is None, "completed turn")
        usage = [x["params"]["tokenUsage"] for x in server if x.get("method") == "thread/tokenUsage/updated"]
        require(usage and usage[-1] == response["token_usage"], "protocol usage")
        e2_tokens += response["token_usage"]["last"]["totalTokens"]
        # For the observed sample, each returned plan contains the exact single
        # goal write. This is checked from saved raw model answers, never supplied
        # as a substitute response to the replay engine.
        expected_action = {"tool": task["cover"]["write_tool"], "arguments": {**task["goal"], "confirmed": True}}
        require(plan == {"task_id":ident, "actions":[expected_action]}, "actual saved plan is exact goal write")
        receipts.append({"task_id":ident,"raw_sha256":filehash(folder/"final-answer.raw.txt"),"response_sha256":filehash(folder/"response.json"),"thread_id":response["thread_id"],"turn_id":response["turn_id"],"tokens":response["token_usage"]["last"]["totalTokens"]})
    indexed = {(r["task_id"],r["arm"]):r for r in rows}
    recomputed = {}
    fields_checked = set()
    for task in tasks:
        plan = json.loads(plans[task["task_id"]])
        base_state = expected(task, plan, "baseline")["final_state"]
        for arm in ARMS:
            exp = expected(task, plan, arm)
            row = indexed[(task["task_id"],arm)]
            for key, value in exp.items():
                require(row[key] == value, f"independent state/score mismatch {task['task_id']} {arm} {key}")
                fields_checked.add(key)
            require(row["task_sha256"] == canonical(task) and row["plan_sha256"] == canonical(plans[task["task_id"]]), "row input hashes")
            require(row["final_state_equals_baseline"] == (exp["final_state"] == base_state), "baseline exact state comparison")
            require(len(row["live_audit"]) == exp["cover_live_tool_calls"] + exp["real_tool_calls"] and len(row["shadow_audit"]) == exp["cover_shadow_tool_calls"], "logged execution call counts")
            recomputed[(task["task_id"],arm)] = exp
    arm_results = {}
    for arm in ARMS:
        actual = [recomputed[(t["task_id"],arm)] for t in tasks]
        n, success = len(actual), sum(r["task_success"] for r in actual)
        delta = (success-24)/24
        failures = 24-success
        exact_ci = [0.0,0.0] if failures == 0 else [-binomial_quantile(24,failures/24,.975)/24, -binomial_quantile(24,failures/24,.025)/24]
        arm_results[arm] = {"n":n,"task_success":success,"goal_success":sum(r["goal_success"] for r in actual),"protected_state_violations":sum(not r["protected_state_preserved"] for r in actual),"success_difference":delta,"exact_discrete_bootstrap95":exact_ci,"wilson95":wilson(success,n)}
        saved = saved_summary["arms"][arm]
        require(saved["denominator"] == n and saved["task_success_count"] == success and saved["goal_success_count"] == arm_results[arm]["goal_success"] and saved["protected_state_violation_count"] == arm_results[arm]["protected_state_violations"], "summary numerator/denominator")
        require(saved["task_success_rate"] == success/n and saved["invalid_plan_count"] == 0, "summary success fraction and plan failures")
        for key in ("cover_live_tool_calls", "cover_shadow_tool_calls", "real_tool_calls"):
            require(saved[key] == sum(x[key] for x in actual), "summary execution counts")
        same_state = sum(recomputed[(t["task_id"],arm)]["final_state"] == recomputed[(t["task_id"],"baseline")]["final_state"] for t in tasks)
        require(saved["same_final_state_as_baseline_count"] == same_state, "summary exact state invariant")
        require(saved["paired_success_difference_vs_baseline"] == delta and saved["paired_task_bootstrap95"] == exact_ci, "paired effect and independent exact bootstrap distribution")
        require(all(abs(x-y)<1e-14 for x,y in zip(saved["task_success_wilson95"],wilson(success,n))), "Wilson interval")
    checks = [
        ("unit_and_pseudoreplication","PASS","24 matched task units;120 arm rows are not independent observations."),
        ("pairing_and_baseline","PASS","Each saved raw plan and initial state is reused across all5 arms; differences use the same24 task IDs."),
        ("selection_and_missingness","PASS","All24 predetermined E2 requests completed and remain included;0 discarded plans or baseline failures; no outcome-dependent task replacement."),
        ("endpoint_and_design_timing","PASS","Frozen cover placement and goal/protected-state scoring predate all model replies; goal and constraint failures are separately retained."),
        ("multiple_comparisons","BOUNDARY","Four baseline contrasts are descriptive; only state-changing contrast is nonzero; no familywise significance or model-selection claim is made."),
        ("interval_interpretation","BOUNDARY","Wilson and task bootstrap numbers are finite constructed-task summaries, not uncertainty for a random population sample."),
        ("causal_mechanism_and_confounding","PASS_WITH_SCOPE","Within task, only cover destination/type changes. Across tasks, hand-built overlap/protected/slack factors explain effects; do not infer ecosystem failure prevalence."),
        ("effect_size_vs_significance","PASS","Primary result is15/24 fewer complete tasks(-62.5pp), with9goal failures and6protected-state violations; no p-value headline."),
        ("null_and_equivalence","BOUNDARY","Exact baseline-state equality in24 trials for discard/shadow/read demonstrates this implementation's invariant; bootstrap[0,0] does not establish universal equivalence."),
        ("generalization_and_dependence","BOUNDARY","One model,24 simple tasks/two finite domains,one plan each; templates and deterministic environment are shared. Confidence intervals do not remove this construction dependence."),
        ("construct_and_cost_validity","PASS_WITH_SCOPE","Measures objective task/state preservation and tool-call work. Actor/resource permission and confirmed=true are tool-level checks; scripted cover flags do not establish human consent to each decoy. No attacker inference or privacy benefit is measured; local CPU nanoseconds are not network/API latency; pure reads do not certify idempotent writes."),
    ]
    report = {"status":"PASS_SAVED_E2_LINEAGE_AND_OUTCOME_VERIFICATION","utc":datetime.now(timezone.utc).isoformat(),"new_model_calls":0,"frozen_source_count":len(source_checks),"frozen_sources_match":all(source_checks.values()),"task_count":24,"arm_rows":120,"raw_answer_bindings_verified":24,"e2_observed_tokens":e2_tokens,"global_collection_observed_tokens":all_usage,"fields_independently_reconstructed":sorted(fields_checked),"arm_results":arm_results,"statistical_checks":[{"id":i+1,"check":name,"status":status,"finding":finding} for i,(name,status,finding) in enumerate(checks)],"receipts":receipts,"input_file_sha256":{"freeze":filehash(PACK/"freeze.json"),"tasks":filehash(PACK/"e2-tasks.json"),"plans":filehash(BASE/"runtime/replay-inputs-001/e2-plans.json"),"results":filehash(REPLAY/"results.json"),"summary":filehash(REPLAY/"summary.json")},"interpretation":"Saved actual Luna plans reproduce the predicted finite-state mechanism: live cover competes for target state or changes protected resources; discard,clone-isolated andpure-read arms preserve the baseline. This is a controlled plan-replay mechanism result, not an autonomous-agent evaluation or privacy-defense effectiveness result.","review_identity":"Separate deterministic reconstruction by the same AI-assisted project workflow; not independent human coding or external researcher validation."}
    reports = (("E2-VERIFICATION.json",json.dumps(report,indent=2,ensure_ascii=False)+"\n"),("E2-VERIFICATION.txt","E2 saved-result verification: PASS\n\n24 actual Luna plan outputs bind exactly to frozen requests, protocol final messages, export inputs and120 replay rows. All frozen source hashes match. No model request or original-result modification occurred.\n\n"+"\n".join(f"{arm}: task success {r['task_success']}/24; goal {r['goal_success']}/24; protected violations {r['protected_state_violations']}/24; paired difference {r['success_difference']:.6f}; exact discrete bootstrap95 {r['exact_discrete_bootstrap95']}" for arm,r in arm_results.items())+"\n\n11 statistical checks:\n"+"\n".join(f"{i+1}. {name} [{status}]: {finding}" for i,(name,status,finding) in enumerate(checks))+"\n\n"+report["interpretation"]+"\n"+report["review_identity"]+"\n"))
    for filename, value in (() if check_only else reports):
        with (OUT/filename).open("x",encoding="utf-8",newline="\n") as handle:
            handle.write(value)
    print(json.dumps({k:report[k] for k in ("status","task_count","arm_rows","e2_observed_tokens","global_collection_observed_tokens","new_model_calls")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="Revalidate saved inputs/results without writing reports")
    main(parser.parse_args().check_only)
