"""Generate the current primary cross-fit table from the complete attack union."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
C=P/'experiments/sp2027-r7-crossfit'
D=json.loads((C/'detailed_results.json').read_text())

def row(arm,condition,target):
 return next(v for v in D['results'] if (v['prompt'],v['condition'],v['target'])==(arm,condition,target))

def ba(v):return f"{100*v['suite_ba']:.1f} [{100*v['suite_ba_ci95'][0]:.1f}, {100*v['suite_ba_ci95'][1]:.1f}]"

def put(name,text):
 path=M/'tables'/name;text=text.strip()+'\n'
 if '--check' in sys.argv:assert path.read_text(encoding='utf8')==text,name
 else:path.write_text(text,encoding='utf8',newline='\n')

lines=[r'''\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{2pt}
\caption{Primary E10 cross-fit summary under the expanded 11-attacker union: all 690 episodes and 53 customers. Maximum network BA with customer-bootstrap 95\% intervals. Standard prompt unless marked Rules; byte/call ratios relative to undefended transport. Joint-design absolute-criterion outcomes remain inconclusive.}\label{tab:r5}
\begin{tabular}{@{}lrrr@{}}\toprule
Configuration & Cancel BA (\%) & Return BA (\%) & B$\times$/C$\times$\\\midrule''']
for arm,cond,name in [('baseline','undefended','Undefended'),('baseline','jointconstant','Joint constant'),('baseline','jointbucket1024','Joint buckets'),('rules','jointbucket1024','Rules + buckets')]:
 c=row(arm,cond,'cancel');r=row(arm,cond,'return')
 lines.append(f"{name} & \\mbox{{{ba(c)}}} & \\mbox{{{ba(r)}}} & {c['bytes_ratio']:.1f}/{c['calls_ratio']:.1f}"+r'\\')
lines += [r'''\bottomrule\end{tabular}
\par\smallskip\raggedright Joint constant is E9's shadow-count plus constant-framing design, refit within each fold. Joint buckets changes framing to 1024-byte buckets. Every bootstrap draw reselects the complete maximum; S21 reports both prompts, AUROC and paired reductions.
\end{table}''']
put('r5-main.tex','\n'.join(lines))

lines=[r'''\begin{longtable}{@{}lllrrrr@{}}
\caption{Expanded E10: all 12 cells. Percent BA and paired undefended-minus-defended decrease, each with 95\% customer-bootstrap intervals. AUROC is independently maximized over the same 11 attacks. Ratios are bytes/calls.}\label{tab:r7-crossfit-all}\\
\toprule Prompt & Condition & Target & BA [95\% CI] & AUROC & Decrease [95\% CI] & B$\times$/C$\times$\\\midrule\endfirsthead
\toprule Prompt & Condition & Target & BA [95\% CI] & AUROC & Decrease [95\% CI] & B$\times$/C$\times$\\\midrule\endhead''']
names={'undefended':'Undefended','jointconstant':'Joint constant','jointbucket1024':'Joint buckets'}
for arm in ('baseline','rules'):
 for cond in names:
  for target in ('cancel','return'):
   v=row(arm,cond,target);delta='--'
   if cond!='undefended':
    x=next(x for x in D['paired_contrasts'] if (x['prompt'],x['target'],x['contrast'])==(arm,target,'undefended minus '+cond))
    delta=f"{100*x['ba_decrease']:.1f} [{100*x['ci95'][0]:.1f}, {100*x['ci95'][1]:.1f}]"
   lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} & {names[cond]} & {target} & {ba(v)} & {v['suite_auroc']:.3f} & {delta} & {v['bytes_ratio']:.2f}/{v['calls_ratio']:.2f}"+r'\\')
lines.append(r'\bottomrule\end{longtable}')
put('r7-crossfit-all.tex','\n'.join(lines))

# The three cohort denominators are unchanged. Only E10 now uses the enlarged union.
cohort=r'''\begin{table}[t]\centering\footnotesize
\caption{Denominators and undefended network BA (cancel/return, \%). Episodes include both prompts; numerical pairs use the standard prompt. These are different estimands.}\label{tab:r7-cohorts}
\begin{tabularx}{\columnwidth}{@{}lYrr@{}}\toprule
Study & Observation / fit & Episodes & BA pair\\\midrule
E9 & Replay lengths/order; original frozen suite & 276 (138) & 97.2/94.0\\
E10 & Analytic lengths/order; 11-attack cross-fit & 690 (345) & %CANCEL%/%RETURN%\\
E13/14 & New RPC envelope; lengths/order + time & 276 (138) & 91.7/86.4\\\bottomrule
\end{tabularx}
\par\smallskip\raggedright Parentheses: episodes per prompt. E9/E13 use 24 test customers; E10 pools 53. E14 expands E13's attackers. E13 bytes use its own undefended envelope, not E9's serialization.
\end{table}'''
for t in ('cancel','return'):cohort=cohort.replace('%'+t.upper()+'%',f"{100*row('baseline','undefended',t)['suite_ba']:.1f}")
put('r7-cohorts.tex',cohort)
print('CROSSFIT_PUBLICATION_TABLES_CHECKED' if '--check' in sys.argv else 'CROSSFIT_PUBLICATION_TABLES_WRITTEN')
