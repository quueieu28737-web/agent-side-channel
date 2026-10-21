"""E8 step 1: collect autonomous-agent trajectories on the 115 retail tasks.

Because sandboxed (shadow) cover never reaches the agent and transport framing
does not change message content, the agent's trajectory is independent of the
defense. One trajectory per (task, seed) therefore serves every cover policy and
framing in step 2 (apply_cover.py), which cuts model cost by 8x relative to
running each policy separately. Live cover is excluded for this reason: it would
change the agent's observations and must be run per policy.

Examples
  python -B run_agent_episodes.py --agent scripted --user scripted --out runs/scripted
  python -B run_agent_episodes.py --agent noisy-scripted --user scripted --out runs/noisy
  OPENAI_API_KEY=... python -B run_agent_episodes.py --agent openai --agent-model gpt-4o \
      --user openai --user-model gpt-4o --seeds 3 --max-tokens 30000000 --out runs/gpt-4o
  python -B run_agent_episodes.py ... --cache-only     # offline re-execution from llm_cache/

Seeds index repeated episodes; with temperature 0 an API may still be
non-deterministic, which is why each response is cached.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[1] / "reviewer-audit"))
import retail_replay as old  # noqa: E402
from episode import run_episode  # noqa: E402
import llm  # noqa: E402

SEEDS = [20261021, 20261022, 20261023]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="scripted", choices=["scripted", "noisy-scripted", "openai", "anthropic"])
    ap.add_argument("--agent-model", default="")
    ap.add_argument("--user", default="scripted", choices=["scripted", "openai", "anthropic"])
    ap.add_argument("--user-model", default="")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--tasks", default="all", help="'all' or comma-separated task indices")
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--max-tokens", type=int, default=0, help="stop when total tokens exceed this (0 = no limit)")
    ap.add_argument("--p-extra", type=float, default=0.3, help="noisy-scripted: extra read probability")
    ap.add_argument("--cache-only", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ns, tools, base, tasks = old.load_tau()
    wiki = (HERE.parents[1] / "tau-cover-bridge/vendor/tau_bench__envs__retail__wiki.md").read_text()
    expected = []
    for t in tasks:
        env = old.make_env(ns, tools, base, t)
        for act in t.actions:
            env.step(act)
        expected.append(env.data)
    ids = range(len(tasks)) if a.tasks == "all" else [int(x) for x in a.tasks.split(",")]
    cache = llm.Cache(out / "llm_cache", a.cache_only)
    budget = llm.Budget(a.max_tokens)
    traj_p = out / "trajectories.jsonl"
    done = set()
    if traj_p.exists():  # resumable
        for line in traj_p.read_text().splitlines():
            r = json.loads(line); done.add((r["task"], r["seed"]))
    meta = {"agent": a.agent, "agent_model": a.agent_model, "user": a.user, "user_model": a.user_model,
            "temperature": a.temperature, "max_steps": a.max_steps, "p_extra": a.p_extra if a.agent == "noisy-scripted" else None,
            "seeds": SEEDS[:a.seeds], "tasks": list(ids), "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (out / "run_meta.json").write_text(json.dumps(meta, indent=1))
    with traj_p.open("a") as f:
        for seed in SEEDS[:a.seeds]:
            for tid in ids:
                if (tid, seed) in done:
                    continue
                task = tasks[tid]
                rng = random.Random(seed * 7919 + tid)
                if a.agent in ("scripted", "noisy-scripted"):
                    agent = llm.ScriptedAgent(task, base, rng, a.p_extra if a.agent == "noisy-scripted" else 0.0)
                else:
                    agent = llm.chat_backend(a.agent, a.agent_model, cache, budget, a.temperature)
                user_llm = llm.ScriptedUser(task.instruction) if a.user == "scripted" else \
                    llm.chat_backend(a.user, a.user_model, cache, budget, a.temperature)
                try:
                    ep = run_episode(ns, tools, base, task, expected[tid], agent, user_llm, wiki, a.max_steps)
                except llm.BudgetExceeded as e:
                    print(f"token budget exhausted after {e} tokens; rerun to resume", flush=True)
                    return
                ref = [x.name for x in task.actions]
                ep.update({"task": tid, "seed": seed, "user": task.user_id,
                           "has_cancel": int("cancel_pending_order" in ref),
                           "has_return": int("return_delivered_order_items" in ref)})
                f.write(json.dumps(ep) + "\n"); f.flush()
            print("seed", seed, "done; tokens used", budget.used, flush=True)


if __name__ == "__main__":
    main()
