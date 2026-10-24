"""Compact existing-record index: no recoding or compilation."""
import json,hashlib,re
from pathlib import Path
P=Path(__file__).resolve().parents[2];M=P/'manuscript';O=P/'provenance/r9-review'
source=P/'experiments/reviewer-audit/combined_result_records.json'
r=json.loads(source.read_text());rows=r['baseline_records']+r['added_records']
notes='''Offline delay; no live task outcome.
Executed decoys; usefulness proxy only.
Protected deployment/local serving; topology scoped.
Synthetic insert/pad; no live execution.
K-specific fit then oracle; not live KV trial.
GPTCache prototype cost; not KV-granularity cost.
New padded captures; rounded medians.
Offline batching; model-dependent result.
Synthetic packets; no live zero-delay claim.
Prototype background load; tested signal only.
QCP component cost; excludes combined CTBF.
Length instruction; unequal outputs remain.
Analytic plaintext cost; not network bytes.
Padding/aggregation; payload cost, placement unverified.
Capture transform; distinct from live population.
Live loopback binding; do not join capture accuracy.
Common instruction; not a causal guardrail effect.
Post-trigger probes; detector cost not service TTFT.
Executed UI edits; task/state changes possible.
Offline touch edits; no online task damage claim.
Deterministic simulation; not live protected recovery.
Hardware gap calibration; not protected ASR.
HMAC microcost; not cache reuse/task loss.
Collected prompt rewrites; task utility unmeasured.
Collected decoding changes; no monotone benefit.
Rate/replayed cost; per-token, not request delay.
Loader component costs; not end-to-end TTFT.
Lookup microbenchmark; not full inference cost.
Live local browser tasks; loaded/cold context contrast.
Live access control; not user confidentiality.
MIG noise test; not an LLM defense trial.
Live VPN shift; baseline-trained attacker only.
Filter creates attack view; not mitigation of it.
Selective cache sharing; direct token recovery/quality.
Contextual guessing; distinct from direct recovery.
ORAM TTFT/memory; access-count padding excluded.
Epoch-padding estimate; not measured padded TTFT.
Sparse replacement/quality; attack cost is separate.
Constant-work proposal/estimate; no executed pair.'''.splitlines()
assert len(rows)==len(notes)==39 and len({x['unit_id'] for x in rows})==39
assert len({x['citation_key'] for x in rows})==26
bib='\n'.join(x.read_text(encoding='utf-8-sig') for x in M.rglob('*.bib'))
def tex(s):return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('–','--').replace('>=',r'$\geq$')
def ident(s):return tex(s).replace('-',r'-\allowbreak{}')
locators=[x.get('source_locator',x['scope']) for x in rows]
locators[-1]='IX-B1'
locators[-6]='3.1;5.1--5.6;T1;App.A';locators[-5]=locators[-6]
locators[-4]='VII-C--E;TIII';locators[-3]='VII-C--E;TIII';locators[-2]='3.1;4--7;T4'
locators=[x.replace('Tables','T').replace('Table','T').replace('Fig','F').replace('Appendix','App.').replace(';','; ') for x in locators]
parts=[r'\begin{table*}[t]\centering\footnotesize',r'\caption{Complete index of the 39 result records (26 families). Each row retains its artifact ID, family citation, observation/execution boundary and source-local locator. The panels form one inventory, not independent datasets. T=table, F=figure, App.=appendix; locators refer to the cited source.}\label{tab:r9-record-index}']
for a,b in [(0,20),(20,39)]:
 parts += [r'\begin{minipage}[t]{.492\textwidth}\vspace{0pt}',r'\setlength{\tabcolsep}{2pt}\renewcommand{\arraystretch}{1.04}',r'\begin{tabularx}{\linewidth}{@{}p{.40\linewidth}X@{}}\toprule',r'Record ID / family & Boundary, distinction; source locator\\\midrule']
 for i in range(a,b):parts.append(ident(rows[i]['unit_id'])+r'~\cite{'+rows[i]['citation_key']+'} & '+tex(notes[i])+' '+r'\emph{'+tex(locators[i])+'}'+r'\\')
 parts += [r'\bottomrule\end{tabularx}\end{minipage}']
 if a==0:parts += [r'\hfill']
parts += [r'\end{table*}']
(M/'tables/r9-record-index.tex').write_text('\n'.join(parts)+'\n',encoding='utf8')
(M/'sections/49-r9-record-index.tex').write_text(r'''\section{Result-record index}\label{app:records}
Table~\ref{tab:r9-record-index} indexes all 33 retained baseline and six expansion records. A family can contribute several records because observation, intervention, target, execution population or cost object differs. Sharing a citation does not authorize a paired-effect subtraction or transfer of a component cost to a deployment. This indexes the existing extraction, not a new source-independent coding pass. The machine-readable ledger retains exact versions, hashes, source paths and full locators; shortened locators below are navigation aids.
\input{tables/r9-record-index}
''',encoding='utf8')
validated=[]
for x,n,l in zip(rows,notes,locators):
 assert re.search(r'@\w+\s*\{\s*'+re.escape(x['citation_key'])+r'\s*,',bib),x['citation_key']
 validated.append(dict(record_id=x['unit_id'],family=x['citation_key'],source_path_as_recorded=x['source_path'],source_sha256_as_recorded=x['source_sha256'],exact_record_locator=x.get('source_locator',x['scope']),printed_locator=l,index_boundary_note=n,validation_scope='Identity/citation/locator metadata checked against existing combined ledger; no new fulltext rereading or external fetch'))
report=dict(passed=True,source=str(source.relative_to(P)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),records=39,baseline_records=33,expansion_records=6,families=26,unique_ids=True,bibliography_keys_resolved=True,records_detail=validated,layout='Two side-by-side 20/19-row tabularx panels; standard footnotesize, no margins/font scaling; not compiled, one-page fit unverified',additional_locator_authority={'SHAPE-padding-estimate':'manuscript/sections/31-result-audit.tex current source-follow-up IX-B1'},outputs={str(q.relative_to(P)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [M/'sections/49-r9-record-index.tex',M/'tables/r9-record-index.tex']})
(O/'record-index-source-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('39 records,26 families, all citations resolved')
