"""Preserve the published R8 source state before the R9 editorial revision."""
from pathlib import Path
import subprocess,json,hashlib,shutil
O=Path(__file__).resolve().parent; P=O.parents[1]; R=P.parents[1]; M=P/'manuscript'
def original(rel):
    return subprocess.run(['git','show','HEAD:'+rel],cwd=R,capture_output=True,check=True).stdout
prefix=P.relative_to(R).as_posix()+'/'
base=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True).stdout.strip()
snap=json.loads(original(prefix+'provenance/snapshot.json'))
paths=set(snap['source_hashes'])|{'main.pdf','supplement.pdf','main.bbl','supplement.bbl'}
receipt={}
for rel in sorted(paths):
    data=original(prefix+'manuscript/'+rel);f=O/'prior-manuscript'/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
    receipt['manuscript/'+rel]=hashlib.sha256(data).hexdigest()
for rel in ['SHA256SUMS.json','artifact-index.json','provenance/snapshot.json','README.md']:
    data=original(prefix+rel);f=O/'prior-release'/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
    receipt[rel]=hashlib.sha256(data).hexdigest()
(O/'prior-release.json').write_text(json.dumps({'commit':base,'files':receipt,'scope':'Published R8 sources/PDFs and package manifest, preserved before R9 edits.'},indent=2)+'\n',encoding='utf8')
src=(P/'provenance/r8-review/build_pdfs.py').read_text(encoding='utf8').replace('r8-review','r9-review')
(O/'build_pdfs.py').write_text(src,encoding='utf8',newline='\n')
print('R8_PRESERVED',len(receipt),base)
