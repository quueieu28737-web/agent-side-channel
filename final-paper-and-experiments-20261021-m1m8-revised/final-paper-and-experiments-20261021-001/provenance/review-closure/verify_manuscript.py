"""Validate review corrections, frozen evidence, author provenance and PDFs.

No model calls, network access, fitting or new empirical experiments.
Requires pypdf. --save writes validation.json.
"""
from pathlib import Path,PurePosixPath
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv,hashlib,json,re,subprocess,sys
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
BASE='74ea9e8a50d9ca231332771b600ea4213654f08d'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def csvrows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))

def main():
 prior=read(O/'prior-package-manifest.json')['files']
 allowed={'README.md','artifact-index.json','provenance/snapshot.json','manuscript/main.tex','manuscript/supplement.tex'}
 allowed.update('manuscript/sections/'+x+'.tex' for x in ('03-methodology','04-scope','10-open-challenges','27-intervention-contracts','31-result-audit','34-search-update','37-transfer-tests'))
 allowed.update('manuscript/tables/'+x+'.tex' for x in ('core-family-map','family-audit-matrix','r5-main','result-lineage-example','result-record-schema','synthesis-decisions'))
 for n in ('main','supplement'):
  allowed.update({'manuscript/'+n+'.pdf','manuscript/'+n+'.bbl','pdf/'+n+'.pdf','provenance/build-logs/'+n+'.log','pdf/build-logs/'+n+'.log'})
 kept=sorted(set(prior)-allowed)
 with ThreadPoolExecutor(max_workers=12) as pool:
  for n,h in zip(kept,pool.map(lambda n:sha(P/n),kept)):assert h==prior[n],('Historical file changed',n)
 for script in (O/'build_tables.py',P/'provenance/sok-restructure/build_e9_tables.py',P/'provenance/sok-restructure/build_null_table.py'):
  subprocess.run([sys.executable,'-B',str(script),'--check'],check=True)
 concordance=read(O/'concordance.json')
 for n,h in concordance['sources'].items():assert sha(P/n)==h,n
 j=read(P/'experiments/reviewer-audit/combined_result_records.json');rr=j['baseline_records']+j['added_records']
 counts=Counter(x['citation_key'] for x in rr);assert len(rr)==39 and len(counts)==26
 a=csvrows(P/'experiments/revision-m1-m8/m6_split_checks.csv');mit={x['citation_key'] for x in a}
 assert len(a)==180 and len(mit)==20 and sum(counts[k] for k in mit)==33
 index=csvrows(P/'evidence/retained-release007/search-update/final-family-index.csv')
 core={r['citation_key'] for r in index if r['classification']=='core'}
 contextual=set(counts)-mit;rest=core-set(counts)
 assert len(index)==82 and len(core)==58 and len(contextual)==6 and len(rest)==32
 assert concordance['contextual_families']==sorted(contextual) and concordance['map_only_families']==sorted(rest)
 rows=csvrows(O/'family-record-concordance.csv');assert len(rows)==82 and len({x['citation_key'] for x in rows})==82
 assert {x['citation_key'] for x in rows}=={x['citation_key'] for x in index}
 for x in rows:
  k=x['citation_key'];assert int(x['result_records'])==counts[k] and int(x['audit_cells'])==(9 if k in mit else 0)
  assert x['record_ids']=='; '.join(r['unit_id'] for r in rr if r['citation_key']==k)
  source=next(r for r in index if r['citation_key']==k)
  for field in ('classification','source_version','source_locators'):assert x[field]==source[field],(k,field)
  group='adjacent' if k not in core else 'mitigation' if k in mit else 'contextual-record' if k in contextual else 'map-only'
  assert x['ledger_group']==group,k
 assert sum(int(x['result_records']) for x in rows)==39
 for item in read(O/'coding-columns.json'):
  f=P/item['source'];assert sha(f)==item['sha256'];data=csvrows(f)
  x=[r['coder1_workflow'] for r in data];y=[r['coder2_independent_expert'] for r in data];n=len(x)
  agree=sum(a==b for a,b in zip(x,y));cx=Counter(x);cy=Counter(y);pe=sum(cx[k]*cy[k] for k in set(x+y))/n**2
  assert item['n']==n and item['matches']==agree and abs(item['kappa']-(agree/n-pe)/(1-pe))<1e-12
  assert item['review_vs_final_differences']==sum(r['coder2_independent_expert']!=r['adjudicated_final'] for r in data)
 author=read(O/'author-verification-attestation.json')
 assert author['record_locator_verification']['records']==39 and author['record_locator_verification']['audit_cells']==180
 assert author['family_classification_review']['families']==82 and author['independent_blind_human_reliability'] is False
 e=(M/'sections/37-transfer-tests.tex').read_text();method=(M/'sections/03-methodology.tex').read_text();s=(M/'sections/40-evidence-concordance.tex').read_text()
 for token in ('690','414','276',r'60.6\%/65.5\%',r'60.5\%/60.2\%','post hoc','inter-arrival','flush','unused E4'):assert token.lower() in e.lower(),token
 for token in ('39 result records','180 audit cells','82','author-verification','not independent human inter-rater reliability'):assert token in method,token
 for token in ('33 result records','one record each','adjudicated','Unused identifier','no timing-aware or closed-loop result','positive and negative customers'):assert token in s,token
 assert (M/'main.tex').read_text().index(r'\bibliography{')<(M/'main.tex').read_text().index(r'\appendices')
 pages={};hashes={}
 for n in ('main','supplement'):
  f=P/'pdf'/(n+'.pdf');data=f.read_bytes();assert data==(M/f.name).read_bytes()
  if (P.parents[1]/'.git').exists():assert data==(P.parents[1]/f.name).read_bytes()
  doc=PdfReader(f);ts=[x.extract_text() for x in doc.pages];pages[n]=len(ts);hashes[n]=sha(f)
  for page in doc.pages:assert float(page.mediabox.width)==612 and float(page.mediabox.height)==792
  text='\n'.join(ts);joined=(str(doc.metadata)+text).lower()
  for private in ('quueieu28737','administrator','c:/users/','c:\\users\\','@gmail.com'):assert private not in joined
  refs=next(i+1 for i,t in enumerate(ts) if re.search(r'(?m)^References\s*$',t))
  if n=='main':
   app=next(i+1 for i,t in enumerate(ts) if 'Appendix A.' in t);assert refs==13 and app==17 and len(ts)==17
   assert '10. Conclusion' in ts[refs-1];pages.update(main_body=refs,references_start=refs,appendix_start=app)
   compact=re.sub(r'\s+','',text)
   for triple in ('91.7[82.1,100.0]','85.5[76.6,93.4]','50.7[50.0,57.3]','59.9[50.5,71.7]'):assert triple in compact,triple
   for token in ('B: bound','P: partial','U: unreported'):assert token.replace(' ','') in compact,token
   assert 'τ-bench' in text or 'τ -bench' in text
  else:
   start=next(i+1 for i,t in enumerate(ts) if 'S18. Evidence Concordance' in t)
   assert start==26 and refs==28 and len(ts)==31;pages.update(supplement_s18_start=start,supplement_references_start=refs)
  for folder in ('provenance/build-logs','pdf/build-logs'):
   log=(P/folder/(n+'.log')).read_text(errors='replace')
   for bad in ('Overfull','undefined references','undefined on input line','multiply defined','Float too large'):assert bad not in log,(n,bad)
 visual=read(O/'visual_qa.json');assert visual['status']=='RENDERED_PAGES_INSPECTED' and visual['pdf_sha256']==hashes
 idx=read(P/'artifact-index.json')
 for n in [p for v in idx['modules'].values() for p in v['paths']]+idx['current_publication']:
  p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and ':' not in n
  if n=='provenance/review-closure/validation.json' and '--save' in sys.argv:continue
  assert (P/n).is_file(),n
 full=read(P/'experiments/sp2027-r4-full-20261023/validation.json');assert full['status']=='VERIFIED' and full['episodes']==690
 receipt={'status':'REVIEW_CLOSURE_TABLES_CONCORDANCE_CODING_PRESERVATION_AND_PDF_PASS','base_commit':BASE,
 'preserved_prior_package_files':len(kept),'experimental_files_changed':0,'new_model_calls':0,
 'cohort':{'training':414,'test':276,'total':690},'families':82,'core':58,'audit_cells':180,
 'ledger':{'mitigation_families':20,'mitigation_records':33,'contextual_families':6,'contextual_records':6,'map_only_core_families':32},
 'author_verification_scope':'Explicit author confirmation; not external independent certification',
 'source_results_sha256':sha(P/'experiments/sp2027-r4-full-20261023/results.json'),
 'pdf_pages':pages,'pdf_sha256':hashes,'scope':'Manuscript correction and evidence reconciliation. No new timing, closed-loop, population or independent-coder experiment.'}
 if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
