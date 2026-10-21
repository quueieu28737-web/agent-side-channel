"""Evaluate E6 (dispatch view) and E7 (agent-tool TLS link) from saved artifacts.

Inputs : e6_sessions.json, e7_records.json, e7_meta.json (from e6_e7_retail_cover.py)
Outputs: e6_dispatch_results.json, e7_network_results.json

Attackers (all evaluated by task-grouped stratified 5-fold CV over 115 tasks x
3 seeds; every unit of a task is in the same fold):
  D0_gboost        gradient boosting fitted on undefended sessions of training tasks
  D2_logreg/gboost fitted on defended sessions of training tasks
  count_rule       balanced-accuracy-optimal threshold on the visible target-verb count
  D2_decode_*      (network view only) a profiling attacker that learns a
                   record-size -> tool table from training-fold calls (it can issue
                   its own calls to the public tool API), decodes every test call,
                   then applies the dispatch-view attackers to the decoded trace.
The reported 'best' attacker is the maximum over all attackers, including D0;
this favours the attacker and is conservative for the defense.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
WRITES = {"cancel_pending_order", "modify_pending_order_address", "modify_pending_order_items",
          "modify_pending_order_payment", "modify_user_address", "return_delivered_order_items",
          "exchange_delivered_order_items"}
TARGETS = {"cancel": ("has_cancel", "cancel_pending_order"),
           "return": ("has_return", "return_delivered_order_items")}
SEED = 20261021


def disp_features(calls, verbs):
    cnt = Counter(c["name"] for c in calls)
    f = [cnt.get(v, 0) for v in verbs]
    f += [np.mean([c["resp"] for c in calls if c["name"] == v]) if cnt.get(v) else 0 for v in verbs]
    names = [c["name"] for c in calls]
    big = Counter(zip(names, names[1:]))
    f += [big.get((a, b), 0) for a in verbs for b in ("cancel_pending_order", "get_order_details")]
    f += [len(calls), sum(c["name"] in WRITES for c in calls), sum(c.get("err", False) for c in calls)]
    return f


def exchanges(seq):
    """Group a direction-tagged record sequence into (request bytes, response bytes)."""
    out = []
    for d, n in seq:
        if d == "c2s":
            out.append([n, 0])
        else:
            out[-1][1] += n
    return out


def net_features(seq):
    c2s = [n for d, n in seq if d == "c2s"]; s2c = [n for d, n in seq if d == "s2c"]
    ex = exchanges(seq)
    f = [len(c2s), len(s2c), sum(c2s), sum(s2c), len(ex)]
    f += np.histogram(c2s, bins=96, range=(0, 1536))[0].tolist()
    f += np.histogram(np.log2(np.array([b for _, b in ex]) + 1), bins=22, range=(4, 15))[0].tolist()
    f += ([a for a, _ in ex][:24] + [0] * 24)[:24] + ([b for _, b in ex][:24] + [0] * 24)[:24]
    return f


def cluster_boot(units, scores, preds, n=2000):
    tids = sorted(set(u["task"] for u in units))
    idx = defaultdict(list)
    for k, u in enumerate(units):
        idx[u["task"]].append(k)
    y = np.array([u["y"] for u in units]); s = np.array(scores, float); p = np.array(preds)

    def stat(ix):
        yy, pp, ss = y[ix], p[ix], s[ix]
        if yy.min() == yy.max():
            return np.nan, np.nan
        ba = 0.5 * (np.mean(pp[yy == 1] == 1) + np.mean(pp[yy == 0] == 0))
        pos, neg = ss[yy == 1], ss[yy == 0]
        auc = np.mean((pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :]))
        return ba, auc
    ba, auc = stat(np.arange(len(units)))
    rng = np.random.default_rng(SEED); bs = []
    for _ in range(n):
        pick = rng.choice(tids, len(tids))
        bs.append(stat(np.concatenate([idx[t] for t in pick])))
    bs = np.array(bs, float)
    q = lambda c: [float(np.nanquantile(bs[:, c], .025)), float(np.nanquantile(bs[:, c], .975))]
    return {"ba": float(ba), "ba_ci95": q(0), "auroc": float(auc), "auroc_ci95": q(1)}


def folds(units):
    y = np.array([u["y"] for u in units]); g = np.array([u["task"] for u in units])
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    return list(cv.split(np.zeros(len(y)), y, g)), y


MODELS = {
    "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, class_weight="balanced", max_iter=5000)),
    "gboost": lambda: HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_depth=3,
                                                     class_weight="balanced", random_state=0),
}


def learned(units, fs, y, Xtr_fn, Xte_fn, model):
    sc = np.zeros(len(y)); pr = np.zeros(len(y), int)
    for k, (tr, te) in enumerate(fs):
        m = MODELS[model](); m.fit(np.array(Xtr_fn(k, tr), float), y[tr])
        prob = m.predict_proba(np.array(Xte_fn(k, te), float))[:, 1]
        sc[te] = prob; pr[te] = (prob >= .5).astype(int)
    return cluster_boot(units, sc, pr)


def rule(units, fs, y, counts_fn):
    sc = np.zeros(len(y)); pr = np.zeros(len(y), int)
    for k, (tr, te) in enumerate(fs):
        ctr, cte = np.array(counts_fn(k, tr)), np.array(counts_fn(k, te))
        best = (-1, 0)
        for th in range(0, int(max(ctr.max(), cte.max())) + 2):
            p = (ctr >= th).astype(int)
            b = 0.5 * (np.mean(p[y[tr] == 1] == 1) + np.mean(p[y[tr] == 0] == 0))
            if b > best[0]:
                best = (b, th)
        sc[te] = cte; pr[te] = (cte >= best[1]).astype(int)
    return cluster_boot(units, sc, pr)


def summarize(res):
    best = max(res.items(), key=lambda kv: kv[1]["ba"])
    return {"best_attacker": best[0], "best_ba": best[1]["ba"], "best_ba_ci95": best[1]["ba_ci95"],
            "best_auroc": max(v["auroc"] for v in res.values())}


def main():
    meta = json.loads((HERE / "e7_meta.json").read_text())
    verbs = meta["verbs"]
    S = {(r["cover"], r["task"], r["seed"]): r for r in json.loads((HERE / "e6_sessions.json").read_text())}
    covers = list(dict.fromkeys(k[0] for k in S))
    tasks = sorted({k[1] for k in S}); seeds = sorted({k[2] for k in S})
    e6 = []
    for tgt, (lab, verb) in TARGETS.items():
        units = [{"task": t, "seed": s, "y": S[("none", t, s)][lab]} for t in tasks for s in seeds]
        fs, y = folds(units)
        X0 = [disp_features(S[("none", u["task"], u["seed"])]["calls"], verbs) for u in units]
        for cover in covers:
            sess = [S[(cover, u["task"], u["seed"])] for u in units]
            X = [disp_features(s["calls"], verbs) for s in sess]
            res = {"D0_gboost": learned(units, fs, y, lambda k, ix: [X0[i] for i in ix], lambda k, ix: [X[i] for i in ix], "gboost")}
            for m in MODELS:
                res["D2_" + m] = learned(units, fs, y, lambda k, ix: [X[i] for i in ix], lambda k, ix: [X[i] for i in ix], m)
            cnt = [sum(c["name"] == verb for c in s["calls"]) for s in sess]
            res["count_rule"] = rule(units, fs, y, lambda k, ix: [cnt[i] for i in ix])
            nr = sum(c["kind"] == "real" for s in sess for c in s["calls"])
            nc = sum(c["kind"] == "cover" for s in sess for c in s["calls"])
            e6.append({"target": tgt, "cover": cover, "attackers": res, **summarize(res),
                       "db_equality": float(np.mean([s["db_eq"] for s in sess])),
                       "account_equality": float(np.mean([s["account_eq"] for s in sess])),
                       "call_overhead": nc / nr,
                       "cover_error_rate": float(np.mean([c["err"] for s in sess for c in s["calls"] if c["kind"] == "cover"])) if nc else 0.0,
                       "positive_tasks": int(sum(u["y"] for u in units) // len(seeds)), "tasks": len(tasks), "units": len(units)})
            print("E6", tgt, f"{cover:22s}", "best=%s %.3f [%.2f,%.2f]" % (e6[-1]["best_attacker"], e6[-1]["best_ba"], *e6[-1]["best_ba_ci95"]),
                  "db=%.2f ovh=%.2f" % (e6[-1]["db_equality"], e6[-1]["call_overhead"]), flush=True)
    (HERE / "e6_dispatch_results.json").write_text(json.dumps(e6, indent=1))

    R = {(r["cover"], r["framing"], r["task"], r["seed"]): [tuple(x) for x in r["records"]]
         for r in json.loads((HERE / "e7_records.json").read_text())}
    ncovers = list(dict.fromkeys(k[0] for k in R)); framings = list(dict.fromkeys(k[1] for k in R))
    base_wire = np.mean([sum(n + 5 for _, n in R[("none", "raw", t, s)]) for t in tasks for s in seeds])
    base_rt = np.mean([len(S[("none", t, s)]["calls"]) for t in tasks for s in seeds])
    e7, ident = [], {}
    for framing in framings:
        rows = [(c["name"], ex[0]) for t in tasks for c, ex in zip(S[("none", t, seeds[0])]["calls"], exchanges(R[("none", framing, t, seeds[0])]))]
        by = defaultdict(Counter)
        for nm, sz in rows:
            by[sz][nm] += 1
        ident[framing] = {"calls": len(rows), "distinct_request_sizes": len(by),
                          "request_size_to_tool_accuracy": sum(max(c.values()) for c in by.values()) / len(rows),
                          "majority_tool_baseline": max(Counter(n for n, _ in rows).values()) / len(rows)}
    for tgt, (lab, verb) in TARGETS.items():
        units = [{"task": t, "seed": s, "y": S[("none", t, s)][lab]} for t in tasks for s in seeds]
        fs, y = folds(units)
        for framing in framings:
            X0 = [net_features(R[("none", framing, u["task"], u["seed"])]) for u in units]
            for cover in ncovers:
                seqs = [R[(cover, framing, u["task"], u["seed"])] for u in units]
                sess = [S[(cover, u["task"], u["seed"])] for u in units]
                X = [net_features(q) for q in seqs]
                res = {"D0_gboost": learned(units, fs, y, lambda k, ix: [X0[i] for i in ix], lambda k, ix: [X[i] for i in ix], "gboost")}
                for m in MODELS:
                    res["D2_" + m] = learned(units, fs, y, lambda k, ix: [X[i] for i in ix], lambda k, ix: [X[i] for i in ix], m)
                # Profiling decoder: (request bytes, response bytes) -> tool, else request bytes -> tool.
                exs = [exchanges(q) for q in seqs]
                tables = []
                for tr, _te in fs:
                    full, req = defaultdict(Counter), defaultdict(Counter)
                    for i in tr:
                        for c, (a, b) in zip(sess[i]["calls"], exs[i]):
                            full[(a, b)][c["name"]] += 1; req[a][c["name"]] += 1
                    tables.append(({k: v.most_common(1)[0][0] for k, v in full.items()},
                                   {k: v.most_common(1)[0][0] for k, v in req.items()}))

                def decode(k, i):
                    f, r = tables[k]
                    return [{"name": f.get((a, b), r.get(a, "unknown")), "resp": b} for a, b in exs[i]]
                dec = {i: decode(k, i) for k, (_tr, te) in enumerate(fs) for i in te}
                dfe = lambda k, ix: [disp_features(decode(k, i), verbs) for i in ix]
                res["D2_decode_gboost"] = learned(units, fs, y, dfe, dfe, "gboost")
                res["D2_decode_count_rule"] = rule(units, fs, y, lambda k, ix: [sum(c["name"] == verb for c in decode(k, i)) for i in ix])
                acc = np.mean([d["name"] == c["name"] for i in dec for d, c in zip(dec[i], sess[i]["calls"])])
                wire = np.mean([sum(n + 5 for _, n in q) for q in seqs])
                e7.append({"target": tgt, "cover": cover, "framing": framing, "attackers": res, **summarize(res),
                           "decoder_call_accuracy": float(acc),
                           "db_equality": float(np.mean([s["db_eq"] for s in sess])),
                           "mean_wire_bytes": float(wire), "wire_ratio": float(wire / base_wire),
                           "round_trip_ratio": float(np.mean([len(s["calls"]) for s in sess]) / base_rt)})
                print("E7", tgt, f"{cover:22s}", f"{framing:10s}", "best=%s %.3f [%.2f,%.2f]" % (e7[-1]["best_attacker"], e7[-1]["best_ba"], *e7[-1]["best_ba_ci95"]),
                      "dec=%.2f wire=%.2f rt=%.2f" % (acc, e7[-1]["wire_ratio"], e7[-1]["round_trip_ratio"]), flush=True)
    (HERE / "e7_network_results.json").write_text(json.dumps({"meta": meta, "tool_identification": ident, "results": e7}, indent=1))


if __name__ == "__main__":
    main()
