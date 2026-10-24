from pathlib import Path
import hashlib,json,datetime
h=Path(__file__).resolve().parent;e=h.parent
files=list((e/'sp2027-r4-snapshot-20261023/runs').glob('*/task-*/episode.json'))+list((e/'sp2027-r4-full-20261023/delta/runs').glob('*/task-*/episode.json'))
sources=[]
for d in ['sp2027-r5-crossfit','sp2027-r4-snapshot-20261023','sp2027-r3','sp2027-r2']:
 sources+=list((e/d).glob('*.py'))
payload={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'All snapshot and delta episode files and direct legacy Python sources, frozen before first successful cell output; snapshot may include files outside complete 690 grid.','sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files+sources)}}
(h/'inputs_manifest.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
