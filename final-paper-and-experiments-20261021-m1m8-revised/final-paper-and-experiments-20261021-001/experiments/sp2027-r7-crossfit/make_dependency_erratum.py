"""Create an explicitly unfrozen provenance erratum from existing frozen authorities."""
from pathlib import Path,PureWindowsPath
import json,hashlib
h=Path(__file__).resolve().parent;root=h.parents[1];audit=root/'revision-preview/r7-portability/scratch/added-dependencies.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
entries=read(audit)['dependencies'];anchors={}
for rel in ['experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json','experiments/sp2027-r6-timing/attacker_freeze.json','experiments/sp2027-r6-timing/frozen.json']:anchors[rel]={'sha256':sha(root/rel),'authority':'original frozen runtime/attacker manifest; supplementary import-closure erratum'}
deps=[]
for e in entries:
 rel=e['relative_path'];assert sha(root/rel)==e['sha256']
 if 'sp2027-r6-timing' not in rel:
  source='experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json';table='files';key=str(PureWindowsPath(rel).relative_to('experiments'))
 else:
  source='experiments/sp2027-r6-timing/'+('frozen.json' if rel.endswith('r6common.py') else 'attacker_freeze.json');table='source_sha256';key=Path(rel).name
 assert read(root/source)[table][key]==e['sha256']
 deps.append(dict(relative_path=rel,sha256=e['sha256'],authority_manifest=source,authority_table=table,authority_key=key,purpose=e['purpose']))
closure=dict(status='unfrozen dependency-closure erratum; no numerical change or retraining',reason='Portable source audit identified imports outside original C input/source list. Add only 28 existing SHA-bound source/data dependencies; frozen protocol/source/input/model/result/verification bytes remain unchanged.',anchors=anchors,dependencies=deps,r4_runtime_binding='Runtime SHA must match a hash-verified original episode inference fingerprint.',r6_binding='attacker_freeze.frozen_sha256 must match frozen.json original SHA.',audit_list_sha256=sha(audit))
for name in ['sp2027-r7-crossfit','sp2027-r7-localization']:(root/'experiments'/name/'dependency-closure.json').write_text(json.dumps(closure,indent=2),encoding='utf8')
print('Created C/L explicit closure errata',len(deps))
