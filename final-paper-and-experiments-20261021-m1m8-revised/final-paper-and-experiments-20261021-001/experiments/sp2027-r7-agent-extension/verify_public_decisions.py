from common import *
import tempfile,zipfile
import verify_decisions as vd

def main():
 inventory={x['path']:x for x in read(HERE/'raw_evidence_inventory.json')};meta=read(HERE/'raw_archive.json');assert sha(HERE/meta['path'])==meta['sha256']
 with tempfile.TemporaryDirectory(prefix='r7-public-align-') as td:
  root=Path(td)
  with zipfile.ZipFile(HERE/meta['path']) as z:
   for name in z.namelist():
    if name not in inventory:continue
    out=(root/name).resolve();assert out.is_relative_to(root.resolve());data=z.read(name);assert hashlib.sha256(data).hexdigest()==inventory[name]['public_sha256']
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
  result=vd.verify(root,HERE/'public_decision_alignment.json')
  result['input']='public ZIP only; original raw directories not consulted';result['archive_sha256']=meta['sha256'];write(HERE/'public_decision_alignment.json',result)
 print('PUBLIC_DECISION_ALIGNMENT_OK')
if __name__=='__main__':main()
