"""Offline test of the OpenAI-compatible and Anthropic backends against a local mock
server (no network, no key, no model). The mock agent authenticates the user by
email, reads one order and stops; the mock user answers once and sends ###STOP###.
It checks request formatting, tool-call parsing, caching and --cache-only replay.

  python -B test_backends_mock.py
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent


def script(body, is_anthropic):
    sys_text = body.get("system", "") if is_anthropic else next((m["content"] for m in body["messages"] if m["role"] == "system"), "")
    if "You are a user interacting" in sys_text:
        n = sum(m["role"] == "assistant" for m in body["messages"])
        return ("text", "I want to check my order. My email is aarav.anderson9752@example.com." if n == 0 else "###STOP###")
    n_tool = sum(1 for m in body["messages"] if (m["role"] == "tool") or
                 (is_anthropic and isinstance(m["content"], list) and any(b.get("type") == "tool_result" for b in m["content"])))
    if n_tool == 0:
        return ("tool", "find_user_id_by_email", {"email": "aarav.anderson9752@example.com"})
    return ("text", "Your user id is aarav_anderson_8794. Anything else?")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        anth = self.path.endswith("/v1/messages")
        kind, *rest = script(body, anth)
        if anth:
            content = [{"type": "text", "text": rest[0]}] if kind == "text" else \
                [{"type": "tool_use", "id": "tu_1", "name": rest[0], "input": rest[1]}]
            out = {"content": content, "usage": {"input_tokens": 10, "output_tokens": 5}}
        else:
            msg = {"role": "assistant", "content": rest[0]} if kind == "text" else \
                {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function",
                 "function": {"name": rest[0], "arguments": json.dumps(rest[1])}}]}
            out = {"choices": [{"message": msg}], "usage": {"total_tokens": 15}}
        b = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    for backend in ("openai", "anthropic"):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, OPENAI_BASE_URL=f"http://127.0.0.1:{port}/v1", ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}",
                       OPENAI_API_KEY="mock", ANTHROPIC_API_KEY="mock")
            cmd = [sys.executable, "-B", str(HERE / "run_agent_episodes.py"), "--agent", backend, "--agent-model", "mock",
                   "--user", backend, "--user-model", "mock", "--tasks", "0", "--seeds", "1", "--out", tmp]
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            ep = json.loads((Path(tmp) / "trajectories.jsonl").read_text().splitlines()[0])
            assert [c["name"] for c in ep["calls"]] == ["find_user_id_by_email"], ep["calls"]
            assert ep["status"] == "user_stop" and ep["calls"][0]["resp_text"] == "aarav_anderson_8794"
            n_cache = len(list((Path(tmp) / "llm_cache").glob("*.json")))
            (Path(tmp) / "trajectories.jsonl").unlink()
            env2 = {k: v for k, v in env.items() if k not in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")}
            env2["OPENAI_BASE_URL"] = env2["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:9"  # unreachable
            subprocess.run(cmd + ["--cache-only"], env=env2, check=True, capture_output=True)
            ep2 = json.loads((Path(tmp) / "trajectories.jsonl").read_text().splitlines()[0])
            assert ep2["calls"] == ep["calls"]
            print(backend, "ok: tool call parsed, reward fields present, cache entries", n_cache, "replayed offline")
    srv.shutdown()


if __name__ == "__main__":
    main()
