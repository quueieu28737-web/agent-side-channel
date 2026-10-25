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
s['purpose']='R18 merged manuscript import, corrected evidence denominators and rounding, rebuilt and verified PDFs'
s['current_manuscript']={'revision':'R18-merged-manuscript','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Compile merged manuscript revision 225c5fe; correct pairwise denominator, unresolved holdout wording and GLM rounding; preserve experimental evidence'}
p.write_text(json.dumps(s,indent=2)+'\n')
p=P/'artifact-index.json';s=json.loads(p.read_text());s['modules']['r18-merged-manuscript']={'description':'Merged manuscript, data and PDF verification; original experimental evidence unchanged','paths':['provenance/r18-merged-manuscript/verification.json','provenance/r18-merged-manuscript/anonymous-paper-check.json']};p.write_text(json.dumps(s,indent=2)+'\n')
print('R18_METADATA_UPDATED')
