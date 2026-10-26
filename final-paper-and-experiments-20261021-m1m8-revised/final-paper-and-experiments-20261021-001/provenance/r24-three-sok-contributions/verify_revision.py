"""Check literature-only body, a single appendix case, retained data and delivered PDFs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pypdf import PdfReader
import hashlib,json,re,subprocess,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='d6533c9374c1a118b4b1f139e74de16d5e410a83'
sys.path.insert(0,str(P));from verify_package import closure
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
protected=[n for n in old if n.startswith(('experiments/','evidence/')) or (n.startswith('provenance/') and n!='provenance/snapshot.json')]
with ThreadPoolExecutor(max_workers=8) as pool:
    for n,h in zip(protected,pool.map(lambda n:sha(P/n),protected)):assert h==old[n],n
print('PRESERVED_EVIDENCE_PASS',len(protected),flush=True)
for name in ['sections/03-methodology.tex','sections/04-scope.tex','sections/27-intervention-contracts.tex',
             'tables/r19-joint-bindings.tex','tables/r9-audit-rules.tex','tables/family-audit-matrix.tex',
             'sections/37-transfer-tests.tex','sections/42-live-timing-main.tex']:
    assert (M/name).read_bytes()==prior(Path('manuscript')/name),name
tables=['r9-streaming','r9-dispatch','r9-cohorts','r9-frozen-reference','r9-crossfit','r9-localization','r9-flush','r9-controls','r11-model-replication','r14-calibration-transfer']
for name in tables:assert (M/'tables'/(name+'.tex')).read_bytes()==prior(Path('manuscript/tables')/(name+'.tex'))

main=(M/'main.tex').read_text();before=main.split(r'\bibliographystyle')[0]
def expand(text):
    return re.sub(r'\\input\{([^}]+)\}',lambda m:expand((M/(m[1]+'.tex')).read_text()),text)
body=expand(before)
assert not re.search(r'\bExps?\s*[~. ]*[1-4]',body)
assert r'\input{sections/37-transfer-tests}' not in main
assert 'Controlled Studies Supporting' not in body and 'Four controlled studies' not in body
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',main,re.S)[1]
intro=(M/'sections/01-introduction.tex').read_text()
conclusion=(M/'sections/12-conclusion.tex').read_text()
supp_intro=(M/'supplement.tex').read_text().split(r'\section{Search')[0]
for part in [abstract,intro,conclusion,supp_intro]:
    for term in ['record-level comparison','configuration-level joint binding','deployment decisions']:
        assert term in part.lower(),term
assert intro.count(r'\item \textbf{')==3
assert 'which changes invalidate' not in intro
assert 'Transfer boundaries here delimit the scope of an evaluated result' in intro
unchanged_tables=[n for n in old if n.startswith('manuscript/tables/') and n.endswith('.tex') and n!='manuscript/tables/r9-rq-findings.tex']
for n in unchanged_tables:assert sha(P/n)==old[n],n
stability=(M/'sections/60-calibration-stability.tex').read_text()
prior_stability=prior(Path('manuscript/sections/60-calibration-stability.tex')).decode('utf8')
stat_blocks=lambda s:re.findall(r'\\begin\{table\}.*?\\end\{table\}',s,re.S)
assert len(stat_blocks(stability))==4
assert stat_blocks(stability)==stat_blocks(prior_stability)
assert 'their nonsignificance establishes neither equivalent defenses nor the validity of the audit framework' in stability
assert 'A local-recalibration comparator is justified by the design' in stability
assert 'The 100 resamples add no independent customers' in stability
assert not re.search(r'Exp|case study|GLM|MiniMax|Luna|resamples|supporting',abstract)
assert 'supporting study' not in (M/'tables/r9-rq-findings.tex').read_text()
assert 'measure the consequences' not in intro.lower()
assert all(s in abstract for s in ['82 study families','39 result records','741','133','17','CachePrune','six-axis'])
assert main.index(r'\input{sections/62-appendix-case-study}')>main.index(r'\appendices')>main.index(r'\bibliography{')
main_cl=closure(M,'main.tex');supp_cl=closure(M,'supplement.tex')
assert all('tables/'+n+'.tex' not in main_cl for n in tables)
assert all('tables/'+n+'.tex' in supp_cl for n in tables if n!='r9-streaming')
assert 'tables/transfer-streaming.tex' in supp_cl and 'sections/64-case-study-register.tex' in supp_cl
case=(M/'sections/62-appendix-case-study.tex').read_text();grid=(M/'tables/r23-case-study.tex').read_text()
assert case.count(r'\section{')==1 and r'\subsection{' not in case
assert not re.search(r'Exp[~. ]*[1-4]',case+grid)
assert len(case.split())+len(grid.split())<850
expected={
    'emitter':('tables/r9-streaming.tex',['2.19','0.21','100.0','50.0']),
    'state':('tables/r9-dispatch.tex',['100.0/100.0','100\\%','0\\%']),
    'calibration':('tables/r14-calibration-transfer.tex',['20.8','17.3','15.95','18.65','67.9']),
    'observation':('sections/42-live-timing-main.tex',['61.4','11.4','3.7,19.6']),
}
bindings={}
for boundary,(source,values) in expected.items():
    src=(M/source).read_text()
    for value in values:assert value in src and value in grid,(boundary,value)
    bindings[boundary]={'source':source,'sha256':sha(M/source),'matched_values':values}
assert all(x in case for x in ['Holm-adjusted $p=1.000$','37/50','33/50','[-23.9,6.5]','2.04','15.11','26.2'])
print('BODY_SCOPE_AND_CASE_VALUES_PASS',flush=True)

cites=set();bib=[];pdfs={}
for f in M.glob('*.bib'):bib+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text())
assert len(bib)==len(set(bib))
for name,files in [('main',main_cl),('supplement',supp_cl)]:
    text='\n'.join((M/n).read_text() for n in files if n.endswith('.tex'))
    labels=re.findall(r'\\label\{([^}]+)\}',text);assert len(labels)==len(set(labels)),Counter(labels)
    refs=set(re.findall(r'\\(?:ref|pageref|eqref)\{([^}]+)\}',text));assert refs<=set(labels),refs-set(labels)
    for c in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',text):cites.update(x.strip() for x in c.split(','))
    log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
    assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined|LaTeX Error',log)
    d=PdfReader(M/(name+'.pdf'));ts=[p.extract_text() for p in d.pages];full='\n'.join(ts)
    assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
    assert not any(x in (str(d.metadata)+full).lower() for x in ['quueieu28737','c:/users/','c:\\users\\'])
    assert 'κ' not in full and 'independent dual' not in full.lower()
    refpage=next(i+1 for i,t in enumerate(ts) if 'References' in t)
    pdfs[name]={'pages':len(d.pages),'references_start':refpage,'sha256':sha(M/(name+'.pdf'))}
    if name=='main':
        assert refpage<=13
        bodypdf='\n'.join(ts[:refpage]).split('References',1)[0];assert not re.search(r'\bExp[s. ]*[1-4]',bodypdf)
        assert '690' not in bodypdf and 'MiniMax' not in bodypdf and 'GLM' not in bodypdf
        pages=[i+1 for i,t in enumerate(ts) if 'Case Study: Applying' in t];assert len(pages)==1
        cp=pages[0];assert cp>refpage
        assert 'Recorded contrasts for the worked case' in ts[cp-1]
        assert 'The latter' in ts[cp-1] and '26.2' in ts[cp-1]
        nums={int(k):i+1 for i,t in enumerate(ts) for k in re.findall(r'TABLE\s+(\d+)\.',t)}
        assert set(nums)==set(range(1,15)),nums
        assert {int(k) for k in re.findall(r'TABLE\s+(\d+)\.',bodypdf)}==set(range(1,12))
        body_end=refpage if ts[refpage-1].split('References',1)[0].strip() else refpage-1
        pdfs[name].update({'main_body_last_page':body_end,'main_body_tables':11,'appendix_case_page':cp,'appendix_case_pages':1,'main_body_empirical_sections':0})
    else:assert 'S32.' in full and 'Case-Study Cohort' in full
    if name=='supplement':
        assert not any(s in text for s in ['Main 8.1','Main 8.2','Main 8.3','Main 8.4','the main paper organizes these records into four demonstrations'])
assert cites<=set(bib),cites-set(bib)
report={'revision':'R24-three-sok-contributions','passed':True,'base_commit':BASE,
        'unchanged_scientific_and_prior_provenance_files':len(protected),'new_experiments':0,'new_llm_calls':0,'coding_changed':False,
        'main_body_empirical_sections':0,'appendix_case_studies':1,'detailed_grids_retained':len(tables),
        'case_source_words_including_grid':len(case.split())+len(grid.split()),'case_source_bindings':bindings,
        'contribution_alignment':['record-level comparison','configuration-level joint binding','deployment decisions'],
        'unchanged_manuscript_tables_except_rq_summary':len(unchanged_tables),'unchanged_r21_statistical_tables':len(stat_blocks(stability)),
        'null_result_not_used_as_framework_validation':True,
        'citation_keys':len(cites),'bib_keys':len(bib),'pdfs':pdfs}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(report,ensure_ascii=False))
