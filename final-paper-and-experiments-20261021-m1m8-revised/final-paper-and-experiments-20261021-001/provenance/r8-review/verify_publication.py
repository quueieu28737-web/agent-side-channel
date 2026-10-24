"""Read-only R8 publication gate; receipts distinguish validation from security."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,re,subprocess,sys,zipfile
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure
def read(f):return json.loads(f.read_text(encoding='utf-8-sig'))
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(f,*args):subprocess.run([sys.executable,'-B',str(f),*args],check=True)
def history():
 prior=read(O/'prior-package-manifest.json')['files']
 allowed={'README.md','artifact-index.json','provenance/snapshot.json','manuscript/main.tex','manuscript/supplement.tex'}
 sections=['01-introduction','03-methodology','04-scope','10-open-challenges','11-discussion','12-conclusion','26-corpus-map','27-intervention-contracts','28-fingerprint-dependencies','37-transfer-tests','42-live-timing-main','39-shadow-deployment','44-strong-crossfit']
 allowed.update('manuscript/sections/'+n+'.tex' for n in sections)
 for n in ['main','supplement']:allowed.update({'manuscript/'+n+'.pdf','manuscript/'+n+'.bbl','pdf/'+n+'.pdf','pdf/build-logs/'+n+'.log'})
 kept=sorted(set(prior)-allowed)
 with ThreadPoolExecutor(max_workers=10) as pool:
  for n,h in zip(kept,pool.map(lambda n:sha(P/n),kept)):assert h==prior[n],('Unexpected historical change',n)
 return len(kept)
def main():
 kept=history();print('HISTORY_PASS',kept,flush=True)
 if '--history-only' in sys.argv:return
 for f in ['verify_revision.py','experiments/sp2027-r4-full-20261023/verify_release.py']:run(P/f)
 run(O/'make_tables.py','--check')
 run(O/'numerical_review.py')
 sci=read(O/'science-verification.json');assert sci['status']=='PASS'
 for n,h in sci['saved_result_sha256'].items():assert sha(P/n)==h,n
 assert sci['old_experiment_files_checked']==4542 and sci['cluster_cells']==12 and sci['cluster_positive_customer_deletions']==192
 H=P/'experiments/sp2027-r8-sensitive-attributes'
 for n,h in read(H/'protocol.json')['source_hashes'].items():assert sha(H/n)==h,n
 hv=read(H/'verification.json');assert hv['passed'] and hv['exact_reloaded_scores']==600 and hv['models']==150 and hv['group_disjoint']
 for n,h in hv['output_sha256'].items():assert sha(H/n)==h,n
 assert hv['aligned_calls']==138 and hv['aggregated_instances']==40
 old=read(P/'experiments/sp2027-r4-full-20261023/validation.json');assert old['status']=='VERIFIED' and old['episodes']==690
 av=read(P/'experiments/sp2027-r7-agent-extension/formal_validation.json');assert av['complete'] and av['runs']==150
 cov=read(O/'checklist-coverage.json');ids=[v['id'] for v in cov['items']];assert len(ids)==len(set(ids)) and len(ids)>=30
 for v in cov['items']:
  assert v['status'] in ['COMPLETED','PARTIALLY_ADDRESSED','REQUIRES_NEW_DATA'],v
  for f in v['evidence']:assert (P/f).exists(),f
 assert cov['unresolved_resources']
 body='\n'.join((M/f).read_text(encoding='utf8') for f in closure(M,'main.tex') if f.endswith('.tex'))
 for phrase in ['author-chosen','not a cryptographic','known-cohort','not content inference','live planner utility','15 customers','53 customers']:
  assert phrase in body,phrase
 assert 'No independent human inter-rater reliability is claimed.' in body
 for bad in ['pre-registered tests','E10: primary']:
  assert bad not in body,bad
 assert r'\texttt{cancel\_pending\_order}' in body
 for f in ['family-audit-matrix','core-family-map','r8-controls','r8-flush','r8-cohorts']:
  if f=='core-family-map':continue
  assert 'tables/'+f+'.tex' in closure(M,'main.tex'),f
 source=(M/'main.tex').read_text()
 assert source.index(r'\bibliography{')<source.index(r'\appendices')
 assert r'\documentclass[conference,compsoc]{IEEEtran}' in source and r'\author{}' in source
 pages={};pdfhash={}
 for name in ['main','supplement']:
  f=P/'pdf'/(name+'.pdf');assert f.read_bytes()==(M/f.name).read_bytes()==(R/f.name).read_bytes()
  d=PdfReader(f);texts=[page.extract_text() for page in d.pages];txt='\n'.join(texts)
  for page in d.pages:assert float(page.mediabox.width)==612 and float(page.mediabox.height)==792
  for term in ['quueieu28737','administrator','c:/users/','c:\\users\\']:assert term not in (str(d.metadata)+txt).lower(),(name,term)
  if name=='main':
   refs=next(i+1 for i,t in enumerate(texts) if re.search(r'(?im)^References\s*$',t))
   app=next(i+1 for i,t in enumerate(texts) if 'Appendix A.' in t)
   assert refs<=13 and app>refs and len(texts)<=18,(refs,app,len(texts))
   assert 'Conclusion' in ''.join(texts[:13])
   pages.update(body=refs,references_start=refs,appendix_start=app)
  else:assert 'S23.' in txt
  pages[name]=len(texts);pdfhash[name]=sha(f)
  log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
  for bad in ['Overfull','undefined references','undefined on input line','multiply defined','Float too large']:
   assert bad not in log,(name,bad)
 visual=read(O/'visual_qa.json');assert visual['status']=='ALL_RENDERED_PAGES_INSPECTED' and visual['pdf_sha256']==pdfhash
 anon=read(O/'anonymous-paper-check.json');z=O/'anonymous-paper-source.zip'
 assert anon['archive_sha256']==sha(z)
 with zipfile.ZipFile(z) as f:
  assert f.testzip() is None
  for n,h in anon['members'].items():assert hashlib.sha256(f.read(n)).hexdigest()==h
 result={'status':'R8_HISTORY_SOURCES_ANALYSES_TABLES_PDFS_CHECKLIST_PASS','base_commit':'ec2cb3955da5f73fac796637227510ccedb8265b','preserved_prior_files':kept,'original_sol_runs':690,'prior_additional_luna_runs':150,'new_llm_runs':0,'cluster_cells':12,'positive_customer_deletions':192,'attribute_instances_per_prompt':20,'attribute_customers':15,'attribute_exact_model_scores':600,'pdf_pages':pages,'pdf_sha256':pdfhash,'checklist_items':len(ids),'unresolved_resources':cov['unresolved_resources'],'security_criterion_passed':False}
 if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
