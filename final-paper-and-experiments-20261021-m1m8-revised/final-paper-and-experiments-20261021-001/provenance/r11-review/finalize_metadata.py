from pathlib import Path
import sys,json,hashlib,datetime,shutil
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P))
from verify_package import closure
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['sp2027-r11-minimax','sp2027-r12-glm','sp2027-r15-live-planner']:
 assert json.loads((P/'experiments'/n/'verification.json').read_text())['passed']
assert json.loads((P/'experiments/sp2027-r14-transfer-boundaries/full_suite_verification.json').read_text())['passed']
p=P/'provenance/snapshot.json';s=json.loads(p.read_text())
if not (O/'pre-transfer-snapshot.json').exists():shutil.copy2(p,O/'pre-transfer-snapshot.json')
allpaths=set()
for name,doc in s['documents'].items():
 doc['closure']=closure(M,doc['entry']);doc['pdf_sha256']=sha(P/doc['pdf']);allpaths.update(doc['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(allpaths)}
s['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['current_manuscript']={'revision':'endpoint-and-transfer-boundaries','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Includes preserved R13 WAN work, R11/R12 endpoint tests, R14 expanded transfer suite and R15 scoped live planner utility'}
p.write_text(json.dumps(s,indent=2)+'\n')
p=P/'artifact-index.json';a=json.loads(p.read_text());a['purpose']='Defense transfer boundaries with endpoint replication, expanded transfer attacks and scoped live planner utility'
for n in ['sp2027-r11-minimax','sp2027-r12-glm','sp2027-r14-transfer-boundaries','sp2027-r15-live-planner']:
 a['modules'][n]={'description':'Versioned experimental evidence; see protocol/amendments and verifier for scope','paths':['experiments/'+n+'/README.md','experiments/'+n+'/verification.json']}
p.write_text(json.dumps(a,indent=2)+'\n')
print('METADATA_UPDATED')
