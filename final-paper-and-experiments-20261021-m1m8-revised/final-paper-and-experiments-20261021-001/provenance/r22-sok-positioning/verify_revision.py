"""Verify editorial positioning, numerical retention, source closure and PDF delivery."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pypdf import PdfReader
import hashlib,json,re,subprocess,sys

O=Path(__file__).resolve().parent; P=O.parents[1]; M=P/'manuscript'; R=P.parents[1]
BASE='2a455a12e584fcfc9331f8b5311f749e7c406060'
sys.path.insert(0,str(P)); from verify_package import closure
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def prior(rel): return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
preserve=[n for n in old if n.startswith(('experiments/','evidence/')) or (n.startswith('provenance/') and n!='provenance/snapshot.json')]
with ThreadPoolExecutor(max_workers=8) as pool:
    for n,h in zip(preserve,pool.map(lambda n:sha(P/n),preserve)): assert h==old[n],n
assert (M/'sections/03-methodology.tex').read_bytes()==prior(Path('manuscript/sections/03-methodology.tex'))
assert (M/'tables/r19-joint-bindings.tex').read_bytes()==prior(Path('manuscript/tables/r19-joint-bindings.tex'))
assert (M/'tables/r14-calibration-transfer.tex').read_bytes()==prior(Path('manuscript/tables/r14-calibration-transfer.tex'))

moved=['r9-streaming','r9-dispatch','r9-frozen-reference','r9-crossfit','r9-localization','r9-flush','r9-controls']
for n in moved: assert (M/'tables'/f'{n}.tex').read_bytes()==prior(Path('manuscript/tables')/(n+'.tex'))
main_cl=closure(M,'main.tex'); supp_cl=closure(M,'supplement.tex')
assert not any('tables/'+n+'.tex' in main_cl for n in moved)
assert all('tables/'+n+'.tex' in supp_cl for n in moved if n!='r9-streaming')
assert 'tables/transfer-streaming.tex' in supp_cl
assert 'sections/61-synthesis-study-details.tex' in supp_cl

# Condensed numeric rows must be exact subsets of the retained original grids.
def rows(rel):
    return [re.sub(r'\s+','',line.split(r'\\')[0]) for line in (M/rel).read_text().splitlines() if '&' in line and r'\\' in line]
timing=rows('tables/r22-timing-summary.tex')[1:]
original=rows('tables/r9-controls.tex')[1:]
for row in timing:
    cells=row.split('&'); candidates=[r.split('&') for r in original if r.split('&')[:2]==cells[:2]]
    assert len(candidates)==1,cells
    original_cells=candidates[0]
    assert cells==original_cells[:4]+original_cells[5:],cells
frozen=rows('tables/r22-frozen-summary.tex')[1:]
original=rows('tables/r9-frozen-reference.tex')[1:]
for row in frozen:
    cells=row.split('&'); label='Jointprogram' if cells[0]=='Joint' else cells[0]
    candidates=[r.split('&') for r in original if r.split('&')[0]==label]; assert len(candidates)==1
    src=candidates[0]; assert cells[1:3]==src[1:3] and cells[3]==src[4]+'/'+src[5],cells

names=['sections/37-transfer-tests.tex','sections/42-live-timing-main.tex']
old_words=len(' '.join(prior(Path('manuscript')/n).decode() for n in names).split())
new_words=len(' '.join((M/n).read_text() for n in names).split())
assert new_words<.65*old_words,(old_words,new_words)
assert (M/'tables/r9-rq-findings.tex').read_text().count('RQ')==4
assert 'The systematized conclusion rests on the complete literature audit' in (M/'sections/11-discussion.tex').read_text()
assert 'A SoK of defense-evidence transfer' in (M/'sections/01-introduction.tex').read_text()

citations=set(); bib=[]; pdfs={}
for f in M.glob('*.bib'): bib+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text(encoding='utf8'))
assert len(bib)==len(set(bib))
for name,files in [('main',main_cl),('supplement',supp_cl)]:
    text='\n'.join((M/f).read_text(encoding='utf8') for f in files if f.endswith('.tex'))
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    assert len(labels)==len(set(labels)),[k for k,v in Counter(labels).items() if v>1]
    refs=set(re.findall(r'\\(?:ref|pageref|eqref)\{([^}]+)\}',text)); assert refs<=set(labels),refs-set(labels)
    for c in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',text): citations.update(x.strip() for x in c.split(','))
    log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
    assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined|LaTeX Error',log)
    doc=PdfReader(M/(name+'.pdf')); ts=[p.extract_text() for p in doc.pages]; full='\n'.join(ts)
    assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
    assert not any(s in (str(doc.metadata)+full).lower() for s in ['quueieu28737','c:/users/','c:\\users\\'])
    assert 'κ' not in full and 'independent dual' not in full.lower()
    refpage=next(i+1 for i,t in enumerate(ts) if 'References' in t)
    pdfs[name]={'pages':len(doc.pages),'references_start':refpage,'sha256':sha(M/(name+'.pdf'))}
    if name=='main':
        assert refpage<=13
        assert '50.0' in full and '67.9' in full and 'Holm' in full
        assert 'resolved return reduction' not in full and 'return reduction is resolved' not in full
        tables={int(k):i+1 for i,t in enumerate(ts) for k in re.findall(r'TABLE\s+(\d+)\.',t)}
        assert set(range(1,17))<=set(tables) and max(tables[k] for k in range(1,17))<=refpage
        pdfs[name]['body_tables']=16
        pdfs[name]['study_heading_page']=next(i+1 for i,t in enumerate(ts) if 'Controlled Studies Supporting' in t)
        pdfs[name]['implications_heading_page']=next(i+1 for i,t in enumerate(ts) if '9. Implications,' in t)
    else: assert 'Detailed Operating Points' in full and 'S31.' in full
assert citations<=set(bib),citations-set(bib)
result={'revision':'R22-sok-positioning','passed':True,'base_commit':BASE,
        'unchanged_scientific_and_prior_provenance_files':len(preserve),'new_experiments':0,'new_llm_calls':0,'new_customers':0,
        'coding_changed':False,'detailed_grids_relocated_or_indexed':7,
        'section8_source_words_before':old_words,'section8_source_words_after':new_words,
        'section8_source_word_reduction_percent':round(100*(1-new_words/old_words),1),
        'condensed_frozen_rows_verified':len(frozen),'condensed_timing_rows_verified':len(timing),
        'citation_keys':len(citations),'bib_keys':len(bib),'pdfs':pdfs}
(O/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
