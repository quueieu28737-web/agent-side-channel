"""Wait for completed run outputs, then make reports, verify, and emit local TeX."""
import sys,time,subprocess,json,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent
while not (h/'calibrations.json').exists():time.sleep(5)
for script in ['report.py','verify.py']:
 subprocess.run([sys.executable,'-B',str(h/script)],check=True)
for prompt,name in [('baseline','main_table.tex'),('rules','rules_table.tex'),('all','all_results_table.tex')]:
 with (h/name).open('wb') as f:subprocess.run([sys.executable,'-B',str(h/'table.py'),'--prompt',prompt],stdout=f,check=True)
files=[p for p in h.iterdir() if p.is_file() and p.name not in ['artifact_manifest.json','run.log','finish.log']]
assert max(p.stat().st_size for p in files)<100*1024**2
payload={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)}
(h/'artifact_manifest.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
print('COMPLETE all artifacts verified; largest file bytes',max(v['bytes'] for v in payload.values()),flush=True)

