"""E5: token-streaming emitter over TLS 1.2 and TLS 1.3 (loopback).

Question: does the buffered, training-fitted cap result (Section 8.1) transfer
when the same saved texts are emitted as an SSE-style token stream? Every
observation below is a real socket capture; nothing is computed from accounting.

Tokenization uses tiktoken o200k_base as a proxy segmentation; the generating
model's own tokenizer and timing were not saved. Timing is reported only as a
token-interval accounting proxy, not measured latency.
"""
import hashlib
import json
import tempfile
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import tiktoken
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
sys.path.insert(0, str(HERE))
import tlslab  # noqa: E402

E1 = PKG / "evidence/retained-release007/controlled-study/data/replay-inputs/e1.jsonl"
SEED = 20261021
DRAWS = 10
ENC = tiktoken.get_encoding("o200k_base")
PRE = b'data: {"id":"chatcmpl-r2","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":'
POST = b'}}]}\n\n'
DONE = b"data: [DONE]\n\n"


def load_texts():
    items = [json.loads(s) for s in E1.read_text(encoding="utf-8").splitlines() if s.strip()]
    sets = {"T1": [], "T3": []}
    for i in items:
        sets["T1"].append(dict(i))
        partner = next(j for j in items if j["id"] == i["id"][:-1] + "1")
        sents = [s.strip() for s in partner["text"].split(".") if s.strip()]
        sets["T3"].append(dict(i, text=". ".join(sents[:2 + i["label"]]) + "."))
    return sets


def tokens(text):
    return [ENC.decode([t]) for t in ENC.encode(text)]


def event(content: str, pad: int = 0):
    body = json.dumps(content).encode()
    if pad:
        return PRE + body + b',"p":"' + b"x" * pad + b'"' + POST
    return PRE + body + POST


def pad_to(ev_content, size):
    """Event carrying content, padded with an obfuscation field to exactly size bytes
    (or the next multiple of 16 above size if it overflows; never truncates)."""
    base = len(event(ev_content, 1)) - 1
    target = size if base <= size else int(math.ceil(base / 16) * 16)
    return event(ev_content, target - base) if target > base else event(ev_content, 1)


class Policies:
    def __init__(self, train_texts):
        toks = [tokens(t) for t in train_texts]
        self.tok_size = int(math.ceil(max(len(event(x, 1)) for ts in toks for x in ts) / 16) * 16)
        self.batch_size = int(math.ceil(max(len(event("".join(ts[k:k + 8]), 1))
                                            for ts in toks for k in range(0, len(ts), 8)) / 64) * 64)
        self.n_cap = max(len(ts) for ts in toks)
        framed = max(len(t.encode()) + 4 for t in train_texts)
        self.buf_cap = int(math.ceil(framed / 128) * 128)

    def events(self, text, policy, rng):
        ts = tokens(text)
        n = len(ts)
        if policy == "buffered_raw":
            body = text.encode(); msg = len(body).to_bytes(4, "big") + body
            return [msg[j:j + 128] for j in range(0, len(msg), 128)], dict(ttfb=n, done=n, delay=float(np.mean([n - i for i in range(1, n + 1)])))
        if policy == "buffered_cap":
            body = text.encode(); msg = len(body).to_bytes(4, "big") + body
            tgt = max(self.buf_cap, int(math.ceil(len(msg) / 128) * 128)); msg += b"\0" * (tgt - len(msg))
            return [msg[j:j + 128] for j in range(0, len(msg), 128)], dict(ttfb=n, done=n, delay=float(np.mean([n - i for i in range(1, n + 1)])))
        if policy == "tok_raw":
            ev = [event(x) for x in ts]
        elif policy == "tok_randpad":
            ev = [event(x, int(rng.integers(1, 65))) for x in ts]
        elif policy in ("tok_const", "tok_const_cap"):
            ev = [pad_to(x, self.tok_size) for x in ts]
            if policy == "tok_const_cap":
                ev += [pad_to("", self.tok_size) for _ in range(max(0, self.n_cap - n))]
        elif policy == "batch8_const":
            ev = [pad_to("".join(ts[k:k + 8]), self.batch_size) for k in range(0, n, 8)]
            delay = float(np.mean([min(n, (i // 8 + 1) * 8) - (i + 1) for i in range(n)]))
            return ev + [DONE], dict(ttfb=min(n, 8), done=n, delay=delay)
        else:
            raise ValueError(policy)
        done = self.n_cap if policy == "tok_const_cap" else n
        return ev + [DONE], dict(ttfb=1, done=max(n, done), delay=0.0)


def decode_stream(raw: bytes, policy):
    if policy.startswith("buffered"):
        n = int.from_bytes(raw[:4], "big"); return raw[4:4 + n].decode()
    out = []
    for block in raw.split(b"\n\n"):
        if not block or block == b"data: [DONE]":
            continue
        obj = json.loads(block[len(b"data: "):])
        out.append(obj["choices"][0]["delta"]["content"])
    return "".join(out)


def features(seq):
    a = np.array(seq, dtype=float)
    hist = np.histogram(a, bins=16, range=(0, 512))[0] / max(1, len(a))
    return [len(a), a.sum(), a.mean(), a.std(), a.max(), a.min()] + hist.tolist()


def thr_fit(x, y):
    best = (np.mean(np.array(y) == 0), ("const", 0))
    if np.mean(y) > best[0]:
        best = (np.mean(y), ("const", 1))
    xs = sorted(set(x))
    for a, b in zip(xs, xs[1:]):
        th = (a + b) / 2
        for d in (1, -1):
            p = [(v >= th) == (d == 1) for v in x]
            acc = np.mean(np.array(p, int) == np.array(y))
            if acc > best[0]:
                best = (acc, ("thr", th, d))
    return best[1]


def thr_pred(rule, x):
    if rule[0] == "const":
        return [rule[1]] * len(x)
    return [int((v >= rule[1]) == (rule[2] == 1)) for v in x]


def topic_boot(by_topic, seed=SEED):
    v = np.array([np.mean(x) for _, x in sorted(by_topic.items())])
    rng = np.random.default_rng(seed)
    d = v[rng.integers(0, len(v), (10000, len(v)))].mean(1)
    return [float(v.mean()), float(np.quantile(d, .025)), float(np.quantile(d, .975))]


def identify(obs, profiles, rng):
    """Expected top-1 accuracy with uniform tie breaking; returns (acc, ambiguity)."""
    def dist(a, b):
        m = min(len(a), len(b))
        return abs(len(a) - len(b)) * 1e6 + sum(abs(x - y) for x, y in zip(a[:m], b[:m]))
    accs, amb = [], []
    for i, o in enumerate(obs):
        d = np.array([dist(o, p) for p in profiles])
        ties = np.flatnonzero(d == d.min())
        accs.append(float(i in ties) / len(ties)); amb.append(len(ties))
    return accs, amb


POLICIES = ["buffered_raw", "buffered_cap", "tok_raw", "tok_randpad", "tok_const", "batch8_const", "tok_const_cap"]
RANDOM = {"tok_randpad"}


def main():
    sets = load_texts()
    results, raw_rows = [], []
    for version in ["1.2", "1.3"]:
        srv, cli = tlslab.make_contexts(Path(tempfile.gettempdir()) / "sp2027-r2-cert", version)
        for target, items in sets.items():
            train = [i for i in items if i["split"] == "train"]
            pol = Policies([i["text"] for i in train])
            caps = {}
            for policy in POLICIES:
                n_draw = DRAWS if policy in RANDOM else 1
                rng = np.random.default_rng(SEED)
                for draw in range(n_draw + 1):  # last extra draw = attacker's independent profiling run
                    for i in items:
                        evs, lat = pol.events(i["text"], policy, rng)
                        r = tlslab.run_stream(srv, cli, evs)
                        assert len(r["record_payloads"]) == len(evs), (policy, len(r["record_payloads"]), len(evs))
                        assert decode_stream(r["received"], policy) == i["text"]
                        caps[(policy, draw, i["id"])] = r["record_payloads"]
                        raw_rows.append({"tls": version, "target": target, "policy": policy, "draw": draw,
                                         "id": i["id"], "label": i["label"], "split": i["split"],
                                         "n_tokens": len(tokens(i["text"])), "records": r["record_payloads"],
                                         "cipher": r["cipher"], "latency_proxy": lat,
                                         "sha256": hashlib.sha256(i["text"].encode()).hexdigest()})
                print(version, target, policy, "captured", flush=True)
            base_wire = np.mean([sum(x + 5 for x in caps[("tok_raw", 0, i["id"])]) for i in items])
            buf_wire = np.mean([sum(x + 5 for x in caps[("buffered_raw", 0, i["id"])]) for i in items])
            d0y = [i["label"] for i in train]
            d0_thr = {src: thr_fit([features(caps[(src, 0, i["id"])])[1] for i in train], d0y)
                      for src in ("tok_raw", "buffered_raw")}
            for policy in POLICIES:
                clean = "buffered_raw" if policy.startswith("buffered") else "tok_raw"
                n_draw = DRAWS if policy in RANDOM else 1
                by = defaultdict(lambda: defaultdict(list)); id_acc, id_amb, wires = [], [], []
                for draw in range(n_draw):
                    X = {i["id"]: features(caps[(policy, draw, i["id"])]) for i in items}
                    ytr = [i["label"] for i in train]
                    test = [i for i in items if i["split"] == "test"]
                    xtr = [X[i["id"]] for i in train]; xte = [X[i["id"]] for i in test]
                    preds = {
                        "D0_total_threshold": thr_pred(d0_thr[clean], [x[1] for x in xte]),
                        "D2_total_threshold": thr_pred(thr_fit([x[1] for x in xtr], ytr), [x[1] for x in xte]),
                        "D2_count_threshold": thr_pred(thr_fit([x[0] for x in xtr], ytr), [x[0] for x in xte]),
                    }
                    if len(set(map(tuple, xtr))) > 1:
                        lr = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000))
                        lr.fit(xtr, ytr); preds["D2_sequence_logreg"] = lr.predict(xte).tolist()
                    else:
                        preds["D2_sequence_logreg"] = [int(np.mean(ytr) > .5)] * len(xte)
                    for name, p in preds.items():
                        for i, v in zip(test, p):
                            by[name][i["group_id"]].append(int(v == i["label"]))
                    prof = [caps[(policy, n_draw, i["id"])] for i in items]
                    obs = [caps[(policy, draw, i["id"])] for i in items]
                    a, m = identify(obs, prof, None); id_acc += a; id_amb += m
                    wires += [sum(x + 5 for x in o) for o in obs]
                lat = [r["latency_proxy"] for r in raw_rows if r["tls"] == version and r["target"] == target and r["policy"] == policy and r["draw"] == 0]
                results.append({
                    "tls": version, "target": target, "policy": policy, "draws": n_draw,
                    "binary_accuracy": {k: topic_boot(v) for k, v in by.items()},
                    "best_D2_binary_accuracy": max(topic_boot(v)[0] for k, v in by.items() if k.startswith("D2")),
                    "identification_top1": float(np.mean(id_acc)), "identification_chance": 1 / len(items),
                    "mean_ambiguity_set": float(np.mean(id_amb)),
                    "mean_records": float(np.mean([len(caps[(policy, 0, i["id"])]) for i in items])),
                    "mean_wire_bytes": float(np.mean(wires)),
                    "ratio_vs_token_stream": float(np.mean(wires) / base_wire),
                    "ratio_vs_buffered_unpadded": float(np.mean(wires) / buf_wire),
                    "ttfb_token_intervals": float(np.mean([x["ttfb"] for x in lat])),
                    "completion_token_intervals": float(np.mean([x["done"] for x in lat])),
                    "mean_delivery_delay_token_intervals": float(np.mean([x["delay"] for x in lat])),
                    "test_overflow_outputs": int(sum(
                        (len(tokens(i["text"])) > pol.n_cap) if policy == "tok_const_cap" else
                        (len(i["text"].encode()) + 4 > pol.buf_cap) if policy == "buffered_cap" else 0
                        for i in items if i["split"] == "test")),
                    "fitted": {"tok_event_bytes": pol.tok_size, "batch_event_bytes": pol.batch_size,
                               "n_cap_tokens": pol.n_cap, "buffered_cap_bytes": pol.buf_cap},
                })
    (HERE / "e5_streaming_results.json").write_text(json.dumps(results, indent=1))
    (HERE / "e5_streaming_captures.json").write_text(json.dumps(raw_rows))
    for r in results:
        print(r["tls"], r["target"], f'{r["policy"]:14s}', "D2best=%.3f" % r["best_D2_binary_accuracy"],
              "D0=%.3f" % r["binary_accuracy"]["D0_total_threshold"][0],
              "ID=%.3f" % r["identification_top1"], "ratio=%.2f" % r["ratio_vs_token_stream"],
              "vsbuf=%.2f" % r["ratio_vs_buffered_unpadded"])


if __name__ == "__main__":
    main()
