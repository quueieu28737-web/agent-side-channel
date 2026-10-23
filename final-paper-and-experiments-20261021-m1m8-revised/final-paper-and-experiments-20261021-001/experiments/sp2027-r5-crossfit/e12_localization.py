"""E12: where does real-agent intent leakage live, and why do workflow rules not remove it?

Oracle ablation on the raw (undefended) network and dispatch views, cross-fitted
with the same customer folds as E10: the observer sees (a) the full trace,
(b) the trace with every state-changing write exchange removed, or (c) only the
write exchanges. Also reports how strongly the rules prompt homogenizes the
read-only prefix versus the write calls. No calibration is involved.
"""
from collections import Counter, defaultdict

import numpy as np

import r5lib as L
from e10_crossfit import folds_of, K

VIEWS = {'full': lambda c: True, 'no_writes': lambda c: c['name'] not in L.ev.WRITES,
         'writes_only': lambda c: c['name'] in L.ev.WRITES}


def session(e, keep):
    calls = [dict({k: c[k] for k in ('name', 'req', 'resp', 'err')}, kind='real') for c in e['calls'] if keep(c)]
    return {**{k: e[k] for k in ('task', 'repeat', 'prompt', 'user', 'has_cancel', 'has_return')},
            'calls': calls, 'records': L.tlsmodel.session(calls, 'raw', {})}


def entropy(counter):
    p = np.array(list(counter.values()), float); p /= p.sum()
    return float(-(p * np.log2(p)).sum())


def main():
    ns, tools, base, tasks = L.load()
    verbs = sorted(tools)
    rows, split = L.all_episodes()
    fold = folds_of(rows)
    out = []
    for vname, keep in VIEWS.items():
        S = {(e['prompt'], e['task'], e['repeat']): session(e, keep) for e in rows}
        for arm in L.PROMPTS:
            for target, (lab, verb) in L.ev.TARGETS.items():
                for view in ('dispatch', 'network'):
                    att_all = defaultdict(lambda: (np.zeros(0), np.zeros(0, int))); order = []
                    for k in range(K):
                        tr = [S[arm, e['task'], e['repeat']] for e in rows if e['prompt'] == arm and fold[e['user']] != k]
                        te = [S[arm, e['task'], e['repeat']] for e in rows if e['prompt'] == arm and fold[e['user']] == k]
                        att = L.attack_suite(tr, te, tr, lab, verb, view, verbs, extended=True)
                        for n, (sc, pr) in att.items():
                            att_all[n] = (np.concatenate([att_all[n][0], sc]), np.concatenate([att_all[n][1], pr]))
                        order += te
                    summ, _, _ = L.summarize(L.units_of(order, lab), dict(att_all))
                    out.append({'observer': vname, 'prompt': arm, 'target': target, 'view': view,
                                **{k: summ[k] for k in ('core_ba', 'core_ba_ci95', 'ext_ba', 'ext_ba_ci95', 'core_auroc')}})
                    print(vname, arm, target, view, round(summ['core_ba'], 3), [round(x, 3) for x in summ['core_ba_ci95']], flush=True)
    homog = []
    for arm in L.PROMPTS:
        es = [e for e in rows if e['prompt'] == arm]
        reads = Counter(tuple(c['name'] for c in e['calls'] if c['name'] not in L.ev.WRITES) for e in es)
        writes = Counter(tuple(c['name'] for c in e['calls'] if c['name'] in L.ev.WRITES) for e in es)
        homog.append({'prompt': arm, 'episodes': len(es),
                      'distinct_read_sequences': len(reads), 'read_sequence_entropy_bits': entropy(reads),
                      'distinct_write_sequences': len(writes), 'write_sequence_entropy_bits': entropy(writes),
                      'mean_reads': float(np.mean([sum(c['name'] not in L.ev.WRITES for c in e['calls']) for e in es])),
                      'mean_writes': float(np.mean([sum(c['name'] in L.ev.WRITES for c in e['calls']) for e in es]))})
        print(homog[-1], flush=True)
    L.write(L.HERE / 'e12_localization_results.json', {'results': out, 'homogenization': homog,
            'scope': 'Oracle ablation of undefended traces; cross-fitted with E10 customer folds.'})


if __name__ == '__main__':
    main()
