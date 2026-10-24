from pathlib import Path
import subprocess
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
def read(f):return (M/f).read_text(encoding='utf8')
def put(f,s):(M/f).write_text(s,encoding='utf8',newline='\n')
for old,new in [('transfer-streaming','r9-streaming'),('r7-e6-main','r9-dispatch')]:
 s=read('tables/'+old+'.tex')
 put('tables/'+new+'.tex',s)
 data=subprocess.run(['git','show','HEAD:'+(M/'tables'/f'{old}.tex').relative_to(R).as_posix()],capture_output=True,cwd=R,check=True).stdout
 (M/'tables'/f'{old}.tex').write_bytes(data)
 s=read('sections/37-transfer-tests.tex').replace(r'\input{tables/'+old+'}',r'\input{tables/'+new+'}')
 put('sections/37-transfer-tests.tex',s)
s=read('tables/r9-streaming.tex').replace('T1 acc.','Verbosity').replace('& T3 &','& Prefix &')
s=s.replace('Tokens: o200k\\_base proxy. Count cap: 208 (T1) and 88 (T3) events fitted on training outputs; 2/24 and 5/24 test outputs overflow it.',r'Verbosity contrasts brief/expanded outputs; Prefix contrasts the first two/three sentences of each expanded output. Tokens use o200k\_base. Training count caps are 208/88 events, with 2/24 and 5/24 test overflows, respectively.')
put('tables/r9-streaming.tex',s)
s=read('tables/r9-cohorts.tex').replace(r'@{}lYrr@{}',r'@{}p{.23\columnwidth}Yrr@{}').replace('Distinct estimands, not interchangeable results.','Cohort, observation and cost denominators for Exps~3--4.').replace('Frozen split / RPC:','Frozen-split and RPC rows:').replace('Frozen split / RPC use','frozen-split and RPC rows use')
put('tables/r9-cohorts.tex',s)
s=read('sections/49-r9-record-index.tex')
s=s[:s.index('A family can')]+r"""Separate records identify changes in observation, intervention, target, execution population or cost object within a family. Shortened source locators below support direct lookup; the machine-readable ledger retains exact versions, hashes and full locators.
\input{tables/r9-record-index}
"""
put('sections/49-r9-record-index.tex',s)
s=read('sections/50-r9-experiment-index.tex')
a=s.index('The main text');b=s.index('\\begin{table*}',a)
s=s[:a]+r"""Table~\ref{tab:r9-experiment-index} maps the four main experiments to stable artifact keys and detailed supplementary methods. Reanalysis, prompts and repetitions retain their original customer/task membership.
"""+s[b:]
s=s.replace('These are navigation mappings, not pooled populations or interchangeable observation contracts.','The right column supplies optional implementation and full-grid detail.').replace('Stand-in-planner pipeline check; not autonomous-model replication.','Stand-in-planner pipeline check.').replace('Retrospective training-fold operating-point selection with the historical suite; not the updated primary attack comparison.','Retrospective training-fold operating-point selection with the historical suite.')
s=s[:s.index("The artifact's machine-readable index")]+r"""The reproducibility index resolves these keys to files, protocols, saved predictions and executable verification commands. The source versions and calibration chronology remain available for every analysis.
"""
put('sections/50-r9-experiment-index.tex',s)
# Define main notation once; legacy labels are explicit only in the supplementary crosswalk.
s=read('supplement.tex')
s=s.replace(r'\newcommand{\NRR}{\textsc{nr-r}}',r'\newcommand{\NRR}{\textsf{U}}').replace(r'\newcommand{\NRA}{\textsc{nr-a}}',r'\newcommand{\NRA}{\textsf{A}}').replace(r'\newcommand{\NRV}{\textsc{nr-v}}',r'\newcommand{\NRV}{\textsf{?}}').replace(r'\newcommand{\NA}{\textsc{na}}',r'\newcommand{\NA}{--}')
start=s.index('This supplement provides');end=s.index('\\section{Search and Evidence Audit}',start)
s=s[:start]+r"""This supplement supplies implementation details, full result grids and historical coding records. The main paper contains the complete 58-family map, nine audit rules, 20-family matrix, 39-record index and four experimental demonstrations. Main-text Exp~1 maps to archived E1/E3/E5; Exp~2 to E2/E6/E7; Exp~3 to E9/E10/E12; and Exp~4 to E13/E14. The main Appendix~C indexes the remaining extensions. Historical E-keys and S-section numbers below remain stable for reproduction.

\paragraph{Shared evidence notation}
B means bound, P partial, U unreported in inspected scope, A source unavailable, ? an unverified binding, and -- inapplicable. Archived machine fields NR-R/NR-A/NR-V map respectively to U/A/?. Source availability and applicability retain distinct meanings. S1--S10 contain search, coding and literature audit details; S11--S17 contain transport/agent mechanisms and initial analyses; S18--S23 contain source reconciliation, timing controls, stronger attacks, the model extension and sensitivity checks.
"""+s[end:]
put('supplement.tex',s)
print('NAVIGATION_AND_NOTATION_UPDATED')
