import re,json,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent;root=h.parents[1];m=root/'manuscript';seen={};missing=[]
def visit(p):
 if p in seen:return
 if not p.exists():missing.append(str(p));return
 s=p.read_text(encoding='utf-8-sig');seen[p]=s
 for rel in re.findall(r'\\input\{([^}]+)\}',s):visit(m/(rel if rel.endswith('.tex') else rel+'.tex'))
visit(m/'main.tex')
for p,s in seen.items():
 for i,line in enumerate(s.splitlines(),1):
  if re.search(r'confirmatory|preregister|independent confirm|timing|cross.fit|paired|19\.6|23\.4|690|345|11.attack|nondomin',line,re.I):print(f'{p.relative_to(m)}:{i}: {line}')
print('LIVE CLOSURE',len(seen),'files',sum(len(s.splitlines()) for s in seen.values()),'lines; missing',missing)
record=dict(scope='All main.tex recursively reachable TeX source files scanned; main and S20/S21 narrative plus R7 quantitative tables read and checked against C/L data. Corpus source claims outside C/L not independently reverified.',main_live_sources={p.relative_to(m).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(seen)},main_tex_files=len(seen),main_tex_lines=sum(len(s.splitlines()) for s in seen.values()),missing=missing,supplement_files=['sections/43-robustness.tex','sections/44-strong-crossfit.tex','tables/r7-all.tex','tables/r7-crossfit-all.tex','tables/r7-e12-all.tex'],finding='S20 empirical Pareto points use heterogeneous attacker unions (17–22 for measured vs 7 for simulated), which changes serial-shadow versus WT max-target dominance under a common7 sensitivity. No C/L number, denominator, paired-CI, retained-call/wire fraction or posthoc/timing-scope discrepancy found.')
(h/'manuscript-review.json').write_text(json.dumps(record,indent=2),encoding='utf8')
