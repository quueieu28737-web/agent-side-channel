"""Check the M1 wording revision without relabeling or rerunning experiments."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
import hashlib,json,re,subprocess
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='aa34c70ee27c74a3cf92e27109a84865b75ce1ec'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
preserve=[n for n in old if n.startswith(('experiments/','evidence/','provenance/r19-evidence-closure/'))]
with ThreadPoolExecutor(max_workers=8) as pool:
 for n,h in zip(preserve,pool.map(lambda n:sha(P/n),preserve)):assert h==old[n],n
for n in ['sections/03-methodology.tex','sections/10-open-challenges.tex']:
 assert (M/n).read_bytes()==prior(Path('manuscript')/n),n
# Preserve every numeric experimental table, the original coding, and source locators.
allowed={'tables/r19-joint-bindings.tex','tables/r9-audit-rules.tex','tables/r9-rq-findings.tex'}
for n,h in old.items():
 if n.startswith('manuscript/tables/') and n[len('manuscript/'):] not in allowed:assert sha(P/n)==h,n
audit=json.loads((P/'provenance/r19-evidence-closure/summary.json').read_text())
assert audit['records']==39 and audit['record_cells']==351 and audit['all_pairs']==741
table=(M/'tables/r19-joint-bindings.tex').read_text()
assert '2/20 & 1 & 1' in table and '4/22 & 3 & 3' in table and '5/22 & 3 & 4' in table
assert 'CachePrune alone' in table
alltex='\n'.join(x.read_text(encoding='utf8') for x in M.rglob('*.tex'))
citekeys=set()
for group in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',alltex):citekeys.update(x.strip() for x in group.split(','))
bibkeys=[]
for f in M.glob('*.bib'):bibkeys+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text(encoding='utf8'))
assert len(bibkeys)==len(set(bibkeys)) and citekeys<=set(bibkeys)
pdfs={}
for name in ['main','supplement']:
 d=PdfReader(M/(name+'.pdf'));texts=[x.extract_text() for x in d.pages];text='\n'.join(texts)
 assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
 log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
 assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined',log)
 assert all(x not in text.lower() for x in ['quueieu28737','c:/users/','c:\\users\\'])
 # User asked to withdraw newly proposed independent-coding/error-audit passages.
 assert 'Reliability status and prospective verification' not in text
 assert 'random audit of initial AI-field errors' not in text
 assert not re.search(r'Cohen.{0,12}(?:kappa|κ)',text,re.I) and 'κ' not in text
 refs=min(i+1 for i,t in enumerate(texts) if 'References' in t)
 pdfs[name]={'pages':len(d.pages),'sha256':sha(M/(name+'.pdf')),'references_start':refs}
 if name=='main':
  assert refs<=13
  assert 'CachePrune alone' in text
  assert 'AI tools assisted' in text
  body={int(k):i+1 for i,t in enumerate(texts) for k in re.findall(r'TABLE\s+(\d+)\.',t) if int(k)<=21}
  assert set(body)==set(range(1,22)) and max(body.values())<=13
  pdfs[name]['main_table_pages']=body
 else:
  assert 'why a binding is necessary' in text.lower()
  assert 'Claim-conditioned necessity' in text
report={'revision':'R20-claim-conditioned-audit','passed':True,'base_commit':BASE,'unchanged_scientific_and_r19_provenance_files':len(preserve),'coding_changed':False,'independent_recoding_conducted':False,'ai_error_audit_conducted':False,'record_rows':39,'record_cells':351,'record_pairs':741,'join_record_fraction':'2/20','join_supporting_family':'CachePrune','join_families':1,'join_configurations':1,'citation_keys':len(citekeys),'bib_keys':len(bibkeys),'pdfs':pdfs,'scope':'Wording and necessity-of-binding clarification. Original methods/ethics and all archived coding and experimental results are unchanged.'}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(report))
