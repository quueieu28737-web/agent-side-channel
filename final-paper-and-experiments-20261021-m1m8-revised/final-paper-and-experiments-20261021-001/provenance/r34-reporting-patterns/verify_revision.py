"""R34 source-accounting and delivery verification; no empirical validity claim."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,hashlib,json,re,subprocess,sys
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='2a3310ab5c676655172fdc80d942c2fa7f877325'
sys.path.insert(0,str(P));from verify_package import closure
sys.path.insert(0,str(M/'tools'));import audit_check as a
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
protected=[n for n in old if n.startswith(('experiments/','evidence/')) or (n.startswith('provenance/') and n!='provenance/snapshot.json')]
prefix=P.relative_to(R).as_posix()+'/'
changed=subprocess.check_output(['git','diff','--name-only','-z',BASE,'--',prefix],cwd=R).decode().split('\0')
assert not any(n.startswith(prefix) and n[len(prefix):] in protected for n in changed)
for n in ['tables/r19-record-audit.tex','tables/r14-calibration-transfer.tex','tables/r9-frozen-reference.tex','sections/60-calibration-stability.tex']:
 assert (M/n).read_bytes()==prior(Path('manuscript')/n),n
for new,oldpath in [('pair-inventory.csv','provenance/r26-source-reconciliation/pair-inventory.csv'),('record-scopes.csv','provenance/r26-source-reconciliation/record-scope-and-cohort.csv'),('record-source-metadata.json','provenance/r26-source-reconciliation/record-audit.json'),('family-index.csv','provenance/r16-synthesis/holdout-matrix.csv')]:
 assert (M/'data'/new).read_bytes()==(P/oldpath).read_bytes(),new
proc=subprocess.run([sys.executable,str(M/'tools/audit_check.py'),'--json',str(O/'audit-check.json')],capture_output=True,text=True)
assert proc.returncode==0,proc.stdout+proc.stderr
ar=load(O/'audit-check.json');assert ar['failed']==0 and ar['passed']>=36
idx={r['id']:r for r in a.parse_record_index()};cells=a.parse_record_cells();mit={k:v for k,v in cells.items() if not v['contextual']}
assert len(idx)==39 and len(mit)==33 and sum(len(v['cells']) for v in cells.values())==351
pairs=list(csv.DictReader((M/'data/pair-inventory.csv').open(encoding='utf-8-sig',newline='')))
related=[r for r in pairs if r['related_subset']=='true'];assert len(pairs)==741 and len(related)==133
assert Counter(r['descriptive'] for r in related)=={'COMPATIBLE':17,'INCOMPATIBLE':105,'UNRESOLVED':11}
scopes={r['record_id']:r for r in csv.DictReader((M/'data/record-scopes.csv').open(encoding='utf-8-sig',newline=''))}
g=load(M/'data/granularity-sensitivity.json');assert len(g['variants'])==4
expected=[(39,133,17,105,11,0,0),(38,124,16,98,9,1,1),(35,103,10,83,9,1,4),(26,44,2,31,3,8,15)]
for v,ex in zip(g['variants'],expected):
 groups={rid:key for key,rs in v['memberships'].items() for rid in rs};assert set(groups)==set(idx)
 edges=defaultdict(list);hidden=[]
 for p in related:
  x,y=groups[p['left_unit']],groups[p['right_unit']]
  if x==y:hidden.append(p['pair_id'])
  else:edges[tuple(sorted((x,y)))].append(p)
 actual=Counter()
 for key,ps in edges.items():
  sts={x['descriptive'] for x in ps};actual[next(iter(sts)) if len(sts)==1 else 'MIXED']+=1
  saved=next(x for x in v['pairs'] if tuple(x['units'])==key)
  assert set(saved['pair_ids'])=={p['pair_id'] for p in ps}
 assert actual==v['counts'] and set(hidden)==set(v['hidden_within_unit_pairs'])
 vals=(len(v['memberships']),len(edges),*(actual[k] for k in ['COMPATIBLE','INCOMPATIBLE','UNRESOLVED','MIXED']),len(hidden))
 assert vals==ex,vals
q=load(M/'data/joint-query-identities.json');assert len(q['memberships'])==33
expect_counts=[(22,4),(22,5),(17,2),(20,2),(14,0)]
for (name,items),ex in zip(a.QUERIES.items(),expect_counts):
 eligible=[k for k,v in mit.items() if all(v['cells'][i-1]!='--' for i in items)]
 bound=[k for k,v in mit.items() if all(v['cells'][i-1]=='B' for i in items)]
 assert (len(eligible),len(bound))==ex
 assert set(q['queries'][name]['bound_ids'])==set(bound)
 for row in q['memberships']:
  k=row['record_id'];expect='B' if k in bound else ('E' if k in eligible else 'x');assert row[name]==expect
cross=load(M/'data/family-to-joint-crosswalk.json');assert len(cross)==8 and sum(bool(r['same_record']) for r in cross)==3
assert sum(len(r['same_record']) for r in cross)==5
src=load(M/'data/source-status-ledger.json');assert len(src['families'])==82 and len(src['records'])==39
assert src['family_counts']=={'preprint_cited':61,'venue_publication_listed':21}
for n,h in src['bibliography_hashes'].items():assert sha(M/n)==h
for r in src['records']:
 assert r['inference_binding']==cells[r['record_id']]['cells'][6]
 assert r['utility_binding']==cells[r['record_id']]['cells'][7]
 assert r['cost_binding']==cells[r['record_id']]['cells'][8]
 assert r['source_locator'] and r['archived_source_sha256']
dates=load(M/'data/bibliography-date-check.json');assert len(dates['future_citation_years'])==1
assert dates['inputsnatch_verification']['publisher_citation_year']==2027
main=(M/'main.tex').read_text();abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S)[1]
assert all(t not in abstract for t in ['105','17/133','8/15','2/20','GLM','690'])
assert all(t in abstract for t in ['82 study families','33 mitigation records','20 families','16 of 17','4 of 17','2 of 11','CachePrune'])
def expand(t):return re.sub(r'\\input\{([^}]+)\}',lambda m:expand((M/(m[1]+'.tex')).read_text()),t)
body=expand(main.split(r'\bibliographystyle')[0])
assert not re.search(r'\bExps?\s*[~. ]*[1-4]',body)
assert 'Reporting Patterns and Joint Defense Evidence' in body
assert 'five of the eight' in body and 'cost count is twice' in body
assert '16/17' in body and '6/17' in body and '9/11' in body
assert not any(s in body for s in ['105 different-object','eight of 15','8/15','17/133'])
assert 'tables/r33-pair-summary' not in main.split(r'\bibliographystyle')[0]
assert 'excluded from favorable evidence' in body
assert '13 measured extraction errors' in body
assert 'A usable reporting card' in body
banned=re.compile(r'independent(?:ly)?[ -]+(?:re[- ]?cod|cod)|blind[- ]human recod|independent coder agreement|inter[- ]rater reliability|irr_kit|coder2_sheet|proposed independent source-only',re.I)
for f in M.rglob('*.tex'):assert not banned.search(f.read_text()),f
for rel in ['irr/README.md','irr/coder2_sheet.csv','tools/irr_kit.py']:assert not (M/rel).exists()
bib=[];cites=set();pdfs={}
for f in M.glob('*.bib'):bib+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text())
assert len(bib)==len(set(bib))
for name in ['main','supplement']:
 files=closure(M,name+'.tex');text='\n'.join((M/n).read_text() for n in files if n.endswith('.tex'))
 labels=re.findall(r'\\label\{([^}]+)\}',text);assert len(labels)==len(set(labels)),Counter(labels)
 refs=set(re.findall(r'\\(?:ref|pageref|eqref)\{([^}]+)\}',text));assert refs<=set(labels),refs-set(labels)
 for c in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',text):cites.update(x.strip() for x in c.split(','))
 log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
 assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined|LaTeX Error',log)
 d=PdfReader(M/(name+'.pdf'));texts=[p.extract_text() for p in d.pages];full='\n'.join(texts)
 assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
 assert not banned.search(full.replace('\n',' '))
 assert not any(x in (str(d.metadata)+full).lower() for x in ['quueieu28737','c:/users/','c:\\users\\'])
 refpage=next(i+1 for i,t in enumerate(texts) if 'References' in t)
 pdfs[name]={'pages':len(d.pages),'references_start':refpage,'sha256':sha(M/(name+'.pdf'))}
 if name=='main':
  assert refpage<=13,refpage
  pdfs[name]['main_body_last_page']=refpage if texts[refpage-1].split('References',1)[0].strip() else refpage-1
  for term in ['All 33 mitigation records','Every family with B','Illustrative Case Study']:
   assert re.sub(r'\W','',term).lower() in re.sub(r'\W','',full).lower(),term
  casepage=next(i+1 for i,t in enumerate(texts) if 'Illustrative Case Study' in t);assert casepage>refpage
  pdfs[name]['appendix_case_page']=casepage
  nums=[int(k) for t in texts for k in re.findall(r'TABLE\s+(\d+)\.',t)];assert set(nums)==set(range(1,max(nums)+1)),nums
 else:assert 'S38.' in full
assert cites<=set(bib),cites-set(bib)
out={'revision':'R34-reporting-patterns','passed':True,'base_commit':BASE,'unchanged_scientific_and_prior_provenance_files':len(protected),'audit_checks_passed':ar['passed'],'record_judgments_changed':0,'pair_judgments_changed':0,'coarsening_variants_independently_recomputed':4,'joint_queries_recomputed':5,'publication_metadata_families':82,'source_scope_records':39,'reporting_patterns_check':'reporting-check.json','new_model_calls':0,'new_participant_data':0,'citation_keys':len(cites),'bibliography_keys':len(bib),'pdfs':pdfs,'scope':'Accounting, source identity, document and delivery consistency; not independent human validation or source-result replication.'}
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(out))
