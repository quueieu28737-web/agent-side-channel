"""Derive current E12 display from complete 11-attack oracle predictions."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
D=json.loads((P/'experiments/sp2027-r7-localization/detailed_results.json').read_text())
def row(arm,view,target):return next(v for v in D['results'] if (v['prompt'],v['view'],v['target'])==(arm,view,target))
def fmt(v,key='ba'):
 p=v['suite_'+key];lo,hi=v['suite_'+key+'_ci95'];scale=100 if key=='ba' else 1
 return f'{p*scale:.1f} [{lo*scale:.1f}, {hi*scale:.1f}]' if key=='ba' else f'{p:.3f} [{lo:.3f}, {hi:.3f}]'
def put(name,text):
 p=M/'tables'/name;text=text.strip()+'\n'
 if '--check' in sys.argv:assert p.read_text(encoding='utf8')==text,name
 else:p.write_text(text,encoding='utf8',newline='\n')
lines=[r'''\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{2pt}
\caption{E12 oracle localization under the 11-attack union. Standard prompt: 345 cross-fitted episodes, 53 customers. Maximum network BA (\%) with customer-bootstrap intervals.}\label{tab:r7-e12}
\begin{tabular}{@{}lrrr@{}}\toprule
Target & Full trace & Writes removed & Writes only\\\midrule''']
for t in ('cancel','return'):
 lines.append(t.title()+' & '+' & '.join(r'\mbox{'+fmt(row('baseline',v,t))+'}' for v in ('full','no_writes','writes_only'))+r'\\')
lines.append(r'\bottomrule\end{tabular}\end{table}')
put('r7-e12-main.tex','\n'.join(lines))
lines=[r'''\begin{longtable}{@{}lllrr@{}}
\caption{Expanded E12 oracle ablation, both prompts. Suite-maximum BA (percent) and AUROC, with customer-bootstrap 95\% intervals. The full reference is the verified expanded E10 undefended prediction set.}\label{tab:r7-e12-all}\\
\toprule Prompt & Target & Oracle view & BA [95\% CI] & AUROC [95\% CI]\\\midrule\endfirsthead
\toprule Prompt & Target & Oracle view & BA [95\% CI] & AUROC [95\% CI]\\\midrule\endhead''']
for arm in ('baseline','rules'):
 for t in ('cancel','return'):
  for v,name in [('full','Full trace'),('no_writes','Writes removed'),('writes_only','Writes only')]:
   r=row(arm,v,t);lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} & {t} & {name} & {fmt(r)} & {fmt(r,'auroc')}"+r'\\')
lines.append(r'\bottomrule\end{longtable}')
put('r7-e12-all.tex','\n'.join(lines))
print('LOCALIZATION_PUBLICATION_TABLES_CHECKED' if '--check' in sys.argv else 'LOCALIZATION_PUBLICATION_TABLES_WRITTEN')
