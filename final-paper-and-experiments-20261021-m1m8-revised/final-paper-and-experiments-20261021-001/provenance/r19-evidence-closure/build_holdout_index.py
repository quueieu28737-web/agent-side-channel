"""Keep the complete 82-family code matrix in one readable main appendix table."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
d=json.loads((P/'provenance/r16-synthesis/holdout-matrix.json').read_text())
def row(r):
 name=r['name'].replace('&',r'\&').replace('_',r'\_')
 return r['id']+' '+name+r'~\cite{'+r['citation_key']+'} & '+('C' if r['classification']=='core' else 'A')+' & '+' & '.join(r['axes'][a] for a in d['axes'])
header=r'Family & Scope & T & M & C & H & N & D'
t=[r'\section{Family-Level Holdout Evidence}\label{app:holdouts}',r'Table~\ref{tab:r19-holdouts} covers all 82 indexed families and 492 axis cells. T: task/input/user; M: model; C: harness/topology; H: hardware; N: network/load; D: time. H means an explicitly reported held-out unit/domain; V a condition comparison or recalibration; X a scoped restriction; ? unresolved extraction; -- inapplicable to conceptual families. H identifies separation, not guaranteed transfer success. The 73 hardware and 71 temporal ? cells are not evidence of absent experiments. Core/adjacent scope is C/A. Supplement S28 retains each source locator and interpretation; the archive preserves the underlying extraction.',r'\begin{table*}[t]\centering\footnotesize',r'\caption{Complete holdout-code matrix; codes and axes are defined in Appendix~\ref{app:holdouts}. Source-qualified row notes are in Supplement S28.}\label{tab:r19-holdouts}',r'\setlength{\tabcolsep}{2.4pt}',r'\begin{tabularx}{\textwidth}{@{}Yccccccc@{\hspace{9pt}}Yccccccc@{}}\toprule',header+' & '+header+r'\\\midrule']
for a,b in zip(d['rows'][:41],d['rows'][41:]):t.append(row(a)+' & '+row(b)+r'\\')
t.extend([r'\bottomrule\end{tabularx}',r'\end{table*}'])
out=M/'sections/59-holdout-compact.tex';s='\n'.join(t)+'\n'
if '--check' in sys.argv:assert out.read_text()==s
else:out.write_text(s,encoding='utf8',newline='\n')
p=M/'main.tex';s=p.read_text();s=s.replace(r'\input{sections/56-holdout-matrix}',r'\input{sections/59-holdout-compact}');p.write_text(s,newline='\n')
print('82_FAMILY_MAIN_MATRIX_GENERATED')
