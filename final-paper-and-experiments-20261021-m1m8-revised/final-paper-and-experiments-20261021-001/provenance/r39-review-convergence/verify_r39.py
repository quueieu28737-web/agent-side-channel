"""Check the R35 privacy cohort, frozen source identities and PDF delivery."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys

from pypdf import PdfReader

O=Path(__file__).resolve().parent
P=O.parents[1]
M=P/'manuscript'
R=P.parents[1]
sys.path.insert(0,str(P))
from verify_package import closure
sys.path.insert(0,str(M/'tools'))
import audit_check as audit

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf8'))

run=subprocess.run([sys.executable,str(M/'tools/audit_check.py'),'--json',str(O/'audit-check.json')],cwd=M,capture_output=True,text=True)
assert run.returncode==0,run.stdout+run.stderr
legacy=load(O/'audit-check.json')
assert legacy['failed']==0 and legacy['passed']>=36
d=load(M/'data/r35-privacy-census.json')
for name,h in d['source_sha256'].items(): assert sha(M/name)==h,name
cells=audit.parse_record_cells()
records={k:v for k,v in cells.items() if not v['contextual'] and v['family']!='zhu2026turing'}
assert len(cells)==39 and len(records)==31
assert len({v['family'] for v in records.values()})==19
assert len(d['core_ids'])==52 and len(d['no_linked_qualifying_record_ids'])==33
base=d['variants']['all']
assert set(base['record_ids'])==set(records)
for name,items in audit.QUERIES.items():
    eligible={k for k,v in records.items() if all(v['cells'][i-1]!='--' for i in items)}
    bound={k for k in eligible if all(records[k]['cells'][i-1]=='B' for i in items)}
    partial={k for k in eligible if all(records[k]['cells'][i-1] in ('B','P') for i in items)}
    q=base['joint_queries'][name]
    assert (set(q['eligible_ids']),set(q['bound_ids']),set(q['partial_accepted_ids']))==(eligible,bound,partial),name
assert [(v['bound'],v['eligible']) for v in base['joint_queries'].values()]==[(3,20),(5,21),(2,15),(2,19),(0,13)]
assert {k:len(v) for k,v in base['modes'].items()}=={'Ex':13,'Tr':5,'Si':5,'Co':6,'Un':2}
for j,strict,partial,denom in [(7,15,16,16),(8,3,5,16),(9,11,15,18),(4,4,8,10),(5,2,2,10)]:
    field=base['fields'][f'R{j}']
    assert (field['strict']['bound'],field['partial_accepted']['bound'],field['strict']['eligible'])==(strict,partial,denom)

matrix=(M/'tables/r35-defense-coverage.tex').read_text(encoding='utf8')
keys={key.strip() for group in re.findall(r'\\cite\{([^}]*)\}',matrix) for key in group.split(',')}
assert keys==set(base['family_ids'])
gaps=(M/'sections/r35-privacy-gaps.tex').read_text(encoding='utf8')
keys={key.strip() for group in re.findall(r'\\cite\{([^}]*)\}',gaps) for key in group.split(',')}
assert keys==set(d['no_linked_qualifying_record_ids'])
positive=(M/'tables/r35-positive-joins.tex').read_text(encoding='utf8')
assert all(s in positive for s in ('3/20','5/21','2/15','2/19','0/13'))
for q in base['joint_queries'].values():
    for record in q['bound_ids']:
        if record.startswith('CACHEPRUNE-'): assert 'CACHEPRUNE' in positive
        else: assert record in positive,record

prior=json.loads(subprocess.check_output(['git','show','e8e14d0728fab33e868cc7feb7a2e2ee92057ac0:'+P.relative_to(R).as_posix()+'/SHA256SUMS.json'],cwd=R))['files']
protected={k for k in prior if k.startswith(('experiments/','evidence/')) or (k.startswith('provenance/') and k!='provenance/snapshot.json')}
changed=subprocess.check_output(['git','diff','--name-only','-z','e8e14d0728fab33e868cc7feb7a2e2ee92057ac0','--',P.relative_to(R).as_posix()],cwd=R).decode().split('\0')
prefix=P.relative_to(R).as_posix()+'/'
assert not any(n.startswith(prefix) and n[len(prefix):] in protected for n in changed)

bib=[]
for f in M.glob('*.bib'):bib+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text(encoding='utf8'))
assert len(bib)==len(set(bib))
pdfs={}
for name in ('main','supplement'):
    sources=closure(M,name+'.tex')
    tex='\n'.join((M/n).read_text(encoding='utf8') for n in sources if n.endswith('.tex'))
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    assert len(labels)==len(set(labels)),[k for k,v in Counter(labels).items() if v>1]
    refs=set(re.findall(r'\\(?:ref|pageref|eqref)\{([^}]+)\}',tex))
    assert refs<=set(labels),refs-set(labels)
    citations={v.strip() for group in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',tex) for v in group.split(',')}
    assert citations<=set(bib),citations-set(bib)
    log=(P/'pdf/build-logs'/(name+'.log')).read_text(encoding='utf8',errors='replace')
    assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined|LaTeX Error',log),name
    file=M/(name+'.pdf')
    assert sha(file)==sha(P/'pdf'/(name+'.pdf'))==sha(R/(name+'.pdf'))
    reader=PdfReader(file)
    pages=[p.extract_text() or '' for p in reader.pages]
    refpage=next(i+1 for i,t in enumerate(pages) if 'References' in t)
    pdfs[name]={'pages':len(pages),'references_start':refpage,'sha256':sha(file)}
    if name=='main':
        assert refpage<=13
        # Pages 14–16 contain only references; page 17 resumes the appendix.
        assert len(pages)<=21 and all(not re.search(r'Appendix\s+[A-Z]',pages[i]) for i in (13,14,15))
        assert 'Appendix' in pages[16] and 'Mapped Privacy Families' in ''.join(pages)
        pdfs[name]['counted_pages_excluding_reference_only_pages']=len(pages)-3
        assert pdfs[name]['counted_pages_excluding_reference_only_pages']<=18
    else:
        text='\n'.join(pages)
        assert all(s in text for s in ('S39. Forward-Citation','S40. Three Object','S41. Privacy and Attribution'))

r36=load(M/'data/r36-sensitivity.json')
for name,h in r36['source_sha256'].items(): assert sha(M/name)==h,name
variants=r36['variants']
assert (variants['historical_fit_scope']['Matched adaptation + inference']['bound'],variants['historical_fit_scope']['Matched adaptation + inference']['eligible'])==(2,15)
assert (variants['broad_nonfit_unknown']['Matched adaptation + inference']['bound'],variants['broad_nonfit_unknown']['Matched adaptation + inference']['eligible'])==(2,22)
assert (variants['broad_nonfit_unknown']['All five bindings']['bound'],variants['broad_nonfit_unknown']['All five bindings']['eligible'])==(0,19)
assert variants['placement_required']['Inference + cost']['bound']==4
assert r36['triple_loo_bound_distribution']=={'0':1,'2':18}

r37=load(M/'data/r37-reconstruction.json')
for name,h in r37['input_sha256'].items(): assert sha(M/name)==h,name
assert len(r37['record_order'])==39 and sum(len(r['cells']) for r in r37['record_order'])==351
assert len(r37['pairs'])==133 and Counter(v['label'] for v in r37['pairs'])=={'M':17,'D':105,'U':11}
assert len(r37['same_family_different'])==8
assert [r['record_id'] for r in r37['record_order']]==[r['id'] for r in audit.parse_record_index()]
assert all(cells[r['record_id']]['cells']==r['cells'] for r in r37['record_order'])
assert 'R4/R5/R7 for matched fitting/inference' in (M/'sections/70-audit-reconstruction.tex').read_text(encoding='utf8')
supptext='\n'.join((p.extract_text() or '') for p in PdfReader(M/'supplement.pdf').pages)
assert 'S28. Family-Level Holdout Evidence' in supptext
assert 'S29. Complete Record-Local Audit and Joint Bindings' in supptext
maintext='\n'.join((p.extract_text() or '') for p in PdfReader(M/'main.pdf').pages)
assert 'COMPLETE RECORD-CELL AND PAIR INDEX' in maintext
assert 'Match' in maintext and 'Different object' in maintext
granularity=(M/'tables/r34-comparison-index.tex').read_text(encoding='utf8')
assert 'M/D/U: unanimous scoped match/different object/unresolved' in granularity
assert 'Unit & Units & M & D & U & Mix & Hidden' in granularity

result={'status':'R39_REVIEW_CONVERGENCE_PDFS_PASS','legacy_audit_checks':legacy['passed'],
        'core_privacy_attribution':52,'mitigation_families':19,'mitigation_records':31,
        'unlinked_core_families':33,'joint_queries':5,'protected_prior_files':len(protected),
        'new_model_calls':0,'pdfs':pdfs,
        'scope':'Accounting and source closure; not a citation-misuse rate.'}
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(result))
