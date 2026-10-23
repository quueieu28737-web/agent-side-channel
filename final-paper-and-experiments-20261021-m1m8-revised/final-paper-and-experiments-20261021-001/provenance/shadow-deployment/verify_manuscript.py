"""Verify the deployment revision and preservation of all frozen evidence.

Requires pypdf; no model calls, fitting or network access. --save writes a receipt.
The prior SoK verifier remains an immutable historical-layout check.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,re,subprocess,sys
from pypdf import PdfReader

O=Path(__file__).resolve().parent
P=O.parents[1]
M=P/'manuscript'
S=P/'provenance/sok-restructure'
BASE='35d43a8d4866737571faf4cc3f91581bdd4dc144'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
 prior=read(O/'prior-package-manifest.json')['files']
 allowed={'README.md','artifact-index.json','provenance/snapshot.json',
          'manuscript/main.tex','manuscript/supplement.tex',
          'manuscript/sections/37-transfer-tests.tex','manuscript/sections/10-open-challenges.tex'}
 for n in ('main','supplement'):
  allowed.update({'manuscript/'+n+'.pdf','manuscript/'+n+'.bbl','pdf/'+n+'.pdf',
                  'provenance/build-logs/'+n+'.log','pdf/build-logs/'+n+'.log'})
 kept=sorted(set(prior)-allowed)
 with ThreadPoolExecutor(max_workers=12) as pool:
  for n,h in zip(kept,pool.map(lambda n:sha(P/n),kept)):
   assert h==prior[n],('Historical file changed',n)
 for script in ('build_sok_tables.py','build_e9_tables.py','build_null_table.py','verify_r5_tables.py'):
  subprocess.run([sys.executable,'-B',str(S/script),'--check'],check=True)
 source=read(O/'sources.json')
 assert len(source['sources'])==5 and source['new_empirical_results'] is False
 bib=(M/'refs-deployment.bib').read_text()
 assert set(re.findall(r'@\w+\{([^,]+)',bib))=={x['key'] for x in source['sources']}
 for x in source['sources']:assert x['url'] in bib,x['key']
 e=(M/'sections/37-transfer-tests.tex').read_text()
 d=(M/'sections/10-open-challenges.tex').read_text()
 s=(M/'sections/39-shadow-deployment.tex').read_text()
 for token in (r'73.9\%',r'66.1\%/55.5\%',r'50.0\%/50.0\%','690','414','276','2,760','110/138','105/138',
               'Transport link versus dispatch boundary','Planner-visible equivalence','not such a tunnel','prefix-only'):
  assert token in e,token
 for token in ('Authorized reads and verified no-ops','Provider-supported isolation','trusted MCP/tool gateway','deployment design'):
  assert token in d,token
 for token in ('not been evaluated as production integrations','fixed-length','fail closed','not automatically reproduce production latency',
               'Tool provider','Downstream link','committed','not a general substitute'):
  assert token.lower() in s.lower(),token
 assert (M/'main.tex').read_text().index(r'\bibliography{') < (M/'main.tex').read_text().index(r'\appendices')
 assert 'sections/39-shadow-deployment' in (M/'supplement.tex').read_text()
 index=read(P/'artifact-index.json')
 paths=[n for x in index['modules'].values() for n in x['paths']]+index['current_publication']
 for n in paths:
  q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts and ':' not in n
  if n=='provenance/shadow-deployment/validation.json' and '--save' in sys.argv:continue
  assert (P/n).is_file(),n
 pages={};hashes={}
 for name in ('main','supplement'):
  pdf=P/'pdf'/(name+'.pdf'); data=pdf.read_bytes()
  assert data==(M/pdf.name).read_bytes()
  if (P.parents[1]/'.git').exists():assert data==(P.parents[1]/pdf.name).read_bytes()
  doc=PdfReader(pdf);pages[name]=len(doc.pages);hashes[name]=sha(pdf)
  ts=[x.extract_text() for x in doc.pages]
  for x in doc.pages:assert float(x.mediabox.width)==612 and float(x.mediabox.height)==792
  joined=(str(doc.metadata)+'\n'.join(ts)).lower()
  for private in ('quueieu28737','administrator','c:/users/','c:\\users\\','@gmail.com'):assert private not in joined
  refs=next(i+1 for i,t in enumerate(ts) if re.search(r'(?m)^References\s*$',t))
  if name=='main':
   app=next(i+1 for i,t in enumerate(ts) if 'Appendix A.' in t)
   assert refs<=13 and app>refs and len(doc.pages)<=18
   assert '10. Conclusion' in ts[refs-1]
   pages.update(main_body=refs,references_start=refs,appendix_start=app)
  else:
   section=next(i+1 for i,t in enumerate(ts) if 'S17. Shadow Cover:' in t)
   assert section<refs
   pages.update(supplement_s17_start=section,supplement_references_start=refs)
  for folder in ('provenance/build-logs','pdf/build-logs'):
   log=(P/folder/(name+'.log')).read_text(errors='replace')
   for bad in ('Overfull','undefined references','undefined on input line','multiply defined','Float too large'):assert bad not in log,(name,bad)
 assert pages['main']==17 and pages['supplement']==29
 visual=read(O/'visual_qa.json')
 assert visual['status']=='RENDERED_PAGES_INSPECTED' and visual['pdf_sha256']==hashes
 full=read(P/'experiments/sp2027-r4-full-20261023/validation.json')
 assert full['episodes']==690 and full['status']=='VERIFIED'
 receipt={'status':'SHADOW_DEPLOYMENT_BOUNDARIES_SOURCES_PRESERVATION_AND_PDF_PASS','base_commit':BASE,
  'preserved_prior_package_files':len(kept),'experimental_files_changed':0,'new_model_calls':0,
  'cohort':{'training':414,'test':276,'total':690},'core_families':58,'audit_cells':180,
  'new_official_references':5,'source_ledger_sha256':sha(O/'sources.json'),
  'source_results_sha256':sha(P/'experiments/sp2027-r4-full-20261023/results.json'),
  'pdf_pages':pages,'pdf_sha256':hashes,
  'scope':'Architecture and manuscript revision; existing evidence and tables unchanged. No production deployment or full-tunnel experiment.'}
 if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
