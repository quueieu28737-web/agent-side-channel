"""Refresh presentation fragments after exact verification; frozen fitting files untouched."""
import sys,subprocess,json,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent
assert json.loads((h/'verification.json').read_text())['passed']
for prompt,name in [('baseline','main_table.tex'),('rules','rules_table.tex'),('all','all_results_table.tex')]:
 (h/name).write_bytes(subprocess.check_output([sys.executable,'-B',str(h/'table.py'),'--prompt',prompt]))
files=[p for p in h.iterdir() if p.is_file() and p.name not in ['artifact_manifest.json','run.log','finish.log']]
assert max(p.stat().st_size for p in files)<100*1024**2
(h/'artifact_manifest.json').write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)},indent=2),encoding='utf8')
print('Refreshed baseline main table, separate rules table, all-results table, and artifact hashes.')
