from pathlib import Path
import sys,json,hashlib,re
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
for name in ['sp2027-r11-minimax','sp2027-r12-glm','sp2027-r15-live-planner']:
 v=json.loads((P/'experiments'/name/'verification.json').read_text());ck(name,v['passed'])
v=json.loads((P/'experiments/sp2027-r14-transfer-boundaries/full_suite_verification.json').read_text());ck('transfer28',v['passed'] and v['rows']==28)
v=json.loads((P/'experiments/sp2027-r14-transfer-boundaries/verification.json').read_text());ck('transfer metrics intervals costs',v['passed'] and v['captures']==690)
v=json.loads((P/'experiments/sp2027-r14-transfer-boundaries/write_detector_verification.json').read_text());ck('nonoracle detector',v['passed'])
prior=json.loads((O/'prior-SHA256SUMS.json').read_text())['files']
paths=[n for n in prior if n.startswith(('experiments/','evidence/'))]
with ThreadPoolExecutor(max_workers=8) as pool:
 for n,h in zip(paths,pool.map(lambda n:sha(P/n),paths)):ck('preserved:'+n,h==prior[n])
pagecounts={}
for name in ['main','supplement']:
 d=PdfReader(M/(name+'.pdf'));pagecounts[name]=len(d.pages)
 ck(name+' copies',all(sha(p/(name+'.pdf'))==sha(M/(name+'.pdf')) for p in [R,P/'pdf']))
 log=(P/'pdf/build-logs'/(name+'.log')).read_text()
 ck(name+' no compile warnings',not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined',log))
 text='\n'.join(q.extract_text() for q in d.pages)
 ck(name+' no private identifiers',not any(s in text.lower() for s in ['quueieu28737','c:/users/','c:\\users\\']))
 if name=='main':
  refs=[i+1 for i,p in enumerate(d.pages) if 'References' in p.extract_text()];ck('body within13',refs and min(refs)<=13)
  ck('transfer matrix in main','Calibration source' in text and '70.8 / 50.0' in text)
report={'passed':True,'checks':len(checks),'preserved_scientific_files':len(paths),'pages':pagecounts,'pdf_sha256':{n:sha(M/(n+'.pdf')) for n in ['main','supplement']}}
(O/'release_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
