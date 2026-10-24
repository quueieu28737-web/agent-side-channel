"""Apply three explicitly sourced label corrections; retain historical coding columns."""
from pathlib import Path
import json,hashlib,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript/tables'
changes=json.loads((O/'audit-corrections.json').read_text())
prior=json.loads((O/'prior-package-manifest.json').read_text())['files']
outputs={}
for name in ('family-audit-matrix.tex','six-check-audit.tex'):
 base=O/('prior-'+name)
 assert hashlib.sha256(base.read_bytes()).hexdigest()==prior['manuscript/tables/'+name]
 outputs[name]=base.read_text()
s=outputs['family-audit-matrix.tex'];lines=s.splitlines()
for c in changes['changes']:
 idx=next(i for i,l in enumerate(lines) if c['family']+'}' in l)
 cells=lines[idx].split(' & ');column=int(c['item'][1:]);assert cells[column]=='?'
 cells[column]=r'\textbf{B}' if c['to']=='Bound' else 'U';lines[idx]=' & '.join(cells)
s='\n'.join(lines)+'\n'
s=s.replace(r'\midrule Bound & 20 & 17 & 16 &',r'\midrule Bound & 20 & 17 & 17 &')
s=s.replace('?: unverified binding (intentional);','?: unverified binding (11 cells);')
s=s.replace('CachePrune jointly binds R7--R9 at one operating point.','CachePrune jointly binds R7--R9 at one operating point. Source follow-up resolves three former ? cells: cloud-traffic R3 to B; Shape and Substance R4/R5 to U (S8).')
assert s.count(' & ?')==11
outputs['family-audit-matrix.tex']=s
s=outputs['six-check-audit.tex']
s=s.replace('R3. Placement \\& action dispatch & 13 (16) & 2 (3) & 0 (0) & 1 (1)', 'R3. Placement \\& action dispatch & 14 (17) & 2 (3) & 0 (0) & 0 (0)')
s=s.replace('R4. Protected-condition fit & 4 (4) & 1 (1) & 0 (0) & 4 (6)', 'R4. Protected-condition fit & 4 (4) & 1 (1) & 0 (1) & 4 (5)')
s=s.replace('R5. Matched adapted test & 2 (2) & 2 (2) & 0 (0) & 5 (7)', 'R5. Matched adapted test & 2 (2) & 2 (2) & 0 (1) & 5 (6)')
s=s.replace('Supplied two-column agreement','Current totals apply the three source-follow-up corrections; the historical coding columns remain unchanged. Supplied two-column agreement')
outputs['six-check-audit.tex']=s
for name,s in outputs.items():
 if '--check' in sys.argv:assert (M/name).read_text()==s,name
 else:(M/name).write_text(s,newline='\n')
print('THREE_SOURCE_CORRECTIONS_11_UNVERIFIED_HISTORICAL_COLUMNS_UNCHANGED')
