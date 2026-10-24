"""Verify/recompute from the public redacted ZIP; never requests a model."""
from common import *
import argparse,tempfile,zipfile,shutil,re

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--network',action='store_true',help='also redo train-only TLS replay and fixed-suite network analysis');args=ap.parse_args()
 root=HERE;archive=root/'raw-evidence-public.zip';meta=read(root/'raw_archive.json');assert sha(archive)==meta['sha256']
 inventory=read(root/'raw_evidence_inventory.json')
 with tempfile.TemporaryDirectory(prefix='r7-public-recompute-') as td:
  target=Path(td)
  with zipfile.ZipFile(archive) as z:
   for info in z.infolist():
    name=Path(info.filename);assert not name.is_absolute() and '..' not in name.parts
    out=(target/name).resolve();assert out.is_relative_to(target.resolve())
    data=z.read(info)
    if info.filename not in ['raw_evidence_inventory.json','PUBLIC_REDACTION.json']:
     row=next(x for x in inventory if x['path']==info.filename);assert hashlib.sha256(data).hexdigest()==row['public_sha256']
     assert not re.search(rb'(?i)[a-z]:[\\/]+Users[\\/]+',data)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
  for name in set(read(root/'formal_plan.json')['files'])|{'formal_plan.json','formal_collection.json'}:
   shutil.copyfile(root/name,target/name)
  import verify_formal as vf
  vf.HERE=target;vf.main();validation=read(target/'formal_validation.json')
  validation.update({'input':'public redacted ZIP only; raw source directories not consulted','archive_sha256':meta['sha256'],'public_file_hashes_checked':len(inventory)})
  write(root/'public_validation.json',validation)
  if args.network:
   import network_replay as nr
   import evaluate_network as ne
   nr.HERE=target;ne.HERE=target
   for command in ['calibrate','capture']:
    sys.argv=['network_replay.py',command,'--workers','2'];nr.main()
   ne.main();new=read(target/'network_results.json');old_result=read(root/'network_results.json')
   key=lambda r:(r['target'],r['view'],r['prompt'],r['condition'])
   before={key(r):r for r in old_result['results']};after={key(r):r for r in new['results']}
   fields=['suite_ba','suite_auroc','suite_ba_ci95','suite_auroc_ci95']
   assert before.keys()==after.keys()
   for k in before:
    for f in fields:assert before[k][f]==after[k][f],str((k,f))
   write(root/'public_network_validation.json',{'complete':True,'recomputed_results':len(after),'matched_fields':fields,'input':'public ZIP with pinned public sandbox tools; no original raw directories or LLM requests','archive_sha256':meta['sha256']})
 print('PUBLIC_RECOMPUTATION_OK')
if __name__=='__main__':main()
