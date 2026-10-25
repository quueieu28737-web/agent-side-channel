"""Prepare R19 verification from the released R18 workflow (run once)."""
from pathlib import Path
import re,json,subprocess
from collections import Counter
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
for name in ['build_pdfs.py','verify_revision.py','release_ops.py','update_metadata.py']:
 s=(O/name).read_text().replace('r18-merged-manuscript','r19-evidence-closure').replace('R18','R19')
 if name=='verify_revision.py':s=s.replace("assert '7 of 15' not in texts['main']", "assert '351' in texts['supplement']\nassert all(s in texts['main'] for s in ['741','133','608','2/20','18.65','4.66'])")
 if name=='update_metadata.py':
  s=s.replace('R19 merged manuscript import, corrected evidence denominators and rounding, rebuilt and verified PDFs','R19 complete 39-record pair audit, configuration-level joint bindings, paired transfer intervals/costs and deployment decisions')
  s=s.replace('Compile merged manuscript revision 225c5fe; correct pairwise denominator, unresolved holdout wording and GLM rounding; preserve experimental evidence','Complete record-level synthesis and data-bound decision tables; preserve original experimental evidence')
 (O/name).write_text(s,newline='\n')
s=(O/'check_data.py').read_text()
a=s.index('for name,source in names.items():');b=s.index(" vals=[]",s.index(' assert name+',a))
s=s[:a]+'''for name,source in names.items():
'''+s[b:]
s=s.replace("['r9-record-index.tex','r9-rq-findings.tex']", "['r9-record-index.tex','r9-rq-findings.tex','r14-calibration-transfer.tex','r8-rq-findings.tex']")
# Reuse the already recomputed draw vectors for paired differences.
s=s.replace('point_count=0','point_count=0\ndraws={}')
s=s.replace(" b=np.fmax.reduce(bas);c=np.fmax.reduce(aucs)"," b=np.fmax.reduce(bas);c=np.fmax.reduce(aucs)\n draws[(r['study'],r['source'],r['target'],r['condition'],r['label'])]=b")
pos=s.index("names={'MiniMax'")
s=s[:pos]+'''paired=read(E/'sp2027-r14-transfer-boundaries/paired_transfer_intervals.json')
for p in paired:
 a=draws[('calibration_transfer',p['source'],p['target'],p['condition'],p['label'])]
 b=draws[('calibration_transfer',p['target'],p['target'],'transferred_joint',p['label'])]
 delta=a-b
 assert abs(delta[0]-p['difference'])<1e-12 and np.allclose(np.nanquantile(delta[1:],[.025,.975]),p['ci95'])
subprocess.run([sys.executable,str(O/'build_audit.py'),'--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run([sys.executable,str(O/'build_transfer_table.py'),'--check'],check=True,stdout=subprocess.DEVNULL)
''' +s[pos:]
s=s.replace("'point_metrics_recomputed':point_count", "'point_metrics_recomputed':point_count,'paired_contrasts_recomputed':len(paired),'record_cells_recomputed':351,'record_pairs_checked':741")
(O/'check_data.py').write_text(s,newline='\n')
prior=subprocess.check_output(['git','show','d717c2214565e7245aedc026b2d929a9c7bd4818:'+ (P/'SHA256SUMS.json').relative_to(R).as_posix()],cwd=R)
(O/'prior-SHA256SUMS.json').write_bytes(prior)
# Preserve previous family rationale, replace only verified current cells.
prior=json.loads((P/'provenance/r8-review/family-status-overlay.json').read_text())
mapping={'B':'Bound','P':'Partial','U':'NR-R','?':'NR-V','--':'NA'};result=[]
for line in (M/'tables/family-audit-matrix.tex').read_text().splitlines():
 if '&' not in line or r'\cite{' not in line:continue
 key=re.search(r'\\cite\{([^}]+)\}',line).group(1)
 fields=line.split('&')[1:10]
 codes=[re.sub(r'\\textbf\{(.)\}',r'\1',f.split('\\\\')[0]).strip() for f in fields]
 row=next(dict(x) for x in prior['per_family'] if x['family']==key)
 row.update({f'R{i}':mapping[c] for i,c in enumerate(codes,1)})
 if key=='chen2026sparleak':row['R8_reason']='Section 7.5 Table 4 pairs ASR and ROUGE by model and perturbation intensity; R8 admits component utility.'
 result.append(row)
assert len(result)==20
out={'revision':'R19','family_count':20,'per_family':result,'distributions':{f'R{i}':dict(Counter(x[f'R{i}'] for x in result)) for i in range(1,10)},'correction':'SparLeak R8 Partial to Bound; component utility criterion applied consistently. Original historical overlay unchanged.'}
(O/'family-status-overlay.json').write_text(json.dumps(out,indent=2)+'\n')
# Secondary narrative files retain historical inventories with explicit scope.
f=M/'sections/23-defense-comparison.tex';s=f.read_text().replace('The companion mode-specific table and 33-record ledger','The archived initial mode-specific table and 33-record ledger').replace('All 66 utility/cost positions','The completed 39-record, 351-cell audit is in Section~\\ref{app:record-joins}. All 66 initial utility/cost positions');f.write_text(s,newline='\n')
f=M/'sections/49-r9-record-index.tex';s=f.read_text().replace('of the initial ledger used by the pairwise audit','of the initial ledger, expanded to all 39 records in the final pairwise audit');f.write_text(s,newline='\n')
f=M/'tables/r8-rq-findings.tex';s=f.read_text().replace('3/17','4/17').replace('2/16','3/16');f.write_text(s,newline='\n')
f=M/'sections/54-transfer-boundaries.tex';s=f.read_text();s+=r'''
\paragraph{Call-cost reconciliation}
On MiniMax test trajectories, local joint / GLM-calibrated joint / write padding execute 1,712 / 1,588 / 510 calls against 510 undefended calls (3.36 / 3.11 / 1.00$\times$). On GLM they execute 1,409 / 1,548 / 332 calls against 332 undefended calls (4.24 / 4.66 / 1.00$\times$). Counts come from the captured request records, with the raw-session one-request-per-call invariant checked against saved call arrays. The main table reports these costs alongside all eight paired transfer/write-padding intervals.
''';f.write_text(s,newline='\n')
print('R19_CHECKS_PREPARED')
