"""E6/E7: randomized cover on stateful retail tools, policy-aware attackers, and the
joint agent-tool TLS link.

Sessions replay the 115 pinned tau-bench retail reference programs (no LLM
planner). Cover calls are actions sampled from *other* tasks' reference
programs (a population of plausible programs, as in decoy-query defenses) and
are inserted at uniformly random positions. 'shadow' cover executes against a
per-session sandbox copy of the initial database and is invisible to the live
state; 'live' cover executes on the live database.

Views
  dispatch: ordered tool names and response byte lengths (E6; as in Sec. 8.3)
  network : direction-tagged TLS 1.2 application-record lengths on the
            agent-tool link, under a transport framing policy (E7)

This script only generates sessions and socket captures; e67_eval.py computes
all attacker, utility and cost results from the saved files. Cover parameters
were fixed before execution; no parameter is tuned on outcome data.
"""
import copy
import json
import random
import tempfile
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "reviewer-audit"))
import retail_replay as old  # noqa: E402
import tlslab  # noqa: E402

SEEDS = [20261021, 20261022, 20261023]
WRITES = {"cancel_pending_order", "modify_pending_order_address", "modify_pending_order_items",
          "modify_pending_order_payment", "modify_user_address", "return_delivered_order_items",
          "exchange_delivered_order_items"}
COVERS = ["none", "cancel_p50_shadow", "cancel_p100_shadow", "cancel_p100_live",
          "cancel_const2_shadow", "decoy1_shadow", "decoy2_shadow", "shape_eq_shadow"]
NET_COVERS = ["none", "cancel_const2_shadow", "decoy1_shadow", "shape_eq_shadow"]
FRAMINGS = ["raw", "bucket1024", "const"]


def load():
    ns, tools, base, tasks = old.load_tau()
    progs = []
    for t in tasks:
        acts = [(a.name, dict(a.kwargs)) for a in t.actions]
        env = old.make_env(ns, tools, base, t)
        for a in t.actions:
            env.step(a)
        progs.append({"user": t.user_id, "actions": acts, "expected": env.data})
    return ns, tools, base, tasks, progs


def invoke(tools, data, name, kw):
    try:
        return tools[name].invoke(data=data, **kw)
    except Exception as e:  # mirrors Env.step
        return f"Error: {e}"


def template(progs):
    """Fixed per-verb count vector for shape equalization: the maximum count of each
    verb over the public reference-program population (label-free)."""
    c = defaultdict(int)
    for p in progs:
        for v, k in Counter(n for n, _ in p["actions"]).items():
            c[v] = max(c[v], k)
    return dict(c)


def plan_cover(cover, tid, progs, rng, tmpl, cancel_pool):
    me = progs[tid]
    others = [j for j, p in enumerate(progs) if j != tid and p["user"] != me["user"]]
    real_cancels = sum(n == "cancel_pending_order" for n, _ in me["actions"])
    pool = [c for c in cancel_pool if progs[c[0]]["user"] != me["user"]]
    if cover == "none":
        return []
    if cover.startswith("cancel_p"):
        p = 0.5 if "p50" in cover else 1.0
        return [rng.choice(pool)[1]] if rng.random() < p else []
    if cover == "cancel_const2_shadow":
        return [rng.choice(pool)[1] for _ in range(max(0, 2 - real_cancels))]
    if cover.startswith("decoy"):
        k = int(cover[5])
        out = []
        for j in rng.sample(others, k):
            out.append(list(progs[j]["actions"]))
        return out  # list of programs (internal order kept)
    if cover == "shape_eq_shadow":
        have = Counter(n for n, _ in me["actions"])
        by_verb = defaultdict(list)
        for j in others:
            for n, kw in progs[j]["actions"]:
                by_verb[n].append((n, kw))
        out = []
        for v, c in sorted(tmpl.items()):
            out += [rng.choice(by_verb[v]) for _ in range(max(0, c - have[v]))]
        rng.shuffle(out)
        return out
    raise ValueError(cover)


def interleave(real, cover_progs, rng):
    """Uniform random merge preserving the internal order of each program."""
    seqs = [[("real", a) for a in real]] + [[("cover", a) for a in p] for p in cover_progs]
    slots = [i for i, s in enumerate(seqs) for _ in s]
    rng.shuffle(slots)
    it = [iter(s) for s in seqs]
    return [next(it[i]) for i in slots]


def run_session(ns, tools, base, task, prog, cover, plan, rng):
    live = old.fast_clone(base)
    shadow = old.fast_clone(base)
    cover_progs = plan if cover.startswith("decoy") else [[a] for a in plan]
    calls = []
    for kind, (name, kw) in interleave(prog["actions"], cover_progs, rng):
        target = live if (kind == "real" or cover.endswith("_live")) else shadow
        resp = invoke(tools, target, name, kw)
        req = json.dumps({"name": name, "arguments": kw}, sort_keys=True)
        calls.append({"name": name, "kind": kind, "req": len(req.encode()), "resp": len(resp.encode()),
                      "err": resp.startswith("Error:"), "req_text": req, "resp_text": resp})
    exp = prog["expected"]
    db_eq = live["orders"] == exp["orders"] and live["users"] == exp["users"]
    acct = all(live["orders"].get(o) == exp["orders"].get(o) for o in base["orders"]
               if base["orders"][o]["user_id"] == task.user_id) and live["users"].get(task.user_id) == exp["users"].get(task.user_id)
    return calls, db_eq, acct


def frame(text, framing, req, size_caps):
    b = text.encode()
    if framing == "raw":
        return b
    if framing == "bucket1024":
        n = len(b) + 4
        return b + b" " * (int(np.ceil(n / 1024)) * 1024 - n)
    cap = size_caps["req" if req else "resp"]
    n = len(b) + 4
    tgt = cap if n <= cap else int(np.ceil(n / 1024)) * 1024
    return b + b" " * (tgt - n)


def main():
    ns, tools, base, tasks, progs = load()
    VERBS = sorted({n for p in progs for n, _ in p["actions"]})
    tmpl = template(progs)
    cancel_pool = [(j, a) for j, p in enumerate(progs) for a in p["actions"] if a[0] == "cancel_pending_order"]
    sessions = {}
    for cover in COVERS:
        for tid, (task, prog) in enumerate(zip(tasks, progs)):
            for seed in SEEDS:
                rng = random.Random(seed * 1000003 + tid * 7919 + COVERS.index(cover))
                plan = plan_cover(cover, tid, progs, rng, tmpl, cancel_pool)
                calls, db_eq, acct = run_session(ns, tools, base, task, prog, cover, plan, rng)
                sessions[(cover, tid, seed)] = {"calls": calls, "db_eq": db_eq, "acct": acct}
        print("sessions", cover, flush=True)

    # ---------------- E7: network view on the agent-tool TLS link
    srv, cli = tlslab.make_contexts(Path(tempfile.gettempdir()) / "sp2027-r2-cert", "1.2")
    ref = [c for (cv, _t, _s), s in sessions.items() if cv == "none" for c in s["calls"]]
    caps = {"req": int(np.ceil((max(c["req"] for c in ref) + 4) / 256) * 256),
            "resp": int(np.ceil((np.quantile([c["resp"] for c in ref], 0.95) + 4) / 1024) * 1024)}
    net = {}
    for cover in NET_COVERS:
        for framing in FRAMINGS:
            for (cv, tid, seed), s in sessions.items():
                if cv != cover:
                    continue
                ex = [(frame(c["req_text"], framing, True, caps), frame(c["resp_text"], framing, False, caps)) for c in s["calls"]]
                seq = tlslab.run_session(srv, cli, ex)
                assert sum(d == "c2s" for d, _ in seq) == len(ex)
                net[(cover, framing, tid, seed)] = seq
            print("E7 captured", cover, framing, flush=True)
    (HERE / "e7_meta.json").write_text(json.dumps({"framing_caps": caps, "template": tmpl,
                                                   "verbs": VERBS, "tls": "1.2"}, indent=1))
    rows = [{"cover": cv, "task": t, "seed": s, "db_eq": v["db_eq"], "account_eq": v["acct"],
             "user": tasks[t].user_id,
             "has_cancel": int(any(n == "cancel_pending_order" for n, _ in progs[t]["actions"])),
             "has_return": int(any(n == "return_delivered_order_items" for n, _ in progs[t]["actions"])),
             "calls": [{k: c[k] for k in ("name", "kind", "req", "resp", "err")} for c in v["calls"]]}
            for (cv, t, s), v in sessions.items()]
    (HERE / "e6_sessions.json").write_text(json.dumps(rows))
    (HERE / "e7_records.json").write_text(json.dumps([{"cover": a, "framing": b, "task": t, "seed": s, "records": v}
                                                      for (a, b, t, s), v in net.items()]))


if __name__ == "__main__":
    main()
