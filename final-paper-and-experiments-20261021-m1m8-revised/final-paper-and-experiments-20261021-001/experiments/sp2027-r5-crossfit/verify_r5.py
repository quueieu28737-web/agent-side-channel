"""Read-only R5 verifier. Writes validation_r5.json.

1. Analytic TLS model equals all 2,640 R4 and 2,760 full-cohort socket-measured sessions.
2. Generic calibration reproduces R4's frozen calibration from R4 training episodes.
3. Generic cover + sessions reproduce every R4 session (calls, kinds, records, flags).
4. The R5 attack pipeline on the frozen split reproduces R4 and full-cohort results.json
   (suite BA, interval and AUROC for every target/view/prompt/condition).
5. Fresh loopback TLS 1.2 captures (tlslab) equal the analytic model on new
   cross-fitted sessions, including cover calls calibrated on other folds.
6. R4 snapshot inputs are byte-identical to their recorded hashes.
"""
import random
import tempfile
from pathlib import Path

import numpy as np

import r5lib as L
from e10_crossfit import folds_of, run_config
from e6_e7_retail_cover import frame
import tlslab


def main():
    ns, tools, base, tasks = L.load()
    rows, split = L.all_episodes()
    receipt = {}
    R4S = L.read(L.R4 / 'sessions.json'); ref = L.read(L.R4 / 'calibration.json')
    FS = L.read(L.FULL / 'sessions.json')
    receipt['tls_model_vs_r4'] = L.tlsmodel.validate_against_r4(R4S, ref['caps'])
    receipt['tls_model_vs_full_cohort'] = L.tlsmodel.validate_against_r4(FS, ref['caps'])
    assert receipt['tls_model_vs_r4']['mismatches'] == 0 and receipt['tls_model_vs_full_cohort']['mismatches'] == 0

    train = [e for e in rows if e['task'] in set(split['train'])]
    cal = L.fit_calibration(train, tools, base, L.R4_CONFIG)
    keys = ('template', 'donors', 'caps', 'calibration_lengths', 'shape_emit_probability')
    receipt['calibration_reproduced'] = all(cal[k] == ref[k] for k in keys)
    assert receipt['calibration_reproduced']

    S = {(s['prompt'], s['task'], s['repeat'], s['condition']): s for s in FS}
    assert all(S[s['prompt'], s['task'], s['repeat'], s['condition']]['records'] == s['records'] for s in R4S)
    bad = 0
    for e in rows:
        for c, x in L.make_sessions(e, cal, L.R4_CONFIG, tools, base).items():
            r = S[e['prompt'], e['task'], e['repeat'], c]
            same = ([tuple(a) for a in r['records']] == x['records'] and
                    [(q['name'], q['kind'], q['req'], q['resp']) for q in r['calls']] ==
                    [(q['name'], q['kind'], q['req'], q['resp']) for q in x['calls']])
            if c.startswith('shape'):
                same = same and r['template_flags']['template_overflow'] == x['template_overflow']
            bad += not same
    receipt['sessions_reproduced'] = {'sessions': len(rows) * 4, 'mismatches': bad}
    assert bad == 0

    receipt['frozen_split_results_reproduced'] = {}
    for cohort, ref_dir in (('full', L.FULL), ('snapshot', L.R4)):
        crow, csplit = L.all_episodes(cohort)
        heldout = {e['user']: (0 if e['task'] not in set(csplit['train']) else 1) for e in crow}
        res, _, _ = run_config(crow, heldout, L.R4_CONFIG, tools, base, L.CONDITIONS, L.PROMPTS,
                               extended=False, eval_folds=[0], log=lambda m: None)
        ref_res = {(r['target'], r['view'], r['prompt'], r['condition']): r for r in L.read(ref_dir / 'results.json')['results']}
        worst = 0.0
        for r in res:
            o = ref_res[r['target'], r['view'], r['prompt'], r['condition']]
            worst = max(worst, abs(r['core_ba'] - o['suite_ba']), abs(r['core_auroc'] - o['suite_auroc']),
                        *[abs(a - b) for a, b in zip(r['core_ba_ci95'], o['suite_ba_ci95'])])
        receipt['frozen_split_results_reproduced'][cohort] = {'cells': len(res), 'max_abs_difference': worst}
        assert len(res) == 32 and worst < 1e-12, (cohort, worst)

    fold = folds_of(rows); rng = random.Random(L.SEED); checked = 0
    with tempfile.TemporaryDirectory() as tmp:
        ctx = tlslab.make_contexts(Path(tmp), '1.2')
        for k in range(2):
            cal_k = L.fit_calibration([e for e in rows if fold[e['user']] != k], tools, base, L.R4_CONFIG)
            for e in rng.sample([e for e in rows if fold[e['user']] == k], 15):
                for cond, s in L.make_sessions(e, cal_k, L.R4_CONFIG, tools, base).items():
                    fr = 'const' if cond in ('padding_only', 'shape_const') else 'raw'
                    ex = [(frame(c['req_text'], fr, True, cal_k['caps']), frame(c['resp_text'], fr, False, cal_k['caps']))
                          for c in s['_texts']]
                    measured = [tuple(x) for x in tlslab.run_session(*ctx, ex)]
                    assert measured == s['records'], (e['task'], cond)
                    checked += 1
    receipt['fresh_socket_captures_match_model'] = checked
    sums = L.read(L.HERE.parent.parent / 'SHA256SUMS.json')['files']
    receipt['r4_input_hashes'] = {}
    for n in ('calibration.json', 'split.json', 'analysis_split.json', 'sessions.json', 'results.json', 'protocol.json'):
        digest = L.sha(L.R4 / n)
        assert sums['experiments/sp2027-r4-snapshot-20261023/' + n] == digest, n
        receipt['r4_input_hashes'][n] = digest
    outputs = [p + n for p in ('', 'snapshot-660/') for n in
               ('e10_crossfit_results.json', 'e11_selection.json', 'e11_heldout_results.json', 'e12_localization_results.json')]
    receipt['output_hashes'] = {n: L.sha(L.HERE / n) for n in outputs if (L.HERE / n).exists()}
    receipt['status'] = 'pass'
    L.write(L.HERE / 'validation_r5.json', receipt)
    print(receipt)


if __name__ == '__main__':
    main()
