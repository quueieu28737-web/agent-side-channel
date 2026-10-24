"""Audit frozen outputs against the pre-erratum manifest and refresh unfrozen index."""
import json,hashlib,sys
from pathlib import Path
base=Path(__file__).resolve().parent
for h in [base,base.parent/'sp2027-r7-localization']:
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 old=h/'artifact_manifest.json';prior=h/'pre-erratum-artifact-manifest.json'
 if not prior.exists():prior.write_bytes(old.read_bytes())
 previous=json.loads(prior.read_text());fixed={'protocol.json','protocol_initial_failed.json','inputs_manifest.json','run.py','predictions.json','results.json','detailed_results.json','RESULTS.md','calibrations.json','bootstrap_suite_ba.npz','verification.json','PLAN.md','retained_fraction.json','run_complete.json'}
 checked={n:v['sha256'] for n,v in previous.items() if n in fixed or (n.startswith('f') and n.endswith('.zip'))}
 for name,digest in checked.items():assert sha(h/name)==digest,('frozen bytes changed',name)
 receipt=dict(passed=True,checked_files=len(checked),pre_erratum_manifest_sha256=sha(prior),frozen_files_sha256=checked)
 (h/'frozen-byte-audit.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
 files=[p for p in h.iterdir() if p.is_file() and p.name not in ['artifact_manifest.json','run.log','finish.log','pipeline.log']]
 assert max(p.stat().st_size for p in files)<100*1024**2
 old.write_text(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)},indent=2),encoding='utf8')
 print(h.name,'frozen bytes verified',len(checked),'largest file',max(p.stat().st_size for p in files))
