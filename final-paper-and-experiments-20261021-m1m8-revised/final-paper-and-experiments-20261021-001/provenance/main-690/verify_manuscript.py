"""Verify the 690-cohort manuscript against frozen results and prior bytes.

Requires pypdf. Reads only unless --save is supplied. No model calls or fitting.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, re, sys
from pypdf import PdfReader
from build_tables import sources, pct
HERE=Path(__file__).resolve().parent
P=HERE.parents[1];M=P/'manuscript';F=P/'experiments/sp2027-r4-full-20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    generated=sources()
    for n,s in generated.items():assert (M/n).read_bytes()==s.encode('utf-8'),n
    prior=read(HERE/'prior-package-manifest.json')['files']
    kept=[n for n in prior if n.startswith(('evidence/','experiments/')) or n.endswith('.bib') or n=='pdf/full-cohort-supplement.pdf']
    with ThreadPoolExecutor(max_workers=12) as pool:
        for n,h in zip(kept,pool.map(lambda n:sha(P/n),kept)):assert h==prior[n],('historical data changed',n)
    r=read(F/'results.json');v=read(F/'validation.json')
    assert v['status']=='VERIFIED' and v['episodes']==690
    assert read(F/'extension_validation.json')['status']=='FULL_COHORT_EXTENSION_VERIFIED'
    assert read(F/'reproduction_validation.json')['status']=='FROZEN_FULL_VERIFIER_REPRODUCED'
    rows={(x['view'],x['prompt'],x['condition'],x['target']):x for x in r['results']}
    u={(x['prompt'],x['condition']):x for x in r['utility']}
    for x in rows.values():assert x['test_tasks']==46 and x['test_episodes']==138 and x['test_customer_clusters']==24
    c=rows['network','baseline','raw','cancel'];t=rows['network','baseline','raw','return']
    jc=rows['network','baseline','shape_const','cancel'];jt=rows['network','baseline','shape_const','return']
    assert pct(c['suite_ba']-jc['suite_ba'])=='47.2' and pct(t['suite_ba']-jt['suite_ba'])=='44.0'
    assert f"{u['baseline','shape_const']['wire_ratio']:.1f}"=='15.4'
    e9=(M/'sections/37-transfer-tests.tex').read_text().split(r'\subsection{E9:')[1]
    for token in (r'97.2\%',r'94.0\%',r'97.1\%',r'86.2\%',r'93.5\%',r'66.1\%',r'55.5\%',r'60.8\%',r'51.9\%',r'60.6\%',r'65.5\%','690','414','276','2,760','110/138','105/138'):
        assert token in e9,token
    for bad in ('663 completed','41 test tasks','246 runs','64.1','82.1','78.0','15.3$'):
        assert bad not in e9,bad
    texts={n:(M/n).read_text() for n in ('main.tex','sections/01-introduction.tex','sections/12-conclusion.tex')}
    for n,s in texts.items():
        assert '690' in s and ('47.2' in s or r'97.2\%/94.0\%' in s),n
        assert 'current complete-task snapshot' not in s and 'An interim evaluation' not in s
    pages={};pdf_hashes={}
    for name in ('main','supplement'):
        pdf=P/'pdf'/(name+'.pdf');data=pdf.read_bytes()
        assert data==(M/(name+'.pdf')).read_bytes()
        doc=PdfReader(pdf);pages[name]=len(doc.pages);pdf_hashes[name]=sha(pdf)
        extracted=[p.extract_text() for p in doc.pages]
        if name=='main':
            pages['main_body']=next(i for i,t in enumerate(extracted) if 'Appendix A.' in t)
            assert pages['main_body']<=13
            assert '690' in extracted[0] and '97.2%' in extracted[0] and '94.0%' in extracted[0]
        else:
            start=next(i for i,t in enumerate(extracted) if 'S14. Complete Real-Agent' in t)
            assert 'All 690 episodes' in extracted[start]
            pages['supplement_s14_first_page']=start+1
        for folder in ('provenance/build-logs','pdf/build-logs'):
            log=(P/folder/(name+'.log')).read_text(errors='replace')
            for bad in ('undefined references','undefined on input line','multiply defined','Overfull','Float too large'):
                assert bad not in log,(name,bad)
    receipt={'status':'FULL_COHORT_MANUSCRIPT_CONSISTENCY_PASS','source_results_sha256':sha(F/'results.json'),'original_validation_sha256':sha(F/'validation.json'),'prior_verified_reproduction_sha256':sha(F/'reproduction_validation.json'),'generated_tables':list(generated),'historical_data_and_bibliography_files_unchanged':len(kept),'cohort':{'training':414,'test':276,'total':690,'test_tasks':46,'test_customers':24},'pdf_pages':pages,'pdf_sha256':pdf_hashes,'new_model_calls':0,'scope':'Manuscript and byte consistency with the previously verified full cohort. Scientific conclusions were reviewed against the saved point estimates and intervals; no claim of external independent replication.'}
    if '--save' in sys.argv:(HERE/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
