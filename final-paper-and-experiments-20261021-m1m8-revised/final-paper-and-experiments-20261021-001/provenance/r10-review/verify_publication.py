"""Verify R10 editorial revision against the immutable R9 release manifest."""
from pathlib import Path
import hashlib,json,re,sys
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
import pdfplumber
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,value):
 assert value,name
 checks.append(name)
prior=json.loads((O/'prior-SHA256SUMS.json').read_text())['files']
paths=[f for f in prior if f.startswith(('experiments/','evidence/','manuscript/tables/','manuscript/figures/'))]
with ThreadPoolExecutor(max_workers=8) as pool:
 for f,h in zip(paths,pool.map(lambda f:sha(P/f),paths)):ck('preserved:'+f,h==prior[f])
for name,total in [('main',17),('supplement',52)]:
 pdf=PdfReader(M/(name+'.pdf'));ck(name+' pages',len(pdf.pages)==total)
 for d in [R,P/'pdf']:ck(name+' copy '+str(d),sha(d/(name+'.pdf'))==sha(M/(name+'.pdf')))
 log=(P/'pdf/build-logs'/(name+'.log')).read_text()
 ck(name+' compilation',not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined',log))
 bbl=(M/(name+'.bbl')).read_text();ck(name+' corrected surname','Z.~Li' in bbl or 'Z. Li' in bbl)
 ck(name+' no lowercase surname','Z.~li' not in bbl)
 ck(name+' acronym capitalization','{LLM}' in bbl and '{KV}' in bbl)
 if name=='main':
  texts=[p.extract_text() for p in pdf.pages]
  ck('body 13 pages','References' in texts[12]);ck('appendices follow references page16','Appendix A' in texts[15]);ck('index final page','TABLE 19' in texts[16])
  with pdfplumber.open(M/'main.pdf') as pp:top=min(w['top'] for w in pp.pages[0].extract_words())
  ck('standard title top',90<top<100)
source=(M/'sections/42-live-timing-main.tex').read_text()
for s in ['Within measured RPC conditions (M)','68.6/62.7','61.4/53.4','descriptive, shared-metadata comparison','neither a theoretical byte lower bound']:
 ck('comparison contract:'+s,s in source)
ck('no forced appendix page',r'\clearpage\n\appendices' not in (M/'main.tex').read_text())
report={'status':'PASS','check_count':len(checks),'preserved_scientific_files':len(paths),'pdf_pages':{'main':17,'supplement':52},'title_top_points':top,'new_experiment_runs':0,'checks':checks,'pdf_sha256':{n:sha(M/(n+'.pdf')) for n in ['main','supplement']}}
if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}))
