"""Additive offline diagnostics. Never invokes agents, APIs, old fits or acquisition.

prepare -> freeze -> fit exactly 12 new candidates -> inspect saved outputs.
Exclusive artifacts prevent accidental reruns. Old source roots are read-only.
"""
import argparse, ast, collections, hashlib, json, math, pathlib, platform, re, sys, time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).absolute().parents[3]
HERE = pathlib.Path(__file__).absolute().parent
FROZEN = ROOT/'artifacts/sok-supplement-20261008-r2/public-trace/frozen/snapshot'
DATA = ROOT/'experiments/uitraces_reanalysis/runtime/frames-origin-order-20261008-001/attempt-001/data/episodes.jsonl'
OLDP = ROOT/'experiments/uitraces_reanalysis/runtime/frames-origin-order-20261008-001/attempt-001/analysis/private_predictions.jsonl'
SPLIT = ROOT/'evidence/field-audit-2026-09-20/uitraces-4f3df18/src__split_records__frames_sampled_split_record.json'
EXPECTED = '8ee7ba07d8d42dd83099cf57849c574aaac18c9db0cd08188b880f376b426642'

def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def now(): return datetime.now(timezone.utc).isoformat()
def save(p,obj):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
def jsonl(p,rows):
    with pathlib.Path(p).open('x',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
def load():
    sys.path.insert(0,str(FROZEN))
    import analyze as a
    from features import project, features
    raw=[json.loads(x) for x in DATA.read_text(encoding='utf-8').splitlines()]
    admitted,labels,coverage=a._admit_rows(raw,a.default_config())
    return a,project,features,raw,admitted,labels,coverage

CONFIG={
    'schema':'additive-h2-failure-diagnostics-v1','seed':20261008,
    'split':'sha256(20261008:question_sha256) modulo100; <50 train, <75 validation, else test',
    'features':{
        'failure_only':['error_present','result_absent'],
        'empty_only':['projected_single_origin_empty'],
        'activity_only':['log1p_event_count','log1p_missing_local_time_count','log1p_valid_local_time_count',
            'log1p_local_time_sum','log1p_local_time_mean','log1p_local_time_std',
            'log1p_local_time_median','log1p_local_time_p90']},
    'models':'same 4 original candidates per representation; logistic C=.1,1,10; RF200 depth12 leaf2 sqrt; seed20261008 n_jobs1',
    'fit_count':12,'selection':'question-weighted validation logloss only; original declared-order tie rule',
    'weights':'N/(Q*n_q), computed on training only; same original train/validation/test',
    'all_test_predictions_after_all_fits':True,
    'saved_reference_programs':['training_prior','single_coarse','single_combined'],
    'strata':'diagnostic error-present OR result-absent; not authenticated task success',
    'uncertainty':'descriptive point scores only; no new confirmatory interval or selection across diagnostics',
    'task_support':'authoritative FRAMES dataset label and exact-question support; grammatical first-token proxy, NOT semantic family',
    'no_collection_no_llm_no_api_no_luna':True,
    'not_blind':'original and 20261018 results were known before this additive protocol',
}

def prepare():
    a,project,features,raw,rows,labels,coverage=load()
    assert sha(DATA)==EXPECTED and len(rows)==4200
    sources=[DATA,OLDP,SPLIT,FROZEN/'analyze.py',FROZEN/'features.py',pathlib.Path(__file__)]
    for p in ['src__page_tracer.js','src__agent_runner.ts','src__export_split_records.py','README.md']:
        sources.append(ROOT/'evidence/field-audit-2026-09-20/uitraces-4f3df18'/p)
    # Freeze before any fitting. Preparation deliberately does not inspect new test predictions.
    save(HERE/'protocol.json',CONFIG)
    sources.append(HERE/'protocol.json')
    save(HERE/'freeze.json',{'created_utc':now(),'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sources},
        'existing_results_known':True,'source_rows':len(rows),'planned_new_fits':12})
    print('FROZEN: 12 additive offline diagnostic fits; no old fit rerun')

def run():
    import numpy as np, scipy, sklearn
    freeze=json.loads((HERE/'freeze.json').read_text())
    assert all(sha(ROOT/p)==h for p,h in freeze['files'].items()), 'frozen input changed'
    out=HERE/'attempt-001'; out.mkdir(exist_ok=False)
    save(out/'launch.json',{'started_utc':now(),'model_api_calls':0,'planned_fits':12,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
        'freeze_sha256':sha(HERE/'freeze.json')})
    a,project,features,raw,rows,labels,coverage=load(); cfg=a.default_config()
    assert cfg['seed']==CONFIG['seed']
    ev=[project(r.episode,'single_origin_js',cfg['origin']) for r in rows]
    # Coarse indices8: are local-page-age summaries, NOT cross-document duration.
    coarse=np.asarray([features(x,'coarse') for x in ev])
    matrices={
        'failure_only':np.asarray([[float(r.error_present),float(not r.result_present)] for r in rows]),
        'empty_only':np.asarray([[float(not x)] for x in ev]),
        'activity_only':np.column_stack([np.log1p([len(x) for x in ev]),coarse[:,8:]])}
    assert matrices['activity_only'].shape==(4200,8)
    assert all(np.isfinite(x).all() for x in matrices.values())
    idx={p:np.asarray([i for i,r in enumerate(rows) if r.partition==p],dtype=np.int64) for p in ('train','validation','test')}
    y=np.asarray([labels.index(r.label) for r in rows]); train,val,test=[idx[p] for p in ('train','validation','test')]
    weights=a.question_weights([rows[i].question_hash for i in train]); qsval=[rows[i].question_hash for i in val]
    ledger=a._FitLedger(out/'fit_ledger.json',12); selected={}; decisions={}
    for key in CONFIG['features']:
        selected[key],decisions[key]=a._select(key,matrices,train,val,y,weights,qsval,labels,cfg,ledger)
    ledger.require_complete(); save(out/'validation-selection.json',decisions)
    # No fit occurs below this line.
    qstest=[rows[i].question_hash for i in test]
    predictions={key:a._probabilities(model,matrices,test,len(labels),cfg['epsilon']) for key,model in selected.items()}
    old={r['id']:r for r in [json.loads(x) for x in OLDP.read_text().splitlines()]}
    assert set(old)=={rows[i].identifier for i in test}
    for key in CONFIG['saved_reference_programs']:
        predictions[key]=np.asarray([old[rows[i].identifier]['probabilities'][key] for i in test])
    assert all(old[rows[i].identifier]['class_order']==labels for i in test)
    flags=np.asarray([r.failed for r in rows],dtype=bool)[test]
    groups={'all':np.ones(len(test),dtype=bool),'flagged':flags,'unflagged':~flags}
    results={}; losses={key:a.row_log_losses(p,y[test],cfg['epsilon']) for key,p in predictions.items()}
    for group,mask in groups.items():
        qs=[q for q,m in zip(qstest,mask) if m]
        results[group]={'rows':int(mask.sum()),'questions':len(set(qs)),
            'identities':dict(collections.Counter(rows[i].label for i,m in zip(test,mask) if m)),
            'programs':{key:{'loss':a.question_mean(losses[key][mask],qs),
                'accuracy':a.question_mean((p.argmax(1)[mask]==y[test][mask]).astype(float),qs)} for key,p in predictions.items()},
            'coarse_minus_combined':a.question_mean((losses['single_coarse']-losses['single_combined'])[mask],qs),
            'conditioning':'equal question weight WITHIN subgroup; changed support, not causal failure effect'}
    saved=[]
    for j,i in enumerate(test):
        saved.append({'id':rows[i].identifier,'label':rows[i].label,'question_hash':rows[i].question_hash,
            'classes':labels,'flagged':bool(flags[j]),'empty_projection':not ev[i],
            'probabilities':{key:p[j].tolist() for key,p in predictions.items()}})
    jsonl(out/'predictions.jsonl',saved)
    save(out/'summary.json',{'results':results,'selected':{k:m.descriptor() for k,m in selected.items()},
        'feature_names':CONFIG['features'],'class_order':labels,'fits':12,'source_rows':len(rows),
        'partitions':coverage['partitions'],'failures_retained':sum(r.failed is True for r in rows),
        'source_flags_not_success':True,'new_intervals':False})
    support(rows,ev,labels)
    projection_example(rows,ev,project)
    assert all(sha(ROOT/p)==h for p,h in freeze['files'].items()), 'frozen input changed after fits'
    save(out/'final.json',{'status':'COMPLETE','finished_utc':now(),'fits':12,'model_api_calls':0,
        'old_programs_refit':False,'all_frozen_inputs_unchanged':True,
        'convergence_warnings':sum(len(x['convergence_warnings']) for x in ledger.entries)})
    print(json.dumps(results,indent=2))

def support(rows,ev,labels):
    # Split file has questions, NOT semantic family annotations. Do not invent them.
    split=json.loads(SPLIT.read_text(encoding='utf-8')); lookup={}
    for r in split['records']:
        lookup[r['agent_id']+'/'+r['episode_id']]=r['question']
    proxy={}; qtext={}
    for r in rows:
        question=lookup[r.identifier]; assert hashlib.sha256(question.encode()).hexdigest()==r.question_hash
        first=re.search(r'[A-Za-z]+',question)
        token=first.group().lower() if first else ''
        proxy[r.identifier]=token if token in ('what','which','who','when','where','how') else 'other'
        qtext[r.question_hash]=question
    family=[]; exact=[]
    for label in labels:
        for p in ('train','validation','test'):
            selected=[r for r in rows if r.label==label and r.partition==p]
            family.append({'identity':label,'partition':p,'authoritative_dataset':'FRAMES',
                'rows':len(selected),'questions':len({r.question_hash for r in selected}),
                'semantic_task_family':'NR: not in admitted split metadata',
                'flagged_rows':sum(r.failed is True for r in selected)})
            for r in selected:
                exact.append({'id':r.identifier,'identity':label,'partition':p,'question_sha256':r.question_hash,
                    'question_form_proxy':proxy[r.identifier],'dataset':'FRAMES','flagged':r.failed})
    save(HERE/'identity-dataset-support.json',family); jsonl(HERE/'identity-exact-question-support.jsonl',exact)
    cells=[]
    for label in labels:
        for p in ('train','validation','test'):
            for t in ('what','which','who','when','where','how','other'):
                sr=[r for r in rows if r.label==label and r.partition==p and proxy[r.identifier]==t]
                cells.append({'identity':label,'partition':p,'question_form_proxy':t,'rows':len(sr),
                    'questions':len({r.question_hash for r in sr}),'flagged_rows':sum(r.failed is True for r in sr)})
    save(HERE/'identity-question-form-proxy.json',cells)
    qs={p:{l:{r.question_hash for r in rows if r.label==l and r.partition==p} for l in labels} for p in ('train','validation','test')}
    save(HERE/'support-summary.json',{'authoritative_semantic_families':'NR; split schema has no family field',
        'authoritative_dataset_counts':dict(collections.Counter(x['dataset'] for x in split['records'])) if 'dataset' in split['records'][0] else {'FRAMES':len(rows)},
        'exact_question_common_to_all_14':{p:len(set.intersection(*v.values())) for p,v in qs.items()},
        'question_count':len(qtext),'proxy_rule':'first ASCII word; what/which/who/when/where/how/other; grammatical NOT semantic',
        'proxy_not_used_in_any_classifier':True,'test_matrix':[x for x in cells if x['partition']=='test'],
        'no_task_family_balanced_causal_estimate':True})

def projection_example(rows,ev,project):
    # Deterministic first (by id) row with multiple epochs; a complete compact record.
    prior=ROOT/'evidence/diagnostic-h2-controls-20261018-001/h2_controls.py'
    tree=ast.parse(prior.read_text(encoding='utf-8'))
    fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='first_document')
    namespace={}; exec(compile(ast.Module(body=[fn],type_ignores=[]),str(prior),'exec'),namespace)
    first_document=namespace['first_document']
    candidates=[]
    for i,r in enumerate(rows):
        raw=r.episode['dom_trace']['events']; first=first_document(r.episode,project,'https://en.wikipedia.org')
        if first and len(ev[i])>len(first): candidates.append((len(raw),r.identifier,i,first))
    _,_,i,first=min(candidates); r=rows[i]
    raw=r.episode['dom_trace']['events']; retained=[]
    for j,e in enumerate(raw):
        p=project({'dom_trace':{'events':[e]}},'single_origin_js','https://en.wikipedia.org')
        retained.append({'source_index':j,'source_type':e.get('type'),'trigger':e.get('trigger'),
            'url_sha256':hashlib.sha256(e.get('url','').encode()).hexdigest(),
            'page_local_t':e.get('t'),'included':bool(p),'projected':p[0] if p else None})
    save(HERE/'projection-example.json',{'id':r.identifier,'question_sha256':r.question_hash,
        'complete_ingested_record_projection':retained,'archive_view':ev[i],
        'first_document_proxy':first,'boundary_rule':'first_document() unchanged diagnostic-h2-controls h2_controls.py',
        'sorting':'none; retain source callback-array order; timestamps can reset',
        'truncation':'archive view none; document proxy stops per original first_document rules',
        'not_raw_archive_full_record':True,'raw_archive_bytes_remain_in_pinned_tar':True,
        'excluded_predictors':['URL/page_key','question','answer','error text/flag','result presence','t_episode','DOM text','frame/document IDs unavailable']})

def verify():
    import numpy as np
    a,project,features,raw,rows,labels,coverage=load()
    out=HERE/'attempt-001'; summary=json.loads((out/'summary.json').read_text())
    pred=[json.loads(x) for x in (out/'predictions.jsonl').read_text().splitlines()]
    assert len(pred)==1135 and sum(x['flagged'] for x in pred)==509
    assert len({x['id'] for x in pred})==1135
    y=np.asarray([labels.index(x['label']) for x in pred]); qs=[x['question_hash'] for x in pred]
    for key in pred[0]['probabilities']:
        p=np.asarray([x['probabilities'][key] for x in pred]); assert np.allclose(p.sum(1),1)
        loss=a.question_mean(a.row_log_losses(p,y),qs)
        assert abs(loss-summary['results']['all']['programs'][key]['loss'])<1e-12
    assert abs(summary['results']['all']['coarse_minus_combined']-.344669172198)<1e-9
    fit=json.loads((out/'fit_ledger.json').read_text()); assert len(fit['fits'])==12
    assert all(x['status']=='complete' for x in fit['fits'])
    support=json.loads((HERE/'identity-question-form-proxy.json').read_text())
    assert sum(x['rows'] for x in support)==4200
    exact=[json.loads(x) for x in (HERE/'identity-exact-question-support.jsonl').read_text().splitlines()]
    assert len(exact)==4200
    ex=json.loads((HERE/'projection-example.json').read_text())
    assert sum(x['included'] for x in ex['complete_ingested_record_projection'])==len(ex['archive_view'])
    save(HERE/'selfchecks.json',{'status':'PASS','checked_utc':now(),'saved_probability_points_reconstructed':True,
        'test_rows':1135,'test_flagged':509,'new_fits':12,'old_coarse_combined_not_refit':True,
        'support_rows_reconcile':4200,'projection_complete':True,'scope':'numerical/code checks, not independent research validation'})
    print('PASS')

def selftest():
    import numpy as np
    sys.path.insert(0,str(FROZEN))
    import analyze as a
    from features import project,features,delay
    e={'dom_trace':{'events':[{'type':'click','url':'https://en.wikipedia.org/wiki/A','t':5},
        {'type':'navigate','url':'https://en.wikipedia.org/wiki/B','trigger':'http'},
        {'type':'scroll','url':'https://en.wikipedia.org/wiki/B','t':1}]}}
    p=project(e,'single_origin_js'); assert len(p)==2 and [x['t'] for x in p]==[5,1]
    c=features(p,'coarse'); assert len(c)==15
    act=np.column_stack([np.log1p([len(p)]),np.asarray([c])[...,8:]])
    assert act.shape==(1,8) and np.isfinite(act).all()
    assert not project({'dom_trace':{'events':[]}},'single_origin_js')
    assert len(a._architectures(a.default_config()))==4
    assert np.allclose(a.question_weights(['a','a','b']),[.75,.75,1.5])
    noisy=delay(p,5000,'fixture'); assert [x['type'] for x in noisy]==[x['type'] for x in p]
    assert all(0<=n['t']-v['t']<=5000 for n,v in zip(noisy,p))
    assert not any(x in CONFIG['features']['activity_only'] for x in ('error_present','result_absent'))
    save(HERE/'engineering-tests.json',{'status':'PASS','fits':0,'model_api_calls':0,
        'tests':['projection keeps callback order despite page clock reset','harness navigate excluded',
            'activity has 8 finite features','question weights original','4 candidates per new representation',
            'independent timestamp noise preserves event types','diagnostics no failure flag in activity features']})
    print('7 no-fit engineering checks PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','verify','selftest']);args=p.parse_args()
    {'prepare':prepare,'run':run,'verify':verify,'selftest':selftest}[args.command]()
