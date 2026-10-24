import json,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent;root=h.parents[1];runtime='experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json';m=json.loads((root/runtime).read_text());o=root/'provenance/r7-review/portable-verification'
items=[json.loads((o/'supplemental-file-dependencies.json').read_text(encoding='utf-8-sig'))['file']]+json.loads((o/'supplemental-fingerprint-files.json').read_text(encoding='utf-8-sig'))['files']
for name in ['sp2027-r7-crossfit','sp2027-r7-localization']:
 d=root/'experiments'/name;c=json.loads((d/'dependency-closure.json').read_text());seen={e['relative_path'] for e in c['dependencies']}
 for e in items:
  rel=e['relative_path'];assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==e['sha256']
  if rel in seen:continue
  base=Path(rel).name
  if base=='runtime_manifest.json':table,key='anchor','sha256';assert e['sha256']==c['anchors'][runtime]['sha256']
  elif base in ['split.json','protocol.json']:table,key='root',base.replace('.json','_sha256');assert m[key]==e['sha256']
  else:table,key='files','sp2027-r4\\'+base;assert m['files'][key]==e['sha256']
  c['dependencies'].append(dict(relative_path=rel,sha256=e['sha256'],authority_manifest=runtime,authority_table=table,authority_key=key,purpose='R5 split and original episode inference fingerprint verification'));seen.add(rel)
 c['reason']=c['reason'].replace('28 existing','36 existing')+' Second portable execution audit adds 8 R4 split/protocol/runtime/fingerprint files, including non-Python inputs.'
 (d/'dependency-closure.json').write_text(json.dumps(c,indent=2),encoding='utf8')
 p=json.loads((d/'dependency-path-map.json').read_text());p['allowed_relative_paths']=sorted(set(c['anchors'])|seen);p['scope']='Only explicit original-manifest-bound supplemental source AND data paths; frozen primary mapping unchanged.';(d/'dependency-path-map.json').write_text(json.dumps(p,indent=2),encoding='utf8')
