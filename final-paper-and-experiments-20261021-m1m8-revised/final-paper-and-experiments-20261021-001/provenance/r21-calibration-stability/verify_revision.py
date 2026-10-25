"""Check R21 publication, preserved evidence and complete resampling provenance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
import hashlib,json,re,subprocess,gzip
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
D=P/'experiments/sp2027-r21-calibration-stability';BASE='5d633c5b457ba8ce3759d877937cdf0fc619918b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def prior(rel):return subprocess.check_output(['git','show',BASE+':'+(P/rel).relative_to(R).as_posix()],cwd=R)
old=json.loads(prior(Path('SHA256SUMS.json')))['files']
preserve=[n for n in old if n.startswith(('experiments/','evidence/','provenance/r19-evidence-closure/','provenance/r20-claim-conditioned-audit/'))]
with ThreadPoolExecutor(max_workers=8) as pool:
    for n,h in zip(preserve,pool.map(lambda n:sha(P/n),preserve)):assert h==old[n],n
assert (M/'sections/03-methodology.tex').read_bytes()==prior(Path('manuscript/sections/03-methodology.tex'))
assert '2/20 & 1 & 1' in (M/'tables/r19-joint-bindings.tex').read_text()
protocol=read(D/'protocol.json');assert protocol['run_sha256']==sha(D/'run.py')
for n,h in protocol['sources'].items():assert sha(D.parent/n)==h,n
plan=read(D.parent/'sp2027-r12-glm/formal_plan.json');train=set(plan['train']);test=set(plan['test'])
sources=['sp2027-r11-minimax','sp2027-r12-glm'];customer_tasks={}
rawtest={n:[s for s in read(D.parent/n/'network_sessions.json') if s['condition']=='raw' and s['task'] in test] for n in sources}
for source in sources:
    es=[read(p) for p in (D.parent/source/'formal/baseline').glob('*/episode.json')]
    customer_tasks[source]={u:sorted(e['task'] for e in es if e['user']==u and e['task'] in train) for u in sorted({e['user'] for e in es if e['task'] in train})}
    assert len(customer_tasks[source])==29
    assert set(customer_tasks[source]).isdisjoint({e['user'] for e in es if e['task'] in test})
files=sorted((D/'replicates').glob('*.json'));assert len(files)==100
for i,p in enumerate(files):
    rep=read(p);assert rep['replicate']==i and len(rep['calibration_customers'])==len(rep['attacker_customers'])==29
    for source,cal in rep['calibrations'].items():
        expected=[t for u in rep['calibration_customers'] for t in customer_tasks[source][u]]
        assert cal['actual_sampled_tasks']==expected and set(expected)<=train
        assert all(d['task'] in train for ds in cal['donors'].values() for d in ds)
    assert sha(D/'captures'/f'{i:03d}.json.gz')==rep['capture_sha256']
    with gzip.open(D/'captures'/f'{i:03d}.json.gz','rt',encoding='utf8') as stream:captures=json.load(stream)
    assert {(c['source'],c['target']) for c in captures}=={(a,b) for a in sources for b in sources}
    for c in captures:
        assert {s['task'] for s in c['sessions']}==train|test
        for s in c['sessions']:
            assert s['application_wire_bytes']==sum(length+5 for direction,length in s['records'])
            assert sum(direction=='c2s' for direction,length in s['records'])==len(s['calls'])
        ts=[s for s in c['sessions'] if s['task'] in test];raw=rawtest[c['target']]
        br=sum(s['application_wire_bytes'] for s in ts)/sum(s['application_wire_bytes'] for s in raw)
        cr=sum(len(s['calls']) for s in ts)/sum(len(s['calls']) for s in raw)
        for row in rep['results']:
            if row['source']==c['source'] and row['target']==c['target'] and row['regime']!='attacker_only':
                assert abs(row['bytes_ratio']-br)<1e-12 and abs(row['calls_ratio']-cr)<1e-12
    for row in rep['results']:
        for m in row['metrics'].values():assert set(m['tasks'])==test
result=read(D/'summary.json');assert result['replicates']==100 and result['sessions']==46000
assert read(D/'verification.json')['passed'] and read(D/'baseline_verification.json')['passed']
assert read(D/'statistics_verification.json')['passed']
assert read(D/'prediction_verification.json')['passed'] and read(D/'prediction_verification.json')['attacker_prediction_arrays_checked']==14000
assert read(D/'statistics_verification.json')['analysis_sha256']==sha(D/'analyze.py')
assert len(result['conditional_tests'])==8 and all(x['holm_p']==1.0 for x in result['conditional_tests'])
alltex='\n'.join(x.read_text(encoding='utf8') for x in M.rglob('*.tex'));citekeys=set()
for group in re.findall(r'\\cite(?:\[[^\]]*\])*\{([^}]+)\}',alltex):citekeys.update(x.strip() for x in group.split(','))
bibkeys=[]
for f in M.glob('*.bib'):bibkeys+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text(encoding='utf8'))
assert len(bibkeys)==len(set(bibkeys)) and citekeys<=set(bibkeys)
pdfs={}
for name in ['main','supplement']:
    d=PdfReader(M/(name+'.pdf'));texts=[p.extract_text() for p in d.pages];text='\n'.join(texts)
    assert sha(M/(name+'.pdf'))==sha(R/(name+'.pdf'))==sha(P/'pdf'/(name+'.pdf'))
    log=(P/'pdf/build-logs'/(name+'.log')).read_text(errors='replace')
    assert not re.search(r'Overfull|undefined references|undefined citations|Float too large|multiply defined',log)
    assert all(x not in text.lower() for x in ['quueieu28737','c:/users/','c:\\users\\'])
    assert 'κ' not in text and 'independent dual' not in text.lower()
    refs=min(i+1 for i,t in enumerate(texts) if 'References' in t)
    pdfs[name]={'pages':len(d.pages),'sha256':sha(M/(name+'.pdf')),'references_start':refs}
    if name=='main':
        assert 'return reduction is resolved' not in text and 'resolved return reduction' not in text
        assert refs<=13 and '100' in text and 'Holm' in text
        body={int(k):i+1 for i,t in enumerate(texts) for k in re.findall(r'TABLE\s+(\d+)\.',t) if int(k)<=21}
        assert set(body)==set(range(1,22)) and max(body.values())<=13
        pdfs[name]['main_table_pages']=body
    else:assert 'Calibration Source and Training-Customer Sensitivity' in ' '.join(text.split())
report={'revision':'R21-calibration-stability','passed':True,'base_commit':BASE,'unchanged_scientific_and_prior_provenance_files':len(preserve),'coding_changed':False,'new_llm_calls':0,'new_customers':0,'calibration_replicates':100,'actual_tls_sessions':46000,'original_seven_attack_prediction_arrays_reproduced':84,'eight_test_holm':True,'citation_keys':len(citekeys),'bib_keys':len(bibkeys),'pdfs':pdfs,'experiment_summary_sha256':sha(D/'summary.json')}
(O/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(report))
