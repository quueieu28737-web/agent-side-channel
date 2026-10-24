"""Current E13 manuscript/source/history/PDF verification; old receipts stay historical."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,re,subprocess,sys
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';D=P/'experiments/sp2027-r6-timing';R=P.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 prior=read(O/'prior-package-manifest.json')['files']
 allowed={'README.md','artifact-index.json','provenance/snapshot.json','manuscript/main.tex','manuscript/supplement.tex'}
 allowed.update('manuscript/sections/'+n+'.tex' for n in ('01-introduction','12-conclusion','37-transfer-tests','10-open-challenges','39-shadow-deployment','40-evidence-concordance','30-reproducibility-guide'))
 for n in ('main','supplement'):
  allowed.update({'manuscript/'+n+'.pdf','manuscript/'+n+'.bbl','pdf/'+n+'.pdf','provenance/build-logs/'+n+'.log','pdf/build-logs/'+n+'.log'})
 kept=sorted(set(prior)-allowed)
 with ThreadPoolExecutor(max_workers=12) as pool:
  for name,h in zip(kept,pool.map(lambda name:sha(P/name),kept)):assert prior[name]==h,('Prior evidence changed',name)
 for script in (D/'make_tables.py',P/'provenance/review-closure/build_tables.py',P/'provenance/sok-restructure/build_e9_tables.py',P/'provenance/sok-restructure/build_null_table.py'):
  subprocess.run([sys.executable,'-B',str(script),'--check'],check=True)
 ev=read(D/'validation.json');assert ev['total_sessions']==4140 and not ev['failures'] and ev['early_cell_sends']==0
 assert ev['results_sha256']==sha(D/'results.json') and ev['attacker_freeze_sha256']==sha(D/'attacker_freeze.json')
 reproduction=read(D/'reproduction_validation.json')
 assert reproduction['status']=='FROZEN_MODELS_ALL_PREDICTIONS_AND_METRICS_REPRODUCED'
 for name,h in reproduction['outputs'].items():assert sha(D/name)==h
 assert reproduction['analysis_sha256']==sha(D/'analyze.py') and reproduction['reproduction_code_sha256']==sha(D/'reproduce.py')
 result=read(D/'results.json');body=(M/'sections/42-live-timing-main.tex').read_text(encoding='utf-8')
 def pair(c,v='suite'):
  return '/'.join(f"{result['cells']['|'.join(('baseline',c,v,t))]['ba']['point']*100:.1f}" for t in ('cancel','return'))
 for c,v in (('shadow_serial','size_order'),('shadow_serial','suite'),('shadow_parallel2','suite'),('tunnel_2ms','suite'),('tunnel_5ms','suite')):
  assert pair(c,v)+r'\%' in body,('Narrative BA differs',c,v)
 delta=result['contrasts']['baseline|shadow_serial|suite|cancel-size']
 expected=f"{delta['point']*100:.1f} points (95\\% paired interval [{delta['ci95'][0]*100:.1f},{delta['ci95'][1]*100:.1f}])"
 assert expected in body,'Narrative paired contrast differs'
 supp=(M/'sections/41-live-timing.tex').read_text(encoding='utf-8')
 for target in ('cancel','return'):
  delta=result['contrasts']['baseline|shadow_serial|suite|'+target+'-raw']
  value=f"{-delta['point']*100:.1f}";lo=f"{-delta['ci95'][1]*100:.1f}";hi=f"{-delta['ci95'][0]*100:.1f}"
  assert value in supp and f'[{lo},{hi}]' in supp,'Supplement effect differs'
 full=read(P/'experiments/sp2027-r4-full-20261023/validation.json');assert full['episodes']==690 and full['status']=='VERIFIED'
 author=read(P/'provenance/review-closure/author-verification-attestation.json')
 assert author['independent_blind_human_reliability'] is False
 source='\n'.join(p.read_text(encoding='utf-8') for p in [M/'main.tex',M/'sections/42-live-timing-main.tex',M/'sections/41-live-timing.tex',M/'sections/10-open-challenges.tex'])
 for text in ('4,140','414/276','timing','266','665','LLM generation','WAN','customer'):
  assert text.lower() in source.lower(),text
 assert (M/'main.tex').read_text().index(r'\bibliography{')<(M/'main.tex').read_text().index(r'\appendices')
 pages={};hashes={}
 for n in ('main','supplement'):
  f=P/'pdf'/(n+'.pdf');assert f.read_bytes()==(M/f.name).read_bytes()==(R/f.name).read_bytes()
  doc=PdfReader(f);ts=[p.extract_text() for p in doc.pages];text='\n'.join(ts)
  for page in doc.pages:assert float(page.mediabox.width)==612 and float(page.mediabox.height)==792
  for private in ('quueieu28737','administrator','c:/users/','c:\\users\\','@gmail.com'):assert private not in (str(doc.metadata)+text).lower()
  refs=next(i+1 for i,t in enumerate(ts) if re.search(r'(?m)^References\s*$',t))
  if n=='main':
   app=next(i+1 for i,t in enumerate(ts) if 'Appendix A.' in t)
   assert refs<=13 and app>refs and len(ts)<=18,(refs,app,len(ts))
   assert any('Conclusion' in t for t in ts[:13]) and 'E13' in text and '4,140' in text
   table_page=next(i+1 for i,t in enumerate(ts) if 'e13:measuredlivetool' in re.sub(r'\s+','',t).lower())
   assert table_page<=13,('E13 float exceeds body limit',table_page)
   for token in ('B: bound','P: partial','U: unreported'):assert token.replace(' ','') in re.sub(r'\s+','',text)
   pages.update(main_body=refs,main_references_start=refs,main_appendix_start=app)
  else:
   assert 'S19.' in text and 'Live Tool Timing' in text and '4,140' in text
   pages['supplement_references_start']=refs
  pages[n]=len(ts);hashes[n]=sha(f)
  for folder in ('provenance/build-logs','pdf/build-logs'):
   log=(P/folder/(n+'.log')).read_text(errors='replace')
   for bad in ('Overfull','undefined references','undefined on input line','multiply defined','Float too large'):assert bad not in log,(n,bad)
 visual=read(O/'visual_qa.json');assert visual['status']=='RENDERED_PAGES_INSPECTED' and visual['pdf_sha256']==hashes
 result={'status':'E13_LIVE_MEASUREMENTS_HISTORY_NUMBERS_SOURCE_AND_PDF_PASS',
         'base_commit':'7ec40be9db177fd5f3966f6920cee540728802ec','preserved_prior_package_files':len(kept),
         'new_tls_sessions':4140,'source_model_runs':690,'new_model_calls':0,
         'experiment_validation_sha256':sha(D/'validation.json'),'pdf_pages':pages,'pdf_sha256':hashes,
         'scope':'New local live-tool timing/latency/tunnel measurements; no new LLM generations, production deployment or independent customer cohort'}
 if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
