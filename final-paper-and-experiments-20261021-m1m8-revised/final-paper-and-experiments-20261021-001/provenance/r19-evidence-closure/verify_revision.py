"""Verify synthesis coverage, provenance, original evidence and final PDF delivery."""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
import csv,json,re,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
h=load(P/'provenance/r16-synthesis/holdout-matrix.json');v=load(P/'provenance/r16-synthesis/record-mode-inventory.json')
src=P/'evidence/retained-release007/search-update/final-family-index.csv'
families=list(csv.DictReader(src.open(encoding='utf-8-sig')))
assert sha(src)==h['source_sha256']
assert len(h['rows'])==len(set(r['citation_key'] for r in h['rows']))==82
assert {r['citation_key'] for r in families}=={r['citation_key'] for r in h['rows']}
assert Counter(r['classification'] for r in h['rows'])=={'core':58,'adjacent':24}
for r,f in zip(h['rows'],families):
 assert r['citation_key']==f['citation_key'] and r['source_locators']==f['source_locators'] and r['source_url']==f['source_url']
 assert len(r['axes'])==6 and set(r['axes'].values())<=set('HVX?-')
 for k,s in r['archived_extraction'].items():assert s==f.get(k,'')
for scope in ['all','core','adjacent']:
 for a in h['axes']:
  assert dict(Counter(r['axes'][a] for r in h['rows'] if scope=='all' or r['classification']==scope))==h['summary'][scope][a]
lpath=P/'experiments/reviewer-audit/combined_result_records.json';l=load(lpath);records=l['baseline_records']+l['added_records']
assert sha(lpath)==v['source_sha256'] and len(v['records'])==39
assert set(r['record'] for r in v['records'])==set(r['unit_id'] for r in records)
assert len(set(r['family'] for r in v['records']))==26
assert Counter(r['mode_group'] for r in v['records'])==v['counts']
for r,s in zip(v['records'],records):assert r['source_sha256']==s.get('source_sha256') and r['family']==s['citation_key']
# Check all historical experimental/evidence bytes, not just aggregate metrics.
prior=load(O/'prior-SHA256SUMS.json')['files'];old=[n for n in prior if n.startswith(('experiments/','evidence/'))]
with ThreadPoolExecutor(max_workers=8) as pool:
 for n,d in zip(old,pool.map(lambda n:sha(P/n),old)):assert d==prior[n],n
pdfs={};texts={}
for n in ['main','supplement']:
 d=PdfReader(M/(n+'.pdf'));text='\n'.join(p.extract_text() for p in d.pages);texts[n]=text
 assert all(sha(M/(n+'.pdf'))==sha(f/(n+'.pdf')) for f in [R,P/'pdf'])
 log=(P/'pdf/build-logs'/(n+'.log')).read_text()
 assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined',log)
 assert not any(s in text.lower() for s in ['quueieu28737','c:/users/','c:\\users\\'])
 assert all(re.search(r'\b'+r['id']+r'\b',text) for r in h['rows'])
 pdfs[n]={'pages':len(d.pages),'sha256':sha(M/(n+'.pdf'))}
 if n=='main':
  refpages=[i+1 for i,p in enumerate(d.pages) if 'References' in p.extract_text()];assert min(refpages)<=13
  pdfs[n]['references_start']=min(refpages)
  body_table_pages={int(t):i+1 for i,p in enumerate(d.pages) for t in re.findall(r'TABLE\s+(\d+)\.',p.extract_text()) if int(t)<=21}
  assert set(body_table_pages)==set(range(1,22)) and max(body_table_pages.values())<=13,body_table_pages
  pdfs[n]['main_table_pages']=body_table_pages
  assert all(s in text for s in ['70.8','67.3','37/50','33/50','1.45','1.51'])
assert 'S27. Complete Record-Mode Synthesis' in texts['supplement']
for name,text in texts.items():
 compact=re.sub(r'\s+',' ',text)
 for pattern in [r'41\.7\s*%',r'25/60',r'Origin[ ~-]+[AB]\b',r'independent human/expert dual-coding',r'49 arXiv-only',r'two-stage agreement']:
  assert not re.search(pattern,compact,re.I),(name,pattern)
 assert 'κ' not in text
assert 'AI tools assisted' in texts['main']
assert load(O/'data-check.json')['passed']
audit=load(O/'summary.json');assert audit['records']==39 and audit['record_cells']==351 and audit['all_pairs']==741
assert audit['related_descriptive']=={'COMPATIBLE':17,'INCOMPATIBLE':105,'UNRESOLVED':11}
overlay=load(O/'family-status-overlay.json');assert overlay['family_count']==20
assert overlay['distributions']['R8']=={'Bound':4,'Partial':2,'NR-R':11,'NA':3}
assert '19.4 for GLM' in re.sub(r'\s+',' ',texts['main'])
assert '351' in texts['supplement']
assert all(s in texts['main'] for s in ['741','133','608','2/20','18.65','4.66'])
report={'revision':'R19-evidence-closure','passed':True,'family_rows':82,'holdout_cells':492,'core':58,'adjacent':24,'record_rows':39,'record_families':26,'record_audit_cells':351,'record_pairs':741,'related_pairs':133,'mode_counts':v['counts'],'preserved_scientific_files':len(old),'pdfs':pdfs,'scope':'Source-bound archived extraction synthesis; coverage/hash/PDF checks do not certify independent source recoding or success of every coded transfer.'}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
