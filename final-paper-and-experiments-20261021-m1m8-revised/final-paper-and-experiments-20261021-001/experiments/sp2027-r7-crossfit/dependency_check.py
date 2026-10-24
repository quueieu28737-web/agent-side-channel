"""Unfrozen import-closure erratum check, using only original SHA-bound dependencies."""
import json,hashlib
from pathlib import Path,PureWindowsPath

def check(here):
 here=Path(here).resolve();root=here.parents[1];cross=root/'experiments/sp2027-r7-crossfit'
 def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 def target(rel):
  p=Path(rel);assert not p.is_absolute() and '..' not in p.parts and p.parts[0]=='experiments'
  result=(root/p).resolve();assert result.is_relative_to(root) and result.is_file(),('missing bounded dependency',rel)
  return result
 closure=read(here/'dependency-closure.json')
 allowed={'experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json','experiments/sp2027-r6-timing/attacker_freeze.json','experiments/sp2027-r6-timing/frozen.json'}
 assert set(closure['anchors'])==allowed
 authorities={}
 for rel,item in closure['anchors'].items():
  p=target(rel);assert sha(p)==item['sha256'],('changed original authority',rel);authorities[rel]=read(p)
 runtime='experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json';attack='experiments/sp2027-r6-timing/attacker_freeze.json';frozen='experiments/sp2027-r6-timing/frozen.json'
 # Bind runtime authority to an already hash-verified original episode, not a new digest assertion.
 mapping=read(cross/'portable-path-map.json');prefix=PureWindowsPath(mapping['original_package_root']);inputs=read(cross/'inputs_manifest.json')['sha256'];bound=False
 for original,digest in inputs.items():
  if not original.endswith('episode.json'):continue
  rel=PureWindowsPath(original).relative_to(prefix);p=target(Path(*rel.parts).as_posix());assert sha(p)==digest
  assert read(p)['inference_fingerprint']['runtime_manifest_sha256']==closure['anchors'][runtime]['sha256'];bound=True;break
 assert bound
 assert authorities[attack]['frozen_sha256']==closure['anchors'][frozen]['sha256']
 supplement=read(here/'dependency-path-map.json');assert set(supplement['allowed_relative_paths'])==set(closure['anchors'])|{e['relative_path'] for e in closure['dependencies']}
 entries=closure['dependencies'];assert len(entries)==36 and len({e['relative_path'] for e in entries})==36
 for entry in entries:
  rel=entry['relative_path'];src=entry['authority_manifest'];assert src in allowed
  table,key=entry['authority_table'],entry['authority_key']
  if src==runtime:
   if table=='files':
    expected='experiments/'+PureWindowsPath(key).as_posix()
    alias=expected.replace('experiments/sp2027-r4/','experiments/sp2027-r4-snapshot-20261023/',1)
    assert rel in (expected,alias);digest=authorities[src]['files'][key]
   elif table=='root':
    assert key in ('split_sha256','protocol_sha256')
    assert rel=='experiments/sp2027-r4-snapshot-20261023/'+key.replace('_sha256','.json');digest=authorities[src][key]
   else:
    assert table=='anchor' and key=='sha256' and rel==src;digest=closure['anchors'][src]['sha256']
  else:
   assert table=='source_sha256' and Path(key).name==key and rel==(Path(src).parent/key).as_posix();digest=authorities[src][table][key]
  assert digest==entry['sha256'];assert sha(target(rel))==digest,('changed bounded dependency',rel)
 original=here/'verification.json';assert read(original)['passed']
 receipt=dict(passed=True,status='supplemental dependency closure only; original numerical verification receipt remains byte-identical',dependencies=36,anchors={k:v['sha256'] for k,v in closure['anchors'].items()},runtime_bound_to_original_episode=True,r6_frozen_chain=True,closure_sha256=sha(here/'dependency-closure.json'),supplemental_path_map_sha256=sha(here/'dependency-path-map.json'),original_verification_sha256=sha(original),original_protocol_sha256=sha(here/'protocol.json'))
 (here/'dependency-verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');return receipt
if __name__=='__main__':print(check(Path(__file__).resolve().parent))


