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
s['purpose']='R17 M2 editorial removal; explicit generating/receiving layers; preserved scientific evidence'
s['current_manuscript']={'revision':'R17-method-trim','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Remove corpus/coding self-critique and binary Origin A/B terminology; preserve source bindings and all experimental results'}
p.write_text(json.dumps(s,indent=2)+'\n')
p=P/'artifact-index.json';s=json.loads(p.read_text());s['modules']['r17-method-trim']={'description':'M2 editorial revision and publication verification; no scientific data changes','paths':['provenance/r17-method-trim/verification.json','provenance/r17-method-trim/anonymous-paper-check.json']};p.write_text(json.dumps(s,indent=2)+'\n')
print('R17_METADATA_UPDATED')
