"""R8 tables: deterministic rendering of existing, immutable result files."""
from pathlib import Path
import json, argparse
P=Path(__file__).resolve().parents[2]
M=P/'manuscript/tables'
common=json.loads((P/'experiments/sp2027-r7-robustness/common-suite.json').read_text())
audit=json.loads((P/'provenance/r8-review/defense-self-audit.json').read_text())
keys=['raw','padding','shadow_serial','shadow_parallel2','tunnel_2ms','tunnel_5ms','bucket1024','tamaraw','tamaraw_fast','front','wtfpad','walkie_talkie','front_shift']
old=(M/'r7-controls.tex').read_text()
rows=[l for l in old.splitlines() if l.startswith(('M &','S &'))]
assert len(rows)==len(keys)
out=[r'\begin{table*}[t]\centering\footnotesize',
r'\caption{Timing-aware E13/E14 comparison: standard prompt, 138 held-out episodes, 24 customers (5 cancel-positive, 7 return-positive). Each BA pair is cancel/return (\%). The common seven models permit a matched-suite comparison; the full union also retains all earlier attacks. All full-union two-target gates remain unconfirmed.}\label{tab:r7-controls}',
r'\begin{tabular}{@{}llrrrrrr@{}}\toprule',
r'View & Condition & Common-seven BA & Full-union BA & Upper BA & Bytes$\times$ & Calls$\times$ & RPC p95 (ms)\\\midrule']
for row,key in zip(rows,keys):
 cols=[c.strip().removesuffix(r'\\') for c in row.split('&')]
 pair='/'.join(f"{100*common['cells'][f'baseline|{key}|{target}']['ba']['point']:.1f}" for target in ['cancel','return'])
 out.append(' & '.join([cols[0],cols[1],pair,cols[2],cols[3],cols[4],cols[5],cols[6] if cols[0]=='M' else '--'])+r'\\')
out += [r'\bottomrule\end{tabular}',
r'\par\smallskip\raggedright M: measured local tool RPC on saved actions; S: offline traffic transformation. RPC p95 ends at the last real response, excluding LLM/WAN. S-row simulated spans are not RPC latency. Upper BA is the full-union 95\% bound. M unions contain 17--22 attacks; S unions contain the common seven. Ratios use prompt-specific undefended captures; S20/S23 give both prompts, interval and finish-time details. No row measures live defended-planner utility.',
r'\end{table*}']
outputs={'r8-controls.tex':'\n'.join(out)+'\n'}
out=[r'\begin{table}[t]\centering\footnotesize',
r'\caption{E13 intent BA after learned flush removal (95\% customer-cluster interval). Each row: 138 test episodes, 24 customers. Maximum of three classifiers plus majority; the complete attack union additionally keeps unstripped observations.}\label{tab:r8-flush}',
r'\begin{tabular}{@{}llrr@{}}\toprule',
r'Prompt & Schedule & Cancel & Return\\\midrule']
for prompt in ['baseline','rules']:
 for cond in ['shadow_serial','shadow_parallel2']:
  vals=[]
  for target in ['cancel','return']:
   b=audit['saved_flush_then_intent'][f'{prompt}|{cond}|flush_stripped_joint|{target}']['ba']
   vals.append(f"{100*b['point']:.1f} [{100*b['ci95'][0]:.1f}, {100*b['ci95'][1]:.1f}]")
  out.append(' & '.join(['Standard' if prompt=='baseline' else 'Rules','Serial' if cond=='shadow_serial' else 'Parallel']+vals)+r'\\')
out.extend([r'\bottomrule\end{tabular}',r'\end{table}'])
outputs['r8-flush.tex']='\n'.join(out)+'\n'
check=argparse.ArgumentParser();check.add_argument('--check',action='store_true'); args=check.parse_args()
for name,content in outputs.items():
 if args.check: assert (M/name).read_text()==content,name
 else: (M/name).write_text(content,encoding='utf-8',newline='\n')
print('PASS: deterministic R8 control and flush tables' if args.check else 'Wrote two R8 tables')
