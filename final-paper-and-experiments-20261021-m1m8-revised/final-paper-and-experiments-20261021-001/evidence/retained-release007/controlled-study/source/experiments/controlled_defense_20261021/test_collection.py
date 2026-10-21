"""No-model collection contract and failure-retention tests."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import cover
import luna_client as lc
import padding
import run_study as controller


class FakeClient:
    def __init__(self, raw='{"text":"saved output"}', usage=True, close_failure=False):
        self.raw = raw
        self.guard = lc.prior.WorkflowGuard()
        self.guard.finished = False
        self.guard.usage = ({"last": {"totalTokens": 13, "inputTokens": 10, "outputTokens": 3}} if usage else None)
        self.guard.messages = [raw]
        self.guard.completed_text_and_usage = self.completed
        self.process = type("Process", (), {"returncode": 0})()
        self.reader = type("Reader", (), {"is_alive": lambda self: False})()
        self.saw_stdout_eof = True
        self.calls = []
        self.close_failure = close_failure

    def completed(self):
        if self.guard.usage is None:
            raise ValueError("usage_missing_not_zero")
        return self.raw, self.guard.usage

    def request(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        self.guard.turn_id = "fake-turn"
        return {"turn": {"id": "fake-turn"}}

    def next(self):
        self.guard.finished = True

    def close(self, clean):
        if self.close_failure:
            raise ValueError("synthetic_close_failure")


class CollectionTests(unittest.TestCase):
    def test_prepared_model_field_contract_and_topic_split(self):
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp) / "pack"
            controller.prepare(pack)
            requests = json.loads((pack / "requests.json").read_text())
            metadata = json.loads((pack / "e1-metadata.json").read_text())
            tasks = json.loads((pack / "e2-tasks.json").read_text())
            self.assertEqual(72, len(requests))
            self.assertEqual(72, len({row["id"] for row in requests}))
            self.assertEqual(24, len(tasks))
            self.assertEqual(48, len(metadata))
            adapted = [{**row, "text": "saved", "status": "ok"} for row in metadata]
            padding.validate_records(adapted)
            by_id = {row["id"]: row for row in requests}
            for task in tasks:
                expected = cover.model_request(task)
                actual = by_id[task["task_id"]]
                self.assertEqual(expected["prompt"], actual["prompt"])
                self.assertEqual(expected["response_schema"], actual["schema"])
                public = json.loads(actual["prompt"].split("\n", 1)[1].split("\nOutput schema:", 1)[0])
                self.assertEqual({"task_id", "task", "initial_state", "policy", "tools"}, set(public))
                self.assertNotIn("cover", public)
                self.assertNotIn("goal", public)
                self.assertNotIn("condition", public)
            controller.verify(pack)

    def invoke_fake(self, client):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(lc, "startup", return_value=(client, "fake-thread")):
                response = lc.one_request({"id": "fixture", "prompt": "synthetic only", "schema": controller.TEXT_SCHEMA},
                                          Path(temp) / "request", time.monotonic() + 300)
            retained = json.loads((Path(temp) / "request" / "response.json").read_text())
            self.assertEqual(response, retained)
        return response

    def test_complete_response_one_admission_no_tools(self):
        client = FakeClient()
        response = self.invoke_fake(client)
        self.assertEqual("COMPLETE", response["status"])
        self.assertEqual(1, response["application_admissions"])
        self.assertEqual(0, response["application_retries"])
        self.assertEqual(["turn/start"], [method for method, _ in client.calls])
        params = client.calls[0][1]
        self.assertEqual([], params["environments"])
        self.assertEqual([], params["runtimeWorkspaceRoots"])
        self.assertEqual("gpt-6-luna", params["model"])

    def test_bad_json_is_retained_content_failure_after_clean_transport(self):
        response = self.invoke_fake(FakeClient(raw="not-json"))
        self.assertEqual("CONTENT_FAILURE", response["status"])
        self.assertEqual(1, response["application_admissions"])
        self.assertIsNone(response["prediction"])

    def test_unknown_usage_and_exit_failure_stop_instead_of_content_recovery(self):
        for client in (FakeClient(usage=False), FakeClient(close_failure=True)):
            response = self.invoke_fake(client)
            self.assertEqual("HOLD", response["status"])
            self.assertEqual(1, response["application_admissions"])
            self.assertIsNone(response["prediction"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
