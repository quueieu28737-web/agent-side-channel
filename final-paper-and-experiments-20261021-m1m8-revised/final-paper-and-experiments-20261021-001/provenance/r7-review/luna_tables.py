"""Render Luna tables directly from the validated, complete supplementary study."""
from pathlib import Path
import hashlib, json, sys

O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
A=P/'experiments/sp2027-r7-agent-extension'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
v=read(A/'formal_validation.json');d=read(A/'compact_manifest.json')
assert v['complete'] and v['runs']==v['reward_recomputed_runs']==d['formal_runs']==150
for name,digest in d['artifacts'].items():
 assert hashlib.sha256((A/name).read_bytes()).hexdigest()==digest,name

def put(name,text):
 path=M/'tables'/name;text=text.strip()+'\n'
 if '--check' in sys.argv:assert path.read_text(encoding='utf8')==text,name
 else:path.write_text(text,encoding='utf8',newline='\n')
def arm(name):return 'Standard' if name=='baseline' else 'Rules'
def pct(v,field):
 c=v[field+'_ci95'];return f"{100*v[field]:.1f} [{100*c[0]:.1f}, {100*c[1]:.1f}]"
def auc(v):
 c=v['suite_auroc_ci95'];return f"{v['suite_auroc']:.3f} [{c[0]:.3f}, {c[1]:.3f}]"

lines=[r'''\begin{table}[ht]\centering\footnotesize
\caption{Additional Luna study: all 75 runs per prompt, including task failures. Tool counts are dispatches to registered tools, including failed calls; tool errors also include unknown-name attempts. Wall-clock time covers model interaction and local execution. These are undefended planner runs, not live-cover replanning.}\label{tab:r7-luna-utility}
\begin{tabular}{@{}lrrrrrr@{}}\toprule
Prompt & Reward & \shortstack{Median / p95\\(s)} & \shortstack{Tool / model\\calls} & \shortstack{Tool\\errors} & \shortstack{Protocol\\errors} & \shortstack{Infra / timeout\\/ retry}\\\midrule''']
for name in ('baseline','rules'):
 v=d['per_prompt'][name]
 lines.append(f"{arm(name)} & {v['reward_sum']}/{v['runs']} & {v['median_episode_seconds']:.1f} / {v['p95_episode_seconds']:.1f} & {v['real_tool_calls']} / {v['model_calls']} & {v['tool_error_calls']} & {v['protocol_error_episodes']} & {v['infrastructure_attempt_errors']} / {v['timeout_attempt_errors']} / {v['automatic_retries']}"+r'\\')
lines.append(r'\bottomrule\end{tabular}\end{table}')
put('r7-luna-utility.tex','\n'.join(lines))

lines=[r'''{\footnotesize
\begin{longtable}{@{}lllrrr@{}}
\caption{Luna dispatch-view diagnostic: maximum over majority, D2 logistic regression and D2 gradient boosting. Each prompt uses 29 training and 46 test tasks. Percent BA and AUROC have customer-bootstrap 95\% intervals. Read-only retains only get/find/list prefixes; it is not Sol E12's entire writes-removed complement.}\label{tab:r7-luna-dispatch}\\
\toprule Prompt & View & Target & BA [95\% CI] & AUROC [95\% CI] & Valid draws\\\midrule\endfirsthead
\toprule Prompt & View & Target & BA [95\% CI] & AUROC [95\% CI] & Valid draws\\\midrule\endhead''']
assert len(d['D2_dispatch_suite'])==12
for v in d['D2_dispatch_suite']:
 lines.append(f"{arm(v['prompt'])} & {v['view']} & {v['target']} & {pct(v,'suite_ba')} & {auc(v)} & {v['valid_ba_draws']}/2000"+r'\\')
lines.append(r'\bottomrule\end{longtable}}')
put('r7-luna-dispatch.tex','\n'.join(lines))

lines=[r'''{\footnotesize
\begin{longtable}{@{}lllrrrr@{}}
\caption{Luna local TLS replay: all 16 prompt/condition/target cells from 600 sessions. The inherited R4 suite includes undefended-trained $D_0$, condition-refitted $D_2$ and decoder/count controls; it differs from the expanded Sol union. Percent BA and AUROC have customer-bootstrap 95\% intervals. B/C denotes wire-byte and dispatch-record ratios to the same prompt's undefended test replay. Records include unknown/error attempts and generated cover; C is not a successful-action ratio.}\label{tab:r7-luna-network}\\
\toprule Prompt & Condition & Target & BA [95\% CI] & AUROC [95\% CI] & B$\times$/C$\times$ & Gate\\\midrule\endfirsthead
\toprule Prompt & Condition & Target & BA [95\% CI] & AUROC [95\% CI] & B$\times$/C$\times$ & Gate\\\midrule\endhead''']
names={'raw':'Undefended','baseline':'Undefended','undefended':'Undefended','padding':'Padding','padding_only':'Padding','shape':'Shape','shape_only':'Shape','shape_raw':'Shape','joint':'Joint','shape_const':'Joint'}
assert len(d['network_suite'])==16
for v in d['network_suite']:
 assert v['condition'] in names,v['condition']
 gate={'meets_evaluated_suite_criterion':'Pass','inconclusive':'Inconcl.','above_threshold':'Above'}[v['criterion']]
 lines.append(f"{arm(v['prompt'])} & {names[v['condition']]} & {v['target']} & {pct(v,'suite_ba')} & {auc(v)} & {v['wire_ratio']:.2f}/{v['call_ratio']:.2f} & {gate}"+r'\\')
lines.append(r'\bottomrule\end{longtable}}')
put('r7-luna-network.tex','\n'.join(lines))
print('LUNA_PUBLICATION_TABLES_CHECKED' if '--check' in sys.argv else 'LUNA_PUBLICATION_TABLES_WRITTEN')
