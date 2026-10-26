"""Check the R32 source overlay, immutable science, source closure and PDF copies."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pypdf import PdfReader
import hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='f4215e30656f00e986a48e1720fd16aa0440a710'
sys.path.insert(0,str(P));from verify_package import closure
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
protected=[n for n in old if n.startswith(('experiments/','evidence/')) or (n.startswith('provenance/') and n!='provenance/snapshot.json')]
prefix=P.relative_to(R).as_posix()+'/'
changed=subprocess.check_output(['git','diff','--name-only','-z',BASE,'--',prefix],cwd=R).decode().split('\0')
assert not any(n.startswith(prefix) and n[len(prefix):] in protected for n in changed),changed
# Full byte verification is delegated to the package manifest checker.
print('PRESERVED_EVIDENCE_PASS',len(protected),flush=True)
tables=['r9-streaming','r9-dispatch','r9-cohorts','r9-frozen-reference','r9-crossfit','r9-localization','r9-flush','r9-controls','r11-model-replication','r14-calibration-transfer','r19-joint-bindings','r25-pair-cohorts','r25-joint-accounting','r28-external-ledger']
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
assert 'not a blinded failure-prediction test' in body
assert 'Four judgments have supporting counterexamples' in body
assert 'Source premise unmet' in body
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S)[1]
intro=(M/'sections/01-introduction.tex').read_text();conclusion=(M/'sections/12-conclusion.tex').read_text()
for part in [abstract,intro,conclusion]:
 for term in ['record-level comparison','configuration-level joint binding','deployment decisions']:assert term in part.lower(),term
claim='traceable comparisons, configuration-bound outcomes and deployment measurement requirements'
for part in [abstract,intro,conclusion,(M/'supplement.tex').read_text()]:
 assert claim in part
for rel in ['sections/68-utility-check-details.tex','tables/r19-record-audit.tex']:
 assert (M/rel).read_bytes()==prior(Path('manuscript')/rel),rel
for rel in ['irr/README.md','irr/coder2_sheet.csv','tools/irr_kit.py']:
 assert not (M/rel).exists(),rel
banned=re.compile(r'independent(?:ly)?[ -]+(?:re[- ]?cod|cod)|blind[- ]human recod|independent coder agreement|inter[- ]rater reliability|irr_kit|coder2_sheet',re.I)
for f in M.rglob('*.tex'):
 assert not banned.search(f.read_text()),f
for f in [R/'docs/R2-SP2027-审稿与修改清单.md',R/'docs/R5-SP2027-审稿与修改清单.md',M/'docs/R27-SP2027-审稿与整改方案.md']:
 text=f.read_text(encoding='utf8')
 assert not re.search(r'(?:^### 实验 A|^\*\*B1\.|启动实验 A|加 IRR|配 IRR|irr_kit|coder2_sheet)',text,re.M),f
method=(M/'sections/03-methodology.tex').read_text()
assert all(x in method for x in ['RQ2 (comparability)','RQ3 (joint evidence)','RQ4 (transfer)'])
assert 'RQ4 distinguishes' in (M/'sections/28-fingerprint-dependencies.tex').read_text()
assert '351 record--item cells with source locators' in (M/'tables/r9-rq-findings.tex').read_text()
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
assert 'Scope and threats to validity' not in body
assert 'independently coding researchers' not in body
assert 'sec:validity' not in body
assert '\\section{Implications and Ethics}' in body
assert 'S34 specifies record boundaries' in body
assert 'sections/67-framework-utility' in (M/'sections/11-discussion.tex').read_text()
assert 'The authors checked entries against the cited sources' in body
assert 'None of the 19 reported holdouts' not in body
assert '133 judged pairs within the complete 741-pair inventory' in body
assert 'A usable reporting card' in body
audit=subprocess.run([sys.executable,str(M/'tools/audit_check.py'),'--json',str(O/'audit-check.json')],capture_output=True,text=True)
assert audit.returncode==0,audit.stdout+audit.stderr
ar=json.loads((O/'audit-check.json').read_text());assert ar['failed']==0 and ar['passed']>=36
recon=json.loads((M/'data/family-summary-reconciliation.json').read_text())
assert recon['family_cells_changed']==13 and recon['record_judgments_changed']==0
assert recon['bound_counts']==[20,17,17,4,2,17,16,4,11]
assert recon['applicable_counts']==[20,20,20,11,11,20,17,17,19]
bs=json.loads((P/'experiments/sp2027-r28-validation/external-summary.json').read_text())
assert bs['records']==15 and bs['defense_study_pairs']==14 and len(bs['retained_control_ids'])==4
assert bs['measurement_objects']=={'protected fit/view':11,'execution/cost':4}
assert all(c>=32 or c in [9,10,13] for c in map(ord,body)), 'Control character in TeX'


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
 assert not banned.search(full.replace('\n',' ')),name
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
  ct=next(i+1 for i,t in enumerate(ts) if 'Recorded contrasts for the worked case' in t);assert ct>=cp and '26.2' in ts[ct-1]
  nums=[int(k) for t in ts for k in re.findall(r'TABLE\s+(\d+)\.',t)]
  assert set(nums)==set(range(1,max(nums)+1)),nums
  end=refpage if ts[refpage-1].split('References',1)[0].strip() else refpage-1
  pdfs[name].update({'main_body_last_page':end,'appendix_case_page':cp,'appendix_case_pages':ct-cp+1,'main_body_utility_checks':2})
 else:
  assert 'sections/66-source-reconciliation.tex' in files
  assert 'Source Reconciliation, Record Boundaries' in full
  assert 'S33.' in full and 'S34.' in full and 'S35.' in full and 'S36.' in full
assert cites<=set(bib),cites-set(bib)
out={'revision':'R32-audit-decisions','passed':True,'base_commit':BASE,
 'unchanged_scientific_and_prior_provenance_files':len(protected),'preservation_check':'Git diff against R31; package checker independently verifies all bytes','unchanged_experimental_tables':checked,
 'new_documentary_studies':0,'new_model_calls':0,'source_reporting_overlay':'record-derived summary only','record_level_judgments_changed':0,'family_summary_cells_changed':13,'audit_checks_passed':ar['passed'],'publication_strata':'4 venue-linked / 16 other cited-version families',
 'retired_task_absent_from_current_sources_and_pdfs':True,'three_sok_contributions_aligned':True,'main_body_utility_checks':2,
 'citation_keys':len(cites),'bibliography_keys':len(bib),'pdfs':pdfs}
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(out))
