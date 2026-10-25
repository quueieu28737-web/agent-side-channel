from pathlib import Path
import sys,json,hashlib,datetime
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';sys.path.insert(0,str(P))
from verify_package import closure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=P/'provenance/snapshot.json';s=json.loads(p.read_text());allpaths=set()
for name,d in s['documents'].items():
 d['closure']=closure(M,d['entry']);d['pdf_sha256']=sha(P/d['pdf']);allpaths.update(d['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(allpaths)}
s['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
s['purpose']='R16 systematic holdout evidence, complete record-mode census and scoped empirical contribution'
s['current_manuscript']={'revision':'R16-systematic-transfer-synthesis','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'82-family six-axis archived-evidence matrix; all39 record-mode census; preserved R11-R15 experimental results'}
p.write_text(json.dumps(s,indent=2)+'\n')
p=P/'artifact-index.json';s=json.loads(p.read_text());s['modules']['r16-synthesis']={'description':'82-family holdout evidence and39-record measurement-mode census; archived extraction scope, not independent recoding','paths':['provenance/r16-synthesis/holdout-matrix.json','provenance/r16-synthesis/record-mode-inventory.json','provenance/r16-synthesis/verification.json']};p.write_text(json.dumps(s,indent=2)+'\n')
print('R16_METADATA_UPDATED')
