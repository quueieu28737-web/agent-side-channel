import copy
import unittest

from cover import ARMS, ToolEnvironment, generate_tasks, model_request, oracle_plan, replay_one, replay_tasks, summary


class CoverTests(unittest.TestCase):
    def setUp(self):
        self.tasks = generate_tasks()

    def test_task_count_conditions_and_initial_cover_validity(self):
        self.assertEqual(len(self.tasks), 24)
        self.assertEqual(len({t["task_id"] for t in self.tasks}), 24)
        for task in self.tasks:
            env = ToolEnvironment(task)
            self.assertTrue(env.call(task["cover"]["write_tool"], task["cover"]["write_arguments"])["ok"])
            self.assertTrue(replay_one(task, oracle_plan(task), "baseline")["task_success"])

    def test_structured_output_schema_closes_every_object(self):
        def check(node):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertFalse(node["additionalProperties"])
                    self.assertEqual(set(node["required"]), set(node["properties"]))
                for child in node.values():
                    check(child)
            elif isinstance(node, list):
                for child in node:
                    check(child)
        for task in self.tasks:
            schema = model_request(task)["response_schema"]
            check(schema)
            self.assertEqual(schema["properties"]["task_id"]["enum"], [task["task_id"]])
            variants = schema["properties"]["actions"]["items"]["anyOf"]
            self.assertEqual(len(variants), 2)
            for variant in variants:
                self.assertEqual(len(variant["properties"]["tool"]["enum"]), 1)
                self.assertIn("actor", variant["properties"]["arguments"]["properties"])

    def test_discard_never_executes_and_read_log_is_outside_state(self):
        for task in self.tasks:
            plan = oracle_plan(task)
            baseline = replay_one(task, plan, "baseline")
            discarded = replay_one(task, plan, "discarded")
            read = replay_one(task, plan, "read_only")
            self.assertEqual(discarded["cover_live_tool_calls"], 0)
            self.assertEqual(discarded["cover_shadow_tool_calls"], 0)
            self.assertEqual(len(discarded["live_audit"]), len(baseline["live_audit"]))
            self.assertEqual(discarded["final_state"], baseline["final_state"])
            self.assertEqual(read["after_cover_state"], task["initial_state"])
            self.assertEqual(read["final_state"], baseline["final_state"])
            self.assertEqual(len(read["live_audit"]), len(baseline["live_audit"])+1)
            self.assertNotIn("audit", read["final_state"])

    def test_shadow_isolation_and_cost(self):
        for task in self.tasks:
            row = replay_one(task, oracle_plan(task), "isolated_shadow")
            self.assertEqual(row["after_cover_state"], task["initial_state"])
            self.assertNotEqual(row["shadow_final_state"], task["initial_state"])
            self.assertEqual(row["cover_live_tool_calls"], 0)
            self.assertEqual(row["cover_shadow_tool_calls"], 1)
            self.assertTrue(row["task_success"])

    def test_auth_confirmation_and_atomic_errors(self):
        task = self.tasks[0]
        for change, expected in (({"actor": "wrong"}, "unauthorized"), ({"confirmed": False}, "confirmation_required"), ({"quantity": 1000}, "insufficient_stock"), ({"quantity": True}, "invalid_arguments")):
            env = ToolEnvironment(task)
            args = {**task["cover"]["write_arguments"], **change}
            self.assertEqual(env.call(task["cover"]["write_tool"], args)["error"], expected)
            self.assertEqual(env.state, task["initial_state"])
        env = ToolEnvironment(task)
        env.state["budget"][task["policy"]["actor"]] = 0
        before = copy.deepcopy(env.state)
        self.assertEqual(env.call(task["cover"]["write_tool"], task["cover"]["write_arguments"])["error"], "insufficient_budget")
        self.assertEqual(env.state, before)

    def test_reads_repeated_are_idempotent_writes_are_not_assumed_so(self):
        task = self.tasks[2]  # overlap/slack
        env = ToolEnvironment(task)
        for _ in range(3):
            self.assertTrue(env.call(task["cover"]["read_tool"], task["cover"]["read_arguments"])["ok"])
        self.assertEqual(env.state, task["initial_state"])
        self.assertTrue(env.call(task["cover"]["write_tool"], task["cover"]["write_arguments"])["ok"])
        first = copy.deepcopy(env.state)
        self.assertTrue(env.call(task["cover"]["write_tool"], task["cover"]["write_arguments"])["ok"])
        self.assertNotEqual(first, env.state)

    def test_state_changing_conditions_can_succeed_or_fail(self):
        rows = [replay_one(task, oracle_plan(task), "state_changing") for task in self.tasks]
        self.assertEqual(sum(r["task_success"] for r in rows), 9)  # 6 inventory + 3 calendar
        self.assertEqual(sum(not r["protected_state_preserved"] for r in rows), 6)
        self.assertTrue(all(not r["business_state_unchanged_by_cover"] for r in rows))
        # Calendar collision must not overwrite the cover or satisfy the real reference.
        collision = next(r for r in rows if r["domain"] == "calendar" and r["condition"]["cover_resource_relation"] == "overlap")
        self.assertFalse(collision["goal_success"])
        self.assertEqual(collision["real_tool_errors"], ["occupied"])

    def test_invalid_model_plan_retained_in_all_arms(self):
        task = self.tasks[0]
        for raw in ("not json", {"task_id": task["task_id"], "actions": []}, {"task_id": "wrong", "actions": []}):
            for arm in ARMS:
                row = replay_one(task, raw, arm)
                self.assertFalse(row["plan_valid"])
                self.assertFalse(row["task_success"])
                self.assertEqual(row["real_tool_calls"], 0)
        row = replay_one(task, {"task_id": task["task_id"], "actions": [{"tool": "inventory.reserve", "arguments": {}}]}, "baseline")
        self.assertTrue(row["plan_valid"])
        self.assertFalse(row["task_success"])
        self.assertEqual(row["real_tool_errors"], ["invalid_arguments"])

    def test_paired_summary_all_tasks_and_no_arm_pseudoreplication(self):
        plans = {t["task_id"]: oracle_plan(t) for t in self.tasks}
        # One failed model plan remains in the denominator.
        plans[self.tasks[-1]["task_id"]] = "invalid"
        rows = replay_tasks(self.tasks, plans)
        out = summary(rows)
        self.assertEqual(out["tasks"], 24)
        self.assertEqual(out["arm_rows"], 120)
        self.assertTrue(all(x["denominator"] == 24 for x in out["arms"].values()))
        self.assertEqual(out["arms"]["baseline"]["task_success_count"], 23)
        self.assertEqual(out["arms"]["read_only"]["paired_success_difference_vs_baseline"], 0)
        self.assertEqual(out["arms"]["read_only"]["same_final_state_as_baseline_count"], 24)
        with self.assertRaises(ValueError):
            replay_tasks(self.tasks, {t["task_id"]: oracle_plan(t) for t in self.tasks[:-1]})


if __name__ == "__main__":
    unittest.main()
