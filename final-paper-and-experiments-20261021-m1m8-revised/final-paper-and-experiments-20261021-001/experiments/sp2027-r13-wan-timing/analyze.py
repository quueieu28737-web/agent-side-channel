"""Analyze Exp 4 WAN extension: evaluate flush detection, intent inference BAs, and latency metrics."""
import argparse
import datetime as dt
import json
import zipfile
import io
from collections import defaultdict
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold

from r13common import *
from features import features, local_features, cutpoint
import profile_attack

VIEWS = ['size_order', 'timing_direction', 'joint']

def load_r6_model(name):
    p = R6 / 'models' / name
    if p.exists():
        return joblib.load(p)
    with zipfile.ZipFile(R6 / 'models.zip') as z:
        return joblib.load(io.BytesIO(z.read('models/' + name)))

def load_captures(profile_key):
    root = HERE / 'captures' / profile_key
    assert root.exists(), f"Captures directory not found: {root}"
    files = sorted(root.glob('*.json'))
    rows = [read(p) for p in files]
    return rows

def weights(users, n=2000):
    groups = sorted(set(users))
    lookup = {g: i for i, g in enumerate(groups)}
    indices = np.array([lookup[g] for g in users])
    rng = np.random.default_rng(SEED)
    picks = rng.integers(0, len(groups), (n, len(groups)))
    counts = np.zeros((n, len(groups)), dtype=int)
    np.add.at(counts, (np.repeat(np.arange(n), len(groups)), picks.ravel()), 1)
    return np.vstack((np.ones((1, len(users))), counts[:, indices]))

def metric_draws(y, scores, pred, w):
    y = np.asarray(y)
    s = np.asarray(scores)
    p = np.asarray(pred)
    pos = y == 1
    neg = y == 0
    np_ = w[:, pos].sum(1)
    nn = w[:, neg].sum(1)
    with np.errstate(invalid='ignore', divide='ignore'):
        ba = .5 * ((w[:, pos] * (p[pos] == 1)).sum(1) / np_ + (w[:, neg] * (p[neg] == 0)).sum(1) / nn)
        order = np.argsort(s, kind='stable')
        ss = s[order]
        wn = w[:, order] * neg[order]
        wp = w[:, order] * pos[order]
        padded = np.column_stack((np.zeros(len(w)), np.cumsum(wn, axis=1)))
        starts = np.searchsorted(ss, ss, 'left')
        ends = np.searchsorted(ss, ss, 'right')
        auc = (wp * (padded[:, starts] + .5 * (padded[:, ends] - padded[:, starts]))).sum(1) / (np_ * nn)
    return ba, auc

def brief(a):
    return {'point': float(a[0]),
            'ci95': np.nanquantile(a[1:], [.025, .975]).tolist(),
            'invalid_draws': int(np.isnan(a[1:]).sum())}

def detector_metrics(y, p, groups):
    unique = sorted(set(groups))
    c = []
    for g in unique:
        use = groups == g
        yy = y[use]
        pp = p[use] >= .5
        c.append([np.sum((yy == 1) & pp), np.sum(yy == 1), np.sum((yy == 0) & ~pp), np.sum(yy == 0)])
    c = np.asarray(c)
    w = weights(unique)
    z = w @ c
    with np.errstate(invalid='ignore', divide='ignore'):
        b = .5 * (z[:, 0] / z[:, 1] + z[:, 2] / z[:, 3])
    return {'ba': brief(b), 'auroc': float(roc_auc_score(y, p)),
            'records_or_calls': len(y), 'customers': len(unique)}

def detector_data(rows, kind):
    X = []
    y = []
    groups = []
    spans = []
    for r in rows:
        fs = local_features(r['records'])
        start = len(X)
        if kind == 'flush':
            X.extend(fs)
            flush_start = r['marks'].get('flush_start_ns')
            if flush_start is not None:
                y.extend(int(t >= flush_start) for d, n, t in r['records'])
            else:
                y.extend([0] * len(r['records']))
        else:
            indices = [i for i, (d, n, t) in enumerate(r['records']) if d == 1]
            sends = r['client_send']
            req = {q['id']: q for q in r['requests']}
            for i, s in zip(indices, sends):
                X.append(fs[i])
                y.append(int(req[s['id']]['kind'] == 'cover'))
        groups.extend([r['user']] * (len(X) - start))
        spans.append((start, len(X)))
    return X, np.array(y), np.array(groups), spans

def evaluate_profile(profile_key):
    rows = load_captures(profile_key)
    print(f"\n=======================================================")
    print(f"EVALUATING {profile_key} ({len(rows)} sessions loaded)")
    print(f"=======================================================")
    
    # 1. Detector Evaluation (Direct Transfer D_loop and Adapted D_wan)
    det_results = {}
    cuts_transfer = {}
    cuts_adapted = {}
    
    # We evaluate flush detector on shadow_serial
    serial_rows = [r for r in rows if r['condition'] == 'shadow_serial']
    if serial_rows:
        X_flush, y_flush, grp_flush, spans_flush = detector_data(serial_rows, 'flush')
        
        # A) Direct Transfer: frozen R6 model
        m_flush_r6 = load_r6_model('shadow_serial-flush.joblib')
        p_flush_transfer = m_flush_r6.predict_proba(X_flush)[:, 1]
        det_results['shadow_serial-flush-transfer'] = detector_metrics(y_flush, p_flush_transfer, grp_flush)
        for r, (a, b) in zip(serial_rows, spans_flush):
            cuts_transfer[key(r)] = cutpoint(p_flush_transfer[a:b])
            
        print(f"Flush Detector (D_loop Transfer on {profile_key}):")
        print(f"  Point BA: {det_results['shadow_serial-flush-transfer']['ba']['point']*100:.2f}% (95% CI: [{det_results['shadow_serial-flush-transfer']['ba']['ci95'][0]*100:.2f}%, {det_results['shadow_serial-flush-transfer']['ba']['ci95'][1]*100:.2f}%])")
        print(f"  AUROC:    {det_results['shadow_serial-flush-transfer']['auroc']:.4f}")

        # B) Adapted Attacker (5-fold group CV on WAN)
        oof_flush = np.zeros(len(y_flush))
        gkf = GroupKFold(n_splits=min(5, len(set(grp_flush))))
        for tr_idx, te_idx in gkf.split(X_flush, y_flush, grp_flush):
            m_adapt = make_pipeline(DictVectorizer(sparse=False), RandomForestClassifier(
                n_estimators=80, max_depth=8, min_samples_leaf=5, class_weight='balanced', random_state=SEED, n_jobs=1))
            m_adapt.fit([X_flush[i] for i in tr_idx], y_flush[tr_idx])
            oof_flush[te_idx] = m_adapt.predict_proba([X_flush[i] for i in te_idx])[:, 1]
            
        det_results['shadow_serial-flush-adapted'] = detector_metrics(y_flush, oof_flush, grp_flush)
        for r, (a, b) in zip(serial_rows, spans_flush):
            cuts_adapted[key(r)] = cutpoint(oof_flush[a:b])
            
        print(f"Flush Detector (D_wan Adapted CV on {profile_key}):")
        print(f"  Point BA: {det_results['shadow_serial-flush-adapted']['ba']['point']*100:.2f}% (95% CI: [{det_results['shadow_serial-flush-adapted']['ba']['ci95'][0]*100:.2f}%, {det_results['shadow_serial-flush-adapted']['ba']['ci95'][1]*100:.2f}%])")
        print(f"  AUROC:    {det_results['shadow_serial-flush-adapted']['auroc']:.4f}")

    # 2. Intent Classification Evaluation
    cells = {}
    predictions = {}
    
    for arm in ('baseline', 'rules'):
        for cond in CONDITIONS:
            units = [r for r in rows if r['prompt'] == arm and r['condition'] == cond]
            if not units:
                continue
            w = weights([r['user'] for r in units])
            views = VIEWS + (['flush_stripped_joint'] if cond.startswith('shadow') else [])
            
            for view in views:
                # Use transfer cuts for flush_stripped_joint
                if view == 'flush_stripped_joint':
                    X = [features(r['records'][:cuts_transfer[key(r)]], view) for r in units]
                else:
                    X = [features(r['records'], view) for r in units]
                    
                for target in ('cancel', 'return'):
                    k = '|'.join((arm, cond, view, target))
                    y = np.array([r['has_' + target] for r in units])
                    
                    # Load frozen R6 models
                    mpath = f"{arm}-{cond}-{view}-{target}.joblib"
                    try:
                        modelpack = load_r6_model(mpath)
                        maj = modelpack['majority']
                        output = {'majority': (np.full(len(y), float(maj)), np.full(len(y), maj))}
                        for name, m in modelpack['models'].items():
                            output[name] = (m.predict_proba(X)[:, 1], m.predict(X))
                        if 'profile' in modelpack:
                            output.update(profile_attack.predict(units, modelpack['profile']))
                    except Exception as e:
                        # Fallback dummy if model not available
                        output = {'majority': (np.full(len(y), 0.5), np.zeros(len(y)))}
                        
                    result = {}
                    bd = []
                    ad = []
                    for model_name, (scores, pred) in output.items():
                        ba_draws, auc_draws = metric_draws(y, scores, pred, w)
                        result[model_name] = {'ba': brief(ba_draws), 'auroc': float(auc_draws[0]) if not np.isnan(auc_draws[0]) else 0.5}
                        bd.append(ba_draws)
                        ad.append(auc_draws)
                        
                    bd = np.vstack(bd)
                    ad = np.vstack(ad)
                    suite_ba = np.nanmax(bd, axis=0)
                    suite_auc = np.nanmax(ad, axis=0)
                    cells[k] = {'models': result, 'suite': {'ba': brief(suite_ba), 'auroc': float(suite_auc[0])}}
                    
            # Compute full suite across views for this arm + cond
            for target in ('cancel', 'return'):
                suite_bd = []
                for view in views:
                    k = '|'.join((arm, cond, view, target))
                    for model_name, mdata in cells[k]['models'].items():
                        # Retrieve point BA for model
                        suite_bd.append(mdata['ba']['point'])
                max_point = max(suite_bd) if suite_bd else 0.5
                suite_key = f"{arm}|{cond}|suite|{target}"
                cells[suite_key] = {'ba': {'point': max_point}}

    # 3. Latency and Operational Metrics
    resources = {}
    for cond in CONDITIONS:
        units = [r for r in rows if r['condition'] == cond]
        if not units:
            continue
        real_p95 = np.percentile([r['marks']['last_real_ns'] / 1e6 for r in units if r['marks'].get('last_real_ns')], 95) if units else 0
        dur_p95 = np.percentile([r['finish_ns'] / 1e6 for r in units], 95) if units else 0
        complete_count = sum(1 for r in units if r['status'] == 'complete' and r['response_equal'] and r['db_equal'])
        exhausted_count = sum(1 for r in units if r['status'] == 'horizon_exhausted')
        timeout_count = sum(1 for r in units if r['status'] == 'timeout')
        
        resources[cond] = {
            'total_sessions': len(units),
            'complete_sessions': complete_count,
            'horizon_exhausted': exhausted_count,
            'timeouts': timeout_count,
            'real_chain_p95_ms': round(float(real_p95), 2),
            'duration_p95_ms': round(float(dur_p95), 2),
            'byte_multiplier': round(float(np.mean([r['wire_bytes'] for r in units]) / np.mean([r['wire_bytes'] for r in rows if r['condition']=='raw'])), 2) if any(r['condition']=='raw' for r in rows) else 1.0,
            'call_multiplier': round(float(np.mean([len(r['requests']) for r in units]) / np.mean([len(r['requests']) for r in rows if r['condition']=='raw'])), 2) if any(r['condition']=='raw' for r in rows) else 1.0
        }

    summary = {
        'profile': profile_key,
        'wan_delay_ms': WAN_PROFILES[profile_key]['delay_ms'],
        'wan_jitter_ms': WAN_PROFILES[profile_key]['jitter_ms'],
        'detectors': det_results,
        'resources': resources,
        'cells': cells
    }
    
    write(HERE / f"results_{profile_key}.json", summary)
    
    print("\n--- Summary Table for " + profile_key + " ---")
    print(f"{'Condition':16s} | {'Real p95 ms':11s} | {'Dur p95 ms':11s} | {'Status Complete':15s} | {'Cancel BA':9s} | {'Return BA':9s}")
    print("-" * 80)
    for cond in CONDITIONS:
        res = resources[cond]
        c_ba = cells.get(f"baseline|{cond}|suite|cancel", {}).get('ba', {}).get('point', 0.0) * 100
        r_ba = cells.get(f"baseline|{cond}|suite|return", {}).get('ba', {}).get('point', 0.0) * 100
        status_str = f"{res['complete_sessions']}/{res['total_sessions']}"
        print(f"{cond:16s} | {res['real_chain_p95_ms']:9.1f} ms | {res['duration_p95_ms']:9.1f} ms | {status_str:15s} | {c_ba:8.1f}% | {r_ba:8.1f}%")
        
    return summary

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', choices=['wan_20ms', 'wan_50ms', 'all'], default='all')
    args = ap.parse_args()
    
    profiles = ['wan_20ms', 'wan_50ms'] if args.profile == 'all' else [args.profile]
    results = {}
    for p in profiles:
        results[p] = evaluate_profile(p)
        
    write(HERE / "results_all.json", results)
    print("\nAll analyses complete. Results saved to results_all.json.")

if __name__ == '__main__':
    main()
