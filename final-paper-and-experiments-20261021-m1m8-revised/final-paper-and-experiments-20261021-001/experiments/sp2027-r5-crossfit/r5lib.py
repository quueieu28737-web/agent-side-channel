"""Shared R5 machinery: generic training-only calibration, online shadow cover,
analytic TLS sessions and the fixed + extended attack suites.

Nothing here calls a model. All inputs are the immutable R4 snapshot episodes.
The R4 configuration reproduces R4's frozen calibration byte-for-byte when it
is given R4's training episodes (checked by verify_r5.py).
"""
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R4 = HERE.parent / 'sp2027-r4-snapshot-20261023'
sys.path.insert(0, str(R4))
from common import PROMPTS, REPEATS, read, write, sha, load, old, inference_fingerprint  # noqa: E402
from e6_e7_retail_cover import invoke  # noqa: E402
import e67_eval as ev  # noqa: E402
import reanalyze as stats  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
import tlsmodel  # noqa: E402

SEED = 20261023
CONDITIONS = ['raw', 'padding_only', 'shape_only', 'shape_const']

# The R4 frozen operating point and the pre-declared R5 alternatives.
R4_CONFIG = {'name': 'r4', 'scope': 'all', 'emit_p': .6, 'framing': 'const', 'resp_q': .95}
FRONTIER = [
    R4_CONFIG,
    {'name': 'r4_bucket', 'scope': 'all', 'emit_p': .6, 'framing': 'bucket1024', 'resp_q': .95},
    {'name': 'r4_cap80', 'scope': 'all', 'emit_p': .6, 'framing': 'const', 'resp_q': .80},
    {'name': 'writes', 'scope': 'writes', 'emit_p': .6, 'framing': 'const', 'resp_q': .95},
    {'name': 'writes_cap80', 'scope': 'writes', 'emit_p': .6, 'framing': 'const', 'resp_q': .80},
    {'name': 'writes_bucket', 'scope': 'writes', 'emit_p': .6, 'framing': 'bucket1024', 'resp_q': .95},
]

EXT_MODELS = {
    'rf': lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight='balanced',
                                         random_state=0, n_jobs=1),
    'knn': lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=7, weights='distance')),
}


FULL = HERE.parent / 'sp2027-r4-full-20261023'
COHORT = os.environ.get('R5_COHORT', 'full')  # 'full' = completed 690-run cohort; 'snapshot' = 660-run R4 grid


def all_episodes(cohort=None):
    """Complete-grid episodes. Returns (rows, split) with split = {'train', 'test'} task ids."""
    cohort = cohort or COHORT
    if cohort == 'snapshot':
        split = read(R4 / 'analysis_split.json')
    else:
        frozen = read(R4 / 'split.json'); split = {'train': frozen['train'], 'test': frozen['test']}
    rows = []
    for arm in PROMPTS:
        for tid in split['train'] + split['test']:
            for rep in REPEATS:
                rel = Path('runs') / arm / f'task-{tid:03d}-repeat-{rep}' / 'episode.json'
                p = R4 / rel if (R4 / rel).exists() else FULL / 'delta' / rel
                e = read(p)
                assert e['inference_fingerprint'] == inference_fingerprint()
                assert (e['task'], e['repeat'], e['prompt']) == (tid, rep, arm)
                rows.append(e)
    return rows, split


def fit_calibration(rows, tools, base, cfg):
    """R4's fit_calibration generalized by scope and response-cap quantile."""
    names = set(tools) if cfg['scope'] == 'all' else set(ev.WRITES)
    tmpl = Counter(); donors = defaultdict(list); lengths = []
    for e in rows:
        counts = Counter(c['name'] for c in e['calls'] if c['name'] in tools)
        for name, n in counts.items():
            tmpl[name] = max(tmpl[name], n)
        for c in e['calls']:
            lengths.append((c['req'], c['resp']))
            if c['name'] in tools:
                donors[c['name']].append({'task': e['task'], 'user': e['user'], 'name': c['name'], 'kwargs': c['kwargs']})
    donors = {v: list({json.dumps(d, sort_keys=True): d for d in ds}.values()) for v, ds in sorted(donors.items())}
    for v, ds in donors.items():
        for d in ds:
            req = json.dumps({'name': v, 'arguments': d['kwargs']}, sort_keys=True)
            resp = invoke(tools, old.fast_clone(base), v, d['kwargs'])
            lengths.append((len(req.encode()), len(resp.encode())))
    tmpl = {k: v for k, v in sorted(tmpl.items()) if k in names}
    return {'template': tmpl, 'donors': {k: v for k, v in donors.items() if k in names},
            'caps': {'req': int(math.ceil((max(q for q, r in lengths) + 4) / 256) * 256),
                     'resp': int(math.ceil((np.quantile([r for q, r in lengths], cfg['resp_q']) + 4) / 1024) * 1024)},
            'shape_emit_probability': cfg['emit_p'], 'calibration_lengths': len(lengths), 'scope': cfg['scope']}


def cover_episode(e, cal, tools, base):
    """Identical to R4 defense.cover_episode (same RNG stream), template-generic."""
    rng = random.Random(20261021 + e['task'] * 100003 + e['repeat'] * 7919 + (e['prompt'] == 'rules') * 13)
    seen = Counter(); emitted = Counter(); calls = []; missing = Counter()
    pools = {v: [d for d in ds if d['user'] != e['user']] for v, ds in cal['donors'].items()}
    shadow = old.fast_clone(base)

    def deficits():
        return {v: n - seen[v] - emitted[v] for v, n in cal['template'].items() if n > seen[v] + emitted[v]}

    def add(v):
        if not pools.get(v):
            missing[v] += 1; return
        d = rng.choice(pools[v]); resp = invoke(tools, shadow, v, d['kwargs'])
        req = json.dumps({'name': v, 'arguments': d['kwargs']}, sort_keys=True)
        calls.append({'name': v, 'kind': 'cover', 'req_text': req, 'resp_text': resp, 'req': len(req.encode()),
                      'resp': len(resp.encode()), 'err': resp.startswith('Error:')})
        emitted[v] += 1
    for c in e['calls']:
        df = deficits()
        if df and rng.random() < cal['shape_emit_probability']:
            add(rng.choices(list(df), weights=list(df.values()))[0])
        seen[c['name']] += 1; calls.append(dict(c, kind='real'))
    rest = [v for v, n in deficits().items() for _ in range(n)]
    rng.shuffle(rest)
    for v in rest:
        add(v)
    counts = Counter(c['name'] for c in calls)
    scoped = [v for v in counts if cal.get('scope', 'all') == 'all' or v in cal['template']]
    return calls, {'template_overflow': any(counts[v] > cal['template'].get(v, 0) for v in scoped),
                   'missing_donor_attempts': dict(missing)}


def make_sessions(e, cal, cfg, tools, base, conditions=CONDITIONS):
    """Return {condition: session} for one episode under one calibration."""
    shaped = None
    out = {}
    for cond in conditions:
        if cond.startswith('shape') and shaped is None:
            shaped, flags = cover_episode(e, cal, tools, base)
        calls = shaped if cond.startswith('shape') else [dict(c, kind='real') for c in e['calls']]
        fr = cfg['framing'] if cond in ('padding_only', 'shape_const') else 'raw'
        lite = [{k: c[k] for k in ('name', 'kind', 'req', 'resp', 'err')} for c in calls]
        recs = tlsmodel.session(lite, fr, cal['caps'])
        out[cond] = {k: e[k] for k in ('task', 'repeat', 'prompt', 'user', 'has_cancel', 'has_return', 'native_reward')}
        out[cond].update({'condition': cond, 'calls': lite, 'records': recs,
                          'wire': sum(n + 5 for d, n in recs),
                          'template_overflow': bool(flags['template_overflow']) if cond.startswith('shape') else False,
                          '_texts': calls})
    return out


def attack_suite(tr, te, tr_raw, lab, verb, view, verbs, extended=True):
    """Fit on training sessions only; return {attacker: (scores, preds)} for test.

    The core suite is exactly R4's. Extended learners are reported separately.
    """
    feat = (lambda s: ev.disp_features(s['calls'], verbs)) if view == 'dispatch' else (lambda s: ev.net_features(s['records']))
    ytr = np.array([s[lab] for s in tr])
    Xtr = [feat(s) for s in tr]; Xte = [feat(s) for s in te]
    att = {}
    maj = int(ytr.mean() >= .5)
    att['majority'] = (np.full(len(te), float(maj)), np.full(len(te), maj))

    def fit(Xa, ya, Xb, model, table):
        if len(set(ya)) < 2:
            return np.full(len(Xb), float(ya[0]))
        mdl = table[model](); mdl.fit(np.asarray(Xa, float), ya)
        return mdl.predict_proba(np.asarray(Xb, float))[:, 1]
    sc = fit([feat(s) for s in tr_raw], np.array([s[lab] for s in tr_raw]), Xte, 'gboost', ev.MODELS)
    att['D0_gboost'] = (sc, (sc >= .5).astype(int))
    for m in ev.MODELS:
        sc = fit(Xtr, ytr, Xte, m, ev.MODELS); att['D2_' + m] = (sc, (sc >= .5).astype(int))
    if extended:
        for m in EXT_MODELS:
            sc = fit(Xtr, ytr, Xte, m, EXT_MODELS); att['ext_D2_' + m] = (sc, (sc >= .5).astype(int))

    def count_rule(ctr, cte):
        ctr = np.asarray(ctr); cte = np.asarray(cte); best = (-1, 0)
        for th in range(int(ctr.max(initial=0)) + 2):
            pred = ctr >= th
            ba = .5 * (np.mean(pred[ytr == 1]) + np.mean(~pred[ytr == 0]))
            if ba > best[0]:
                best = (ba, th)
        return cte.astype(float), (cte >= best[1]).astype(int)
    if view == 'dispatch':
        att['D2_count_rule'] = count_rule([sum(c['name'] == verb for c in s['calls']) for s in tr],
                                          [sum(c['name'] == verb for c in s['calls']) for s in te])
    else:
        full = defaultdict(Counter); req = defaultdict(Counter); freq = Counter()
        for s in tr:
            for c, (a, b) in zip(s['calls'], ev.exchanges(s['records'])):
                full[a, b][c['name']] += 1; req[a][c['name']] += 1; freq[c['name']] += 1
        majority = freq.most_common(1)[0][0] if freq else 'unknown'
        fm = {k: v.most_common(1)[0][0] for k, v in full.items()}; rm = {k: v.most_common(1)[0][0] for k, v in req.items()}
        dec = lambda s: [{'name': fm.get((a, b), rm.get(a, majority)), 'resp': b} for a, b in ev.exchanges(s['records'])]
        dtr = [dec(s) for s in tr]; dte = [dec(s) for s in te]
        sc = fit([ev.disp_features(c, verbs) for c in dtr], ytr, [ev.disp_features(c, verbs) for c in dte], 'gboost', ev.MODELS)
        att['network_decode_gboost'] = (sc, (sc >= .5).astype(int))
        att['network_decode_count_rule'] = count_rule([sum(c['name'] == verb for c in cs) for cs in dtr],
                                                      [sum(c['name'] == verb for c in cs) for cs in dte])
        if extended:
            sc = fit([ev.disp_features(c, verbs) for c in dtr], ytr, [ev.disp_features(c, verbs) for c in dte], 'rf', EXT_MODELS)
            att['ext_network_decode_rf'] = (sc, (sc >= .5).astype(int))
    return att


def summarize(units, attacks, n=2000):
    """Suite maxima (core and extended) with common customer-cluster bootstrap draws."""
    per = {}; core_b = []; core_a = []; ext_b = []; ext_a = []; two = []
    for name, (sc, pr) in attacks.items():
        ba, auc = stats.distributions(units, np.asarray(sc, float), np.asarray(pr), n)
        per[name] = {'ba': float(ba[0]), 'auroc': float(auc[0])}
        (ext_b if name.startswith('ext_') else core_b).append(ba)
        (ext_a if name.startswith('ext_') else core_a).append(auc)
        two.append(np.maximum(auc, 1 - auc))
    cb = np.nanmax(core_b, 0); ca = np.nanmax(core_a, 0)
    eb = np.nanmax(core_b + ext_b, 0); ea = np.nanmax(core_a + ext_a, 0)
    tw = np.nanmax(two, 0)
    q = lambda v: [float(x) for x in np.nanquantile(v[1:], [.025, .975])]
    out = {'core_ba': float(cb[0]), 'core_ba_ci95': q(cb), 'core_auroc': float(ca[0]),
           'ext_ba': float(eb[0]), 'ext_ba_ci95': q(eb), 'ext_auroc': float(ea[0]),
           'sign_agnostic_auroc': float(tw[0]), 'sign_agnostic_auroc_ci95': q(tw),
           'attackers': per, 'invalid_draws': int(np.isnan(cb[1:]).sum())}
    out['criterion_core'] = stats.criterion(out['core_ba'], out['core_ba_ci95'], out['core_auroc'])
    out['criterion_ext'] = stats.criterion(out['ext_ba'], out['ext_ba_ci95'], out['ext_auroc'])
    return out, cb, eb


def units_of(sessions, lab):
    return [{'task': s['user'], 'task_id': s['task'], 'seed': s['repeat'], 'y': s[lab]} for s in sessions]
