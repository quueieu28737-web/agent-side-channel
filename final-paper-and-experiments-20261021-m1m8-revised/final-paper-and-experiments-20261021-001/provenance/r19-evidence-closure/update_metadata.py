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
s['purpose']='R19 complete 39-record pair audit, configuration-level joint bindings, paired transfer intervals/costs and deployment decisions'
s['current_manuscript']={'revision':'R19-evidence-closure','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Complete record-level synthesis and data-bound decision tables; preserve original experimental evidence'}
p.write_text(json.dumps(s,indent=2)+'\n')
p=P/'artifact-index.json';s=json.loads(p.read_text());s['modules']['r19-evidence-closure']={'description':'Complete 39-record audit, within-configuration joins, paired transfer costs and deployment decisions','paths':['provenance/r19-evidence-closure/record-audit.json','provenance/r19-evidence-closure/pair-inventory.csv','provenance/r19-evidence-closure/summary.json','provenance/r19-evidence-closure/transfer-costs.json','provenance/r19-evidence-closure/family-status-overlay.json','provenance/r19-evidence-closure/verification.json','provenance/r19-evidence-closure/anonymous-paper-check.json']};p.write_text(json.dumps(s,indent=2)+'\n')
print('R19_METADATA_UPDATED')
