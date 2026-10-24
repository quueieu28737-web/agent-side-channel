import sys,subprocess,json,time,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent;c=h.parent/'sp2027-r7-crossfit'
while not (c/'verification.json').exists():time.sleep(5)
assert json.loads((c/'verification.json').read_text())['passed']
for script in ['run.py','report.py','verify.py']:subprocess.run([sys.executable,'-B',str(h/script)],check=True)
for args,name in [(['--prompt','baseline'],'main_table.tex'),(['--detail'],'s21_table.tex')]:
 with (h/name).open('wb') as f:subprocess.run([sys.executable,'-B',str(h/'table.py')]+args,stdout=f,check=True)
files=[p for p in h.iterdir() if p.is_file() and p.name not in ['artifact_manifest.json','pipeline.log']];assert max(p.stat().st_size for p in files)<100*1024**2
(h/'artifact_manifest.json').write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)},indent=2),encoding='utf8');print('COMPLETE verified independent E12 extension',flush=True)
