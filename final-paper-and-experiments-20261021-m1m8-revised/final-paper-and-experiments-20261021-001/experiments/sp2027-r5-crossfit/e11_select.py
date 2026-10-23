"""E11b: training-only operating-point selection on the frozen R4 split.

Selection rule (fixed in this file before the held-out stage is run):
  1. For every configuration in r5lib.FRONTIER, run customer-grouped 5-fold
     cross-fitting *inside the 69 R4 training tasks only* (calibration and
     attackers refit per inner fold) and record the network-view core-suite
     maximum BA for both targets and both prompts, plus the byte ratio.
  2. Eligible: every one of those four inner BAs is <= 0.60.
  3. Choose the eligible configuration with the smallest inner byte ratio
     (ties: smaller call ratio). If none is eligible, keep the R4 configuration.
  4. Write e11_selection.json, then calibrate the chosen configuration on all
     414 training episodes and evaluate it once on the frozen test tasks.
The held-out test episodes are never read before step 4. The rule was first run on the
663-run snapshot (41 test tasks; snapshot-660/) and then, unchanged, on the completed
690-run cohort (46 test tasks). Training data, hence the inner selection, are identical.
"""
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

import r5lib as L
from e10_crossfit import run_config, K


def inner_folds(rows):
    users = sorted({e['user'] for e in rows})
    lab = {u: 0 for u in users}
    for e in rows:
        lab[e['user']] = max(lab[e['user']], 2 * e['has_cancel'] + e['has_return'])
    cv = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=L.SEED + 1)
    fold = {}
    for k, (_, te) in enumerate(cv.split(np.zeros(len(users)), [lab[u] for u in users], users)):
        for i in te:
            fold[users[i]] = k
    return fold


def main():
    ns, tools, base, tasks = L.load()
    rows, split = L.all_episodes()
    train_ids = set(split['train'])
    train = [e for e in rows if e['task'] in train_ids]
    fold = inner_folds(train)
    inner = []
    for cfg in L.FRONTIER:
        res, _, _ = run_config(train, fold, cfg, tools, base, ['raw', 'shape_const'], L.PROMPTS, extended=False,
                               log=lambda m: print(m, flush=True))
        net = [r for r in res if r['view'] == 'network' and r['condition'] == 'shape_const']
        rec = {'config': cfg['name'], 'inner_network_core_ba': {f"{r['target']}/{r['prompt']}": r['core_ba'] for r in net},
               'inner_bytes_ratio': float(np.mean([r['bytes_ratio'] for r in net])),
               'inner_calls_ratio': float(np.mean([r['calls_ratio'] for r in net]))}
        rec['eligible'] = all(v <= .60 for v in rec['inner_network_core_ba'].values())
        inner.append(rec); print(rec, flush=True)
    eligible = [r for r in inner if r['eligible']]
    chosen = min(eligible, key=lambda r: (r['inner_bytes_ratio'], r['inner_calls_ratio']))['config'] if eligible else 'r4'
    L.write(L.HERE / 'e11_selection.json', {'rule': __doc__, 'inner': inner, 'chosen': chosen,
                                            'training_tasks': sorted(train_ids)})
    # Held-out stage: fold 0 = frozen test customers, fold 1 = frozen training customers.
    heldout = {e['user']: (0 if e['task'] not in train_ids else 1) for e in rows}
    out = []
    for name in dict.fromkeys(['r4', chosen]):
        cfg = next(c for c in L.FRONTIER if c['name'] == name)
        res, draws, cals = run_config(rows, heldout, cfg, tools, base, ['raw', 'shape_const'], L.PROMPTS,
                                      eval_folds=[0], log=lambda m: print(m, flush=True))
        for r in res:
            r['role'] = 'selected' if name == chosen else 'r4_reference'
        out += res
    L.write(L.HERE / 'e11_heldout_results.json', {'chosen': chosen, 'results': out,
            'scope': f'Frozen split: calibration on 414 training episodes, single evaluation on {sum(e["task"] not in train_ids for e in rows)} held-out episodes.'})
    for r in out:
        if r['view'] == 'network':
            print(r['config'], r['target'], r['prompt'], r['condition'], round(r['core_ba'], 3), r['core_ba_ci95'],
                  round(r['ext_ba'], 3), round(r['bytes_ratio'], 2), round(r['calls_ratio'], 2), flush=True)


if __name__ == '__main__':
    main()
