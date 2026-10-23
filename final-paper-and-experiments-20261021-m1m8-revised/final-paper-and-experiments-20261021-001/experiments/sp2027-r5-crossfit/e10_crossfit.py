"""E10/E11: customer-grouped cross-fitting of the training-only defense over all
660 complete-grid episodes (110 tasks, 51 customers), plus a pre-declared
operating-point frontier.

In every fold, calibration (template, donors, caps) and every attacker are fit
only on the other folds' customers; out-of-fold predictions are then pooled.
The frozen R4 split and its headline numbers are untouched (see e10_frozen in
verify_r5.py). No model is called; captures use the analytic TLS model that
reproduces all 2,640 socket-measured R4 sessions exactly.
"""
import argparse
import time
from collections import defaultdict

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

import r5lib as L

K = 5


def folds_of(rows):
    users = sorted({e['user'] for e in rows})
    lab = {u: 0 for u in users}
    for e in rows:
        lab[e['user']] = max(lab[e['user']], 2 * e['has_cancel'] + e['has_return'])
    y = np.array([lab[u] for u in users])
    cv = StratifiedGroupKFold(n_splits=K, shuffle=True, random_state=L.SEED)
    fold = {}
    for k, (_, te) in enumerate(cv.split(np.zeros(len(users)), y, users)):
        for i in te:
            fold[users[i]] = k
    return fold


def run_config(rows, fold, cfg, tools, base, conditions, arms, extended=True, log=print, eval_folds=range(K)):
    verbs = sorted(tools)
    key = lambda e: (e['prompt'], e['task'], e['repeat'])
    oof = defaultdict(dict)       # (target, view, arm, cond) -> attacker -> (scores, preds) arrays by test order
    order = defaultdict(list)     # (target, view, arm, cond) -> test sessions in pooled order
    cost = defaultdict(lambda: {'wire': 0, 'calls': 0, 'raw_wire': 0, 'raw_calls': 0, 'overflow': 0, 'n': 0})
    cals = []
    for k in eval_folds:
        t0 = time.time()
        train = [e for e in rows if fold[e['user']] != k]
        cal = L.fit_calibration(train, tools, base, cfg)
        cals.append({'fold': k, 'template': cal['template'], 'caps': cal['caps'],
                     'training_customers': len({e['user'] for e in train})})
        sess = {key(e): L.make_sessions(e, cal, cfg, tools, base, conditions) for e in rows}
        for arm in arms:
            tr_e = [e for e in train if e['prompt'] == arm]
            te_e = [e for e in rows if fold[e['user']] == k and e['prompt'] == arm]
            for cond in conditions:
                tr = [sess[key(e)][cond] for e in tr_e]; te = [sess[key(e)][cond] for e in te_e]
                tr_raw = [sess[key(e)]['raw'] for e in tr_e]
                c = cost[arm, cond]
                c['wire'] += sum(s['wire'] for s in te); c['calls'] += sum(len(s['calls']) for s in te)
                c['raw_wire'] += sum(sess[key(e)]['raw']['wire'] for e in te_e)
                c['raw_calls'] += sum(len(e['calls']) for e in te_e)
                c['overflow'] += sum(s['template_overflow'] for s in te); c['n'] += len(te)
                for target, (lab, verb) in L.ev.TARGETS.items():
                    for view in ('dispatch', 'network'):
                        att = L.attack_suite(tr, te, tr_raw, lab, verb, view, verbs, extended)
                        cell = (target, view, arm, cond)
                        for name, (sc, pr) in att.items():
                            prev = oof[cell].get(name, (np.zeros(0), np.zeros(0, int)))
                            oof[cell][name] = (np.concatenate([prev[0], sc]), np.concatenate([prev[1], pr]))
                        order[cell] += te
        log(f"  {cfg['name']} fold {k} done in {time.time()-t0:.0f}s caps={cal['caps']}")
    results = []; draws = {}
    for cell, att in oof.items():
        target, view, arm, cond = cell
        lab = L.ev.TARGETS[target][0]
        units = L.units_of(order[cell], lab)
        summ, cb, eb = L.summarize(units, att)
        draws[cell] = (cb, eb)
        c = cost[arm, cond]
        results.append({'config': cfg['name'], 'target': target, 'view': view, 'prompt': arm, 'condition': cond,
                        'episodes': len(units), 'customers': len({u['task'] for u in units}),
                        'positive_customers': len({u['task'] for u in units if u['y']}),
                        'positive_tasks': len({u['task_id'] for u in units if u['y']}),
                        'bytes_ratio': c['wire'] / c['raw_wire'], 'calls_ratio': c['calls'] / c['raw_calls'],
                        'template_overflow_rate': c['overflow'] / c['n'], **summ})
    return results, draws, cals


def paired(draws, a, b):
    out = {}
    for which, idx in (('core', 0), ('ext', 1)):
        d = draws[a][idx] - draws[b][idx]
        out[which] = {'difference': float(d[0]), 'ci95': [float(x) for x in np.nanquantile(d[1:], [.025, .975])]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', action='append', help='run only these configurations (partial output)')
    ap.add_argument('--merge', action='store_true', help='merge partial outputs into e10_crossfit_results.json')
    a = ap.parse_args()
    if a.merge:
        parts = [L.read(L.HERE / f"e10_part_{c['name']}.json") for c in L.FRONTIER]
        merged = dict(parts[0])
        for key in ('results', 'contrasts'):
            merged[key] = [x for p in parts for x in p[key]]
        merged['calibrations'] = {k: v for p in parts for k, v in p['calibrations'].items()}
        L.write(L.HERE / 'e10_crossfit_results.json', merged)
        for c in L.FRONTIER:
            (L.HERE / f"e10_part_{c['name']}.json").unlink()
        return
    ns, tools, base, tasks = L.load()
    rows, split = L.all_episodes()
    fold = folds_of(rows)
    fold_summary = []
    for k in range(K):
        us = {e['user'] for e in rows if fold[e['user']] == k}
        fold_summary.append({'fold': k, 'customers': len(us),
                             'cancel_positive_customers': len({e['user'] for e in rows if fold[e['user']] == k and e['has_cancel']}),
                             'return_positive_customers': len({e['user'] for e in rows if fold[e['user']] == k and e['has_return']})})
    print(fold_summary, flush=True)
    all_results = []; contrasts = []; cal_log = {}
    for cfg in [c for c in L.FRONTIER if not a.config or c['name'] in a.config]:
        primary = cfg['name'] == 'r4'
        conds = L.CONDITIONS if primary else ['raw', 'padding_only', 'shape_const']
        res, draws, cals = run_config(rows, fold, cfg, tools, base, conds, L.PROMPTS, log=lambda m: print(m, flush=True))
        all_results += res; cal_log[cfg['name']] = cals
        for target in L.ev.TARGETS:
            for view in ('dispatch', 'network'):
                for arm in L.PROMPTS:
                    contrasts.append({'config': cfg['name'], 'target': target, 'view': view, 'prompt': arm,
                                      'contrast': 'shape_const minus raw',
                                      **paired(draws, (target, view, arm, 'shape_const'), (target, view, arm, 'raw'))})
                contrasts.append({'config': cfg['name'], 'target': target, 'view': view, 'prompt': 'rules-baseline',
                                  'contrast': 'rules minus baseline under shape_const',
                                  **paired(draws, (target, view, 'rules', 'shape_const'), (target, view, 'baseline', 'shape_const'))})
        for r in res:
            if r['view'] == 'network' and r['condition'] in ('raw', 'shape_const'):
                print(cfg['name'], r['target'], r['prompt'], r['condition'], 'core %.3f %s ext %.3f auc %.3f/%.3f bytes %.2f calls %.2f' % (
                    r['core_ba'], [round(x, 3) for x in r['core_ba_ci95']], r['ext_ba'], r['core_auroc'],
                    r['sign_agnostic_auroc'], r['bytes_ratio'], r['calls_ratio']), flush=True)
    L.write(L.HERE / (f"e10_part_{a.config[0]}.json" if a.config else 'e10_crossfit_results.json'),
            {'design': 'customer-grouped stratified 5-fold cross-fitting; calibration and attackers fit on training folds only',
             'folds': fold_summary, 'fold_of_customer': fold, 'calibrations': cal_log,
             'results': all_results, 'contrasts': contrasts, 'bootstrap_draws': 2000,
             'interval_scope': 'Customer-cluster bootstrap over pooled out-of-fold predictions; conditional on fitted attackers.',
             'r4_calibration_sha256': L.sha(L.R4 / 'calibration.json')})


if __name__ == '__main__':
    main()
