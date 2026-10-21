"""Model backends for the autonomous-agent experiment (E8).

Backends
  scripted        : replays the task's reference program, then reports its outputs
                    (pipeline check; reproduces the E6/E7 setting with online cover)
  noisy-scripted  : scripted agent that inserts plausible extra read calls
                    (synthetic planner variance; NOT an LLM result)
  openai          : any OpenAI-compatible /chat/completions endpoint with tools
  anthropic       : Anthropic /v1/messages with tools

LLM backends use only urllib. Every request/response pair is cached under
<out>/llm_cache/ keyed by the SHA-256 of the request body, so a finished run can
be re-executed offline (--cache-only) and audited. Keys are read from the
environment (OPENAI_API_KEY / ANTHROPIC_API_KEY) and never written to disk.
"""
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from pathlib import Path


class Budget:
    def __init__(self, max_tokens):
        self.max_tokens = max_tokens
        self.used = 0

    def charge(self, n):
        self.used += n
        if self.max_tokens and self.used > self.max_tokens:
            raise BudgetExceeded(self.used)


class BudgetExceeded(RuntimeError):
    pass


class Cache:
    def __init__(self, root: Path, cache_only: bool):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.cache_only = cache_only

    def get_or_call(self, body: dict, call):
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        p = self.root / f"{key}.json"
        if p.exists():
            return json.loads(p.read_text())
        if self.cache_only:
            raise RuntimeError(f"cache miss in --cache-only mode: {key}")
        resp = call()
        p.write_text(json.dumps({"request": body, "response": resp}))
        return {"request": body, "response": resp}


def _post(url, headers, body, retries=5):
    data = json.dumps(body).encode()
    for k in range(retries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and k < retries - 1:
                time.sleep(2 ** (k + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
        except urllib.error.URLError:
            if k < retries - 1:
                time.sleep(2 ** (k + 1))
                continue
            raise


# ---------------------------------------------------------------- chat models
class OpenAIChat:
    """messages use the OpenAI chat format internally for every backend."""

    def __init__(self, model, cache, budget, temperature=0.0):
        self.model, self.cache, self.budget, self.t = model, cache, budget, temperature
        self.url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions"

    def complete(self, messages, tools=None):
        body = {"model": self.model, "messages": messages, "temperature": self.t}
        if tools:
            body["tools"] = tools
        key = os.environ.get("OPENAI_API_KEY")
        out = self.cache.get_or_call(body, lambda: _post(self.url, {"Authorization": f"Bearer {key}"}, body))
        r = out["response"]
        self.budget.charge(r.get("usage", {}).get("total_tokens", 0))
        m = r["choices"][0]["message"]
        calls = [{"id": c["id"], "name": c["function"]["name"],
                  "arguments": json.loads(c["function"]["arguments"] or "{}")} for c in (m.get("tool_calls") or [])]
        return {"content": m.get("content") or "", "tool_calls": calls, "raw": m}


class AnthropicChat:
    def __init__(self, model, cache, budget, temperature=0.0):
        self.model, self.cache, self.budget, self.t = model, cache, budget, temperature
        self.url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"

    @staticmethod
    def _convert(messages):
        system, out = "", []
        for m in messages:
            if m["role"] == "system":
                system += m["content"]
            elif m["role"] == "tool":
                out.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}]})
            elif m["role"] == "assistant" and m.get("tool_calls"):
                blocks = ([{"type": "text", "text": m["content"]}] if m.get("content") else [])
                blocks += [{"type": "tool_use", "id": c["id"], "name": c["function"]["name"],
                            "input": json.loads(c["function"]["arguments"])} for c in m["tool_calls"]]
                out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": m["role"], "content": m["content"]})
        merged = []
        for m in out:  # the API requires alternating roles
            if merged and merged[-1]["role"] == m["role"]:
                a = merged[-1]["content"]; b = m["content"]
                a = a if isinstance(a, list) else [{"type": "text", "text": a}]
                b = b if isinstance(b, list) else [{"type": "text", "text": b}]
                merged[-1]["content"] = a + b
            else:
                merged.append(m)
        return system, merged

    def complete(self, messages, tools=None):
        system, msgs = self._convert(messages)
        body = {"model": self.model, "max_tokens": 1024, "temperature": self.t, "system": system, "messages": msgs}
        if tools:
            body["tools"] = [{"name": t["function"]["name"], "description": t["function"].get("description", ""),
                              "input_schema": t["function"]["parameters"]} for t in tools]
        hdr = {"x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""), "anthropic-version": "2023-06-01"}
        out = self.cache.get_or_call(body, lambda: _post(self.url, hdr, body))
        r = out["response"]
        u = r.get("usage", {})
        self.budget.charge(u.get("input_tokens", 0) + u.get("output_tokens", 0))
        text = "".join(b["text"] for b in r["content"] if b["type"] == "text")
        calls = [{"id": b["id"], "name": b["name"], "arguments": b["input"]} for b in r["content"] if b["type"] == "tool_use"]
        raw = {"role": "assistant", "content": text}
        if calls:
            raw["tool_calls"] = [{"id": c["id"], "type": "function",
                                  "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}} for c in calls]
        return {"content": text, "tool_calls": calls, "raw": raw}


def chat_backend(kind, model, cache, budget, temperature):
    if kind == "openai":
        if not os.environ.get("OPENAI_API_KEY") and not cache.cache_only:
            raise SystemExit("OPENAI_API_KEY is not set")
        return OpenAIChat(model, cache, budget, temperature)
    if kind == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY") and not cache.cache_only:
            raise SystemExit("ANTHROPIC_API_KEY is not set")
        return AnthropicChat(model, cache, budget, temperature)
    raise ValueError(kind)


# ---------------------------------------------------------------- scripted stand-ins
class ScriptedAgent:
    """Emits the reference program as tool calls, then one response containing the
    task outputs. With p_extra > 0 it inserts read calls on the user's own objects
    before reference calls (synthetic planner variance)."""

    def __init__(self, task, base, rng: random.Random, p_extra=0.0):
        self.plan, self.i, self.done = [], 0, False
        orders = [o for o, v in base["orders"].items() if v["user_id"] == task.user_id]
        items = sorted({it["product_id"] for o in orders for it in base["orders"][o]["items"]})
        for a in task.actions:
            while p_extra and rng.random() < p_extra:
                kind = rng.choice(["user", "order", "product"])
                if kind == "user":
                    self.plan.append(("get_user_details", {"user_id": task.user_id}))
                elif kind == "order" and orders:
                    self.plan.append(("get_order_details", {"order_id": rng.choice(orders)}))
                elif items:
                    self.plan.append(("get_product_details", {"product_id": rng.choice(items)}))
            self.plan.append((a.name, dict(a.kwargs)))
        self.outputs = list(task.outputs)

    def complete(self, messages, tools=None):
        if self.i < len(self.plan):
            name, kw = self.plan[self.i]; self.i += 1
            cid = f"call_{self.i}"
            raw = {"role": "assistant", "content": "", "tool_calls": [
                {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(kw)}}]}
            return {"content": "", "tool_calls": [{"id": cid, "name": name, "arguments": kw}], "raw": raw}
        text = "Done. " + " ".join(self.outputs)
        return {"content": text, "tool_calls": [], "raw": {"role": "assistant", "content": text}}


class ScriptedUser:
    def __init__(self, instruction):
        self.first = instruction

    def complete(self, messages, tools=None):
        n_user_turns = sum(m["role"] == "assistant" for m in messages)
        text = self.first if n_user_turns == 0 else "###STOP###"
        return {"content": text, "tool_calls": [], "raw": {"role": "assistant", "content": text}}
