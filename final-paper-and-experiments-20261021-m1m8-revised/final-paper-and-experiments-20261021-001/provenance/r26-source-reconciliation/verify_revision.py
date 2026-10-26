"""Check the R26 source overlay, immutable science, source closure and PDF copies."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pypdf import PdfReader
import hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='b192bd593f4d6ae6a958122fe6f80ecda048df06'
sys.path.insert(0,str(P));from verify_package import closure
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
protected=[n for n in old if n.startswith(('experiments/','evidence/')) or (n.startswith('provenance/') and n!='provenance/snapshot.json')]
with ThreadPoolExecutor(max_workers=8) as pool:
 for n,h in zip(protected,pool.map(lambda n:sha(P/n),protected)):assert h==old[n],n
print('PRESERVED_EVIDENCE_PASS',len(protected),flush=True)
tables=['r9-streaming','r9-dispatch','r9-cohorts','r9-frozen-reference','r9-crossfit','r9-localization','r9-flush','r9-controls','r11-model-replication','r14-calibration-transfer','r19-joint-bindings','r25-pair-cohorts','r25-joint-accounting']
checked=[]
for n in tables:
 f=Path('manuscript/tables')/(n+'.tex')
 if (P/f).exists():assert (P/f).read_bytes()==prior(f);checked.append(n)
for name in ['sections/37-transfer-tests.tex','sections/42-live-timing-main.tex','sections/60-calibration-stability.tex','tables/r9-audit-rules.tex']:
 assert (M/name).read_bytes()==prior(Path('manuscript')/name),name
main=(M/'main.tex').read_text()
def expand(t):return re.sub(r'\\input\{([^}]+)\}',lambda m:expand((M/(m[1]+'.tex')).read_text()),t)
body=expand(main.split(r'\bibliographystyle')[0])
assert not re.search(r'\bExps?\s*[~. ]*[1-4]',body)
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S)[1]
intro=(M/'sections/01-introduction.tex').read_text();conclusion=(M/'sections/12-conclusion.tex').read_text()
for part in [abstract,intro,conclusion]:
 for term in ['record-level comparison','configuration-level joint binding','deployment decisions']:assert term in part.lower(),term
assert intro.count(r'\item \textbf{')==3
assert all(x in abstract for x in ['82 study families','39 result records','CachePrune','attack generalization'])
assert '690' not in abstract and 'GLM' not in abstract
rq=(M/'sections/28-fingerprint-dependencies.tex').read_text()
assert all(x in rq for x in ['three model H','four mitigation families','attack-side model generalization','defense-side variation','source, target, held-out unit'])
scope=(M/'sections/04-scope.tex').read_text()
assert 'retrospective' in scope.lower() and 'SparLeak' in scope and 'Early Bird' in scope
assert 'pre-reinspection' in (M/'sections/65-audit-sensitivity.tex').read_text()
assert 'current matrix has 11 unverified' not in expand((M/'supplement.tex').read_text())
assert main.index(r'\input{sections/62-appendix-case-study}')>main.index(r'\appendices')>main.index(r'\bibliography{')
subprocess.run([sys.executable,str(O/'verify_analysis.py')],check=True)

cites=set();bib=[];pdfs={}
for f in M.glob('*.bib'):bib+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text())
assert len(bib)==len(set(bib))
for name in ['main','supplement']:
 files=closure(M,name+'.tex')
 text='\n'.join((M/n).read_text() for n in files if n.endswith('.tex'))
 labels=re.findall(r'\\label\{([^}]+)\}',text);assert len(labels)==len(set(labels)),Counter(labels)
 refs=set(re.findall(r'\\(?:ref|pageref|eqref)\{([^}]+)\}',text));assert refs<=set(labels),refs-set(labels)
 for c in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',text):cites.update(x.strip() for x in c.split(','))
 log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
 assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined|LaTeX Error',log)
 d=PdfReader(M/(name+'.pdf'));ts=[p.extract_text() for p in d.pages];full='\n'.join(ts)
 assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
 assert not any(x in (str(d.metadata)+full).lower() for x in ['quueieu28737','c:/users/','c:\\users\\'])
 refpage=next(i+1 for i,t in enumerate(ts) if 'References' in t)
 pdfs[name]={'pages':len(d.pages),'references_start':refpage,'sha256':sha(M/(name+'.pdf'))}
 if name=='main':
  assert len(d.pages)<=18 and refpage<=13
  bodypdf='\n'.join(ts[:refpage]).split('References',1)[0]
  assert not re.search(r'\bExp[s. ]*[1-4]',bodypdf)
  assert '690' not in bodypdf and 'MiniMax' not in bodypdf and 'GLM' not in bodypdf
  cp=next(i+1 for i,t in enumerate(ts) if 'Case Study: Applying' in t);assert cp>refpage
  assert 'Recorded contrasts for the worked case' in ts[cp-1] and '26.2' in ts[cp-1]
  nums=[int(k) for t in ts for k in re.findall(r'TABLE\s+(\d+)\.',t)]
  assert set(nums)==set(range(1,max(nums)+1)),nums
  end=refpage if ts[refpage-1].split('References',1)[0].strip() else refpage-1
  pdfs[name].update({'main_body_last_page':end,'appendix_case_page':cp,'appendix_case_pages':1,'main_body_empirical_sections':0})
 else:
  assert 'sections/66-source-reconciliation.tex' in files
  assert 'Source Reconciliation, Record Boundaries' in full
  assert 'S33.' in full and 'S34.' in full
assert cites<=set(bib),cites-set(bib)
out={'revision':'R26-source-reconciliation','passed':True,'base_commit':BASE,
 'unchanged_scientific_and_prior_provenance_files':len(protected),'unchanged_experimental_tables':checked,
 'new_experiments':0,'new_model_calls':0,'source_reporting_overlay':True,
 'three_sok_contributions_aligned':True,'main_body_empirical_sections':0,
 'citation_keys':len(cites),'bibliography_keys':len(bib),'pdfs':pdfs}
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(out))
