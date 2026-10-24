"""R8 read-only saved-result audit. No model fitting, inference, or old-file writes."""
import csv
import hashlib
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
E = P / 'experiments'

def read(rel):
    return json.loads((E / rel).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

r6 = read('sp2027-r6-timing/results.json')
r7 = read('sp2027-r7-robustness/results.json')
common = read('sp2027-r7-robustness/common-suite.json')
pred = read('sp2027-r6-timing/detector_predictions.json')
conditions = ['raw', 'padding', 'walkie_talkie', 'shadow_serial', 'shadow_parallel2', 'tunnel_2ms', 'tunnel_5ms']
rows = []
for arm in ['baseline', 'rules']:
    for cond in conditions:
        for target in ['cancel', 'return']:
            key = '|'.join([arm, cond, target])
            c = common['cells'][key]
            v = r7['resources'][arm + '|' + cond]
            rows.append(dict(prompt=arm, condition=cond, target=target,
                common_ba=c['ba']['point'], common_ba_ci95=c['ba']['ci95'],
                common_auroc=c['auroc']['point'], common_criterion=c['criterion'],
                full_union_ba=r7['cells'][key]['ba']['point'],
                full_union_suite_size=r7['cells'][key]['suite_size'], **v))

comparisons = []
for arm in ['baseline', 'rules']:
    for a in conditions[2:]:
        for b in conditions[2:]:
            if a == b:
                continue
            ar = [v for v in rows if v['prompt'] == arm and v['condition'] == a]
            br = [v for v in rows if v['prompt'] == arm and v['condition'] == b]
            va = [ar[0]['wire_ratio'], ar[0]['call_ratio']] + [v['common_ba'] for v in ar]
            vb = [br[0]['wire_ratio'], br[0]['call_ratio']] + [v['common_ba'] for v in br]
            if all(x <= y for x, y in zip(va, vb)) and any(x < y for x, y in zip(va, vb)):
                comparisons.append(dict(prompt=arm, lower_point=a, higher_point=b,
                    dimensions=['bytes', 'tool dispatches', 'cancel BA', 'return BA'],
                    scope='Descriptive saved point estimates only; not statistical or deployment dominance; clocks excluded'))

detectors = {}
for k, d in pred.items():
    y = d['y']
    detectors[k] = dict(r6['detectors'][k], positive_labels=sum(y), negative_labels=len(y)-sum(y),
        episodes=len(d['units']), labels='after flush_start_ns' if k.endswith('flush') else 'cover request',
        unit='TLS record' if k.endswith('flush') else 'encrypted request')
flush = {k: v for k, v in r6['cells'].items() if 'flush_stripped_joint' in k}
inputs = [
    'sp2027-r6-timing/results.json', 'sp2027-r6-timing/predictions.json',
    'sp2027-r6-timing/detector_predictions.json', 'sp2027-r6-timing/training_cuts.json',
    'sp2027-r6-timing/test_cuts.json', 'sp2027-r6-timing/analyze.py',
    'sp2027-r6-timing/features.py', 'sp2027-r6-timing/experiment.py',
    'sp2027-r6-timing/attacker_freeze.json',
    'sp2027-r7-robustness/results.json', 'sp2027-r7-robustness/common-suite.json',
    'sp2027-r7-robustness/adapters.py', 'sp2027-r7-robustness/run.py',
    'sp2027-r7-robustness/IMPLEMENTATION.md', 'sp2027-r7-robustness/ERRATA.md',
    'sp2027-r4-full-20261023/results.json',
    'sp2027-r5-crossfit/e10_crossfit_results.json',
    'sp2027-r5-crossfit/e10_crossfit.py',
    'sp2027-r7-agent-extension/network_results.json',
    'sp2027-r7-agent-extension/compact_manifest.json',
    'sp2027-r2/e5_streaming_results.json', 'sp2027-r2/make_tables.py', 'sp2027-r2/e5_streaming.py',
]
e5 = read('sp2027-r2/e5_streaming_results.json')
cap_rows = [r for r in e5 if r['target'] == 'T1' and r['policy'] in ['buffered_raw', 'buffered_cap']]
write('defense-self-audit.json', dict(
    kind='R8 descriptive audit from complete saved result objects; no fitting or new LLM calls',
    common_attackers=common['common_attackers'], matched_rows=rows,
    descriptive_point_dominance=comparisons, detector_denominators=detectors,
    saved_flush_then_intent=flush,
    r6_response_state_checks=r6['resources'],
    absolute_gate='upper 95% suite BA < .60 AND suite point AUROC < .65',
    inference_scope='Action-labelled cancel/return trajectory targets, not unobserved psychological intent',
    utility_scope='Inherited native reward is not defended live-planner utility; logical checks are separate',
    additional_flush_fit_executed=False,
    e5_cap_version_rows=cap_rows,
    e5_denominators='Byte means/ratios: all 48 saved outputs, source loops over items; binary accuracy: 24 heldout outputs / 12 topics; ID: 48-output closed world',
    input_sha256={s: sha(E / s) for s in inputs}, code_sha256=sha(Path(__file__))))

buf = io.StringIO(newline='')
writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
writer.writeheader()
writer.writerows(rows)
(HERE / 'defense-self-audit.csv').write_text(buf.getvalue(), encoding='utf-8', newline='')

md = ['# R8 matched-seven saved-result tables', '',
      'All values below are descriptive. CI in percent. Every row uses 138 episodes / 24 test customers per prompt. Measured and simulated latency must not be compared as a deployment ranking.', '',
      '| Prompt | Condition | Cancel BA [CI] / AUC | Return BA [CI] / AUC | Bytes × | Calls × | Last-real p95 ms | Finish p95 ms | Evidence |',
      '|---|---|---|---|---:|---:|---:|---:|---|']
for arm in ['baseline', 'rules']:
    for cond in conditions:
        cc, rr = [v for v in rows if v['prompt'] == arm and v['condition'] == cond]
        def metric(v):
            lo, hi = v['common_ba_ci95']
            return f"{100*v['common_ba']:.4f} [{100*lo:.4f}, {100*hi:.4f}] / {v['common_auroc']:.6f}"
        md.append(f"| {arm} | {cond} | {metric(cc)} | {metric(rr)} | {cc['wire_ratio']:.8f} | {cc['call_ratio']:.8f} | {cc['last_real_p95_ms']:.8f} | {cc['traffic_p95_ms']:.8f} | {cc['evidence']} |")
md += ['', '## Existing estimated-flush-removal intent attacks', '',
       'Three intent models plus majority; train segmentation is customer OOF. This is already executed, not a proposed result.', '',
       '| Prompt / scheduler | Target | BA [95% CI] | AUROC | Valid draws |',
       '|---|---|---|---:|---:|']
for k, v in flush.items():
    arm, cond, view, target = k.split('|')
    b = v['ba']; lo, hi = b['ci95']
    md.append(f"| {arm} / {cond} | {target} | {100*b['point']:.4f} [{100*lo:.4f}, {100*hi:.4f}] | {v['auroc']['point']:.6f} | {2000-b['invalid_draws']} |")
(HERE / 'defense-self-audit.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
tex = [r'\begin{table*}[t]\centering\footnotesize',
       r'\caption{Suggested R8 self-audit comparison: identical seven-model suite on the same 138 held-out trajectories per prompt (24 customers). BA is cancel/return; byte/call ratios use prompt-specific undefended totals. These are descriptive evaluated points, not statistically certified dominance. WT is an offline RPC adaptation; shadow and tunnel use live local tools on fixed saved actions. None measures live LLM utility under defense.}',
       r'\begin{tabular}{@{}llrrrr@{}}\toprule Prompt & Condition & BA (C/R, \%) & Bytes$\times$ & Calls$\times$ & Execution\\\midrule']
for arm in ['baseline', 'rules']:
    for cond in conditions[2:]:
        cc, rr = [v for v in rows if v['prompt'] == arm and v['condition'] == cond]
        execution = 'offline' if cond == 'walkie_talkie' else 'local tools'
        label = cond.replace('_', r'\_')
        tex.append(f"{arm} & {label} & {100*cc['common_ba']:.1f}/{100*rr['common_ba']:.1f} & {cc['wire_ratio']:.2f} & {cc['call_ratio']:.2f} & {execution}" + r'\\')
tex += [r'\bottomrule\end{tabular}', r'\end{table*}']
(HERE / 'defense-self-audit-suggested-table.tex').write_text('\n'.join(tex) + '\n', encoding='utf-8')
print(json.dumps(dict(saved=True, matched_cells=len(rows), flush_cells=len(flush), detectors=detectors,
                     descriptive_point_dominance=comparisons), ensure_ascii=False, indent=2))
