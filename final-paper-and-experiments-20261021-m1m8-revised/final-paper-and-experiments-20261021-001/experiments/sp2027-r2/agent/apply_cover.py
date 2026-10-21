"""E8 step 2: apply online cover and transport framing to recorded agent trajectories,
replay every session over loopback TLS 1.2, and evaluate with e67_eval.py.

Unlike E6, which knew each reference program in advance, an agent's dispatcher only
knows the calls made so far. Every policy here is therefore *online*: it decides
before each real call, using only the history, and may flush remaining cover when
the session ends. Shadow cover runs in a per-session sandbox copy of the initial
database and never reaches the agent, so one trajectory serves all policies.

  python -B apply_cover.py runs/scripted
  python -B apply_cover.py runs/gpt-4o --no-tls     # dispatch view only (fast)
"""
import argparse
import json
import random
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[1] / "reviewer-audit"))
import retail_replay as old  # noqa: E402
import tlslab  # noqa: E402
import e67_eval  # noqa: E402
from e6_e7_retail_cover import frame, invoke, template  # noqa: E402

COVERS = ["none", "cancel_p50", "cancel_p100", "cancel_const2", "decoy1", "shape_eq"]
NET_COVERS = ["none", "cancel_const2", "decoy1", "shape_eq"]
FRAMINGS = ["raw", "bucket1024", "const"]


class Online:
    """Online cover controller. step() is called before each real call and returns the
    cover calls to dispatch first; end() returns calls to flush after the last one."""

    def __init__(self, cover, rng, tid, user, progs, tmpl, hazard):
        self.cover, self.rng, self.h, self.tmpl = cover, rng, hazard, tmpl
        others = [j for j, p in enumerate(progs) if j != tid and p["user"] != user]
        self.cancels = [a for j in others for a in progs[j]["actions"] if a[0] == "cancel_pending_order"]
        self.by_verb = defaultdict(list)
        for j in others:
            for a in progs[j]["actions"]:
                self.by_verb[a[0]].append(a)
        self.pending = cover == "cancel_p100" or (cover == "cancel_p50" and rng.random() < 0.5)
        self.decoy = list(progs[rng.choice(others)]["actions"]) if cover == "decoy1" else []
        self.seen = Counter()
        self.emitted = Counter()

    def _cancel(self):
        self.emitted["cancel_pending_order"] += 1
        return self.rng.choice(self.cancels)

    def _deficit(self):
        return {v: c - self.seen[v] - self.emitted[v] for v, c in self.tmpl.items() if c - self.seen[v] - self.emitted[v] > 0}

    def step(self, real_name):
        out = []
        if self.cover.startswith("cancel_p") and self.pending and self.rng.random() < self.h:
            out.append(self._cancel()); self.pending = False
        if self.cover == "cancel_const2" and self.emitted["cancel_pending_order"] == 0 \
                and self.seen["cancel_pending_order"] < 2 and self.rng.random() < self.h:
            out.append(self._cancel())
        if self.cover == "decoy1":
            while self.decoy and self.rng.random() < 0.5:
                out.append(self.decoy.pop(0))
        if self.cover == "shape_eq" and self.rng.random() < 0.6:
            d = self._deficit()
            if d:
                v = self.rng.choices(list(d), weights=list(d.values()))[0]
                self.emitted[v] += 1; out.append(self.rng.choice(self.by_verb[v]))
        self.seen[real_name] += 1
        return out

    def end(self):
        out = []
        if self.cover.startswith("cancel_p") and self.pending:
            out.append(self._cancel())
        if self.cover == "cancel_const2":
            while self.seen["cancel_pending_order"] + self.emitted["cancel_pending_order"] < 2:
                out.append(self._cancel())
        if self.cover == "decoy1":
            out += self.decoy; self.decoy = []
        if self.cover == "shape_eq":
            rest = [v for v, c in self._deficit().items() for _ in range(c)]
            self.rng.shuffle(rest)
            for v in rest:
                self.emitted[v] += 1; out.append(self.rng.choice(self.by_verb[v]))
        return out

    def overflow(self):
        if self.cover == "shape_eq":
            return any(self.seen[v] > c for v, c in self.tmpl.items()) or any(v not in self.tmpl for v in self.seen)
        if self.cover == "cancel_const2":
            return self.seen["cancel_pending_order"] + self.emitted["cancel_pending_order"] > 2
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--no-tls", action="store_true")
    a = ap.parse_args()
    D = Path(a.run_dir).resolve()
    ns, tools, base, tasks = old.load_tau()
    progs = [{"user": t.user_id, "actions": [(x.name, dict(x.kwargs)) for x in t.actions]} for t in tasks]
    tmpl = template(progs)
    hazard = 1 / statistics.median(len(p["actions"]) for p in progs)
    eps = [json.loads(l) for l in (D / "trajectories.jsonl").read_text().splitlines()]
    seeds = sorted({e["seed"] for e in eps})
    by_task = defaultdict(dict)
    for e in eps:
        by_task[e["task"]][e["seed"]] = e
    keep = sorted(t for t, v in by_task.items() if len(v) == len(seeds))  # complete task x seed grid only
    sessions, overflow = [], defaultdict(list)
    for ci, cover in enumerate(COVERS):
        for tid in keep:
            for seed in seeds:
                e = by_task[tid][seed]
                rng = random.Random(seed * 1000003 + tid * 7919 + ci)
                ctl = Online(cover, rng, tid, tasks[tid].user_id, progs, tmpl, hazard)
                shadow = old.fast_clone(base)
                calls = []

                def add_cover(lst):
                    for name, kw in lst:
                        resp = invoke(tools, shadow, name, kw)
                        req = json.dumps({"name": name, "arguments": kw}, sort_keys=True)
                        calls.append({"name": name, "kind": "cover", "req": len(req.encode()), "resp": len(resp.encode()),
                                      "err": resp.startswith("Error:"), "req_text": req, "resp_text": resp})
                for c in e["calls"]:
                    add_cover(ctl.step(c["name"]))
                    calls.append({"name": c["name"], "kind": "real", "req": c["req"], "resp": c["resp"], "err": c["err"],
                                  "req_text": c["req_text"], "resp_text": c["resp_text"]})
                add_cover(ctl.end())
                overflow[cover].append(ctl.overflow())
                sessions.append({"cover": cover, "task": tid, "seed": seed, "db_eq": e["db_eq"], "account_eq": e["account_eq"],
                                 "user": e["user"], "has_cancel": e["has_cancel"], "has_return": e["has_return"], "calls": calls})
        print("covered", cover, flush=True)
    verbs = sorted({c["name"] for s in sessions for c in s["calls"]} | set(tmpl))
    ref = [c for s in sessions if s["cover"] == "none" for c in s["calls"]]
    caps = {"req": int(np.ceil((max(c["req"] for c in ref) + 4) / 256) * 256),
            "resp": int(np.ceil((np.quantile([c["resp"] for c in ref], 0.95) + 4) / 1024) * 1024)}
    (D / "e6_sessions.json").write_text(json.dumps([{k: v for k, v in s.items()} | {"calls": [
        {k: c[k] for k in ("name", "kind", "req", "resp", "err")} for c in s["calls"]]} for s in sessions]))
    recs = []
    if not a.no_tls:
        srv, cli = tlslab.make_contexts(Path(tempfile.gettempdir()) / "sp2027-r2-cert", "1.2")
        for s in sessions:
            if s["cover"] not in NET_COVERS:
                continue
            for fr in FRAMINGS:
                ex = [(frame(c["req_text"], fr, True, caps), frame(c["resp_text"], fr, False, caps)) for c in s["calls"]]
                q = tlslab.run_session(srv, cli, ex)
                assert sum(d == "c2s" for d, _ in q) == len(ex)
                recs.append({"cover": s["cover"], "framing": fr, "task": s["task"], "seed": s["seed"], "records": q})
        print("TLS sessions", len(recs), flush=True)
    else:  # e67_eval needs the file; an empty network view is skipped below
        recs = []
    (D / "e7_records.json").write_text(json.dumps(recs))
    (D / "e7_meta.json").write_text(json.dumps({"framing_caps": caps, "template": tmpl, "verbs": verbs, "tls": "1.2",
                                                "online_hazard": hazard}, indent=1))
    util = {}
    for cover in COVERS:
        S = [s for s in sessions if s["cover"] == cover]
        nr = sum(c["kind"] == "real" for s in S for c in s["calls"]); nc = sum(c["kind"] == "cover" for s in S for c in s["calls"])
        util[cover] = {"sessions": len(S), "call_overhead": nc / max(1, nr),
                       "template_overflow_rate": float(np.mean(overflow[cover]))}
    E = [by_task[t][s] for t in keep for s in seeds]
    summary = {"episodes": len(E), "tasks": len(keep), "seeds": seeds,
               "native_reward": float(np.mean([e["native_reward"] for e in E])),
               "db_equality": float(np.mean([e["db_eq"] for e in E])),
               "agent_attempted_cancel_given_label": float(np.mean([e["attempted_cancel"] for e in E if e["has_cancel"]] or [np.nan])),
               "agent_attempted_cancel_given_no_label": float(np.mean([e["attempted_cancel"] for e in E if not e["has_cancel"]] or [np.nan])),
               "mean_real_calls": float(np.mean([len(e["calls"]) for e in E])),
               "status": dict(Counter(e["status"] for e in E)), "covers": util}
    (D / "e8_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    if recs:
        e67_eval.main(D)
    else:
        print("dispatch-only run: evaluate the network view after a TLS replay")


if __name__ == "__main__":
    main()
