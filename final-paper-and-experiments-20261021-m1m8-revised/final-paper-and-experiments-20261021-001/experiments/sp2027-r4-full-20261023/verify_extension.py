"""Verify the incremental full cohort and bind decisions, scoring, captures and sources.

This does not invoke any model. Run from any working directory, with the base
snapshot and historical experiment dependencies retained beside this directory.
"""
from pathlib import Path, PureWindowsPath
from collections import defaultdict, Counter
import hashlib, json, sys, zipfile

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
BASE=EXP/'sp2027-r4-snapshot-20261023'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def archives():
    return [BASE/n for n in ('model-records-baseline.zip','model-records-rules.zip','additional-completed-records.zip')]+[HERE/'delta-model-records.zip']
def episode_paths():
    a=read(HERE/'inputs.json')
    return {n:(BASE/n if n in a['base_episode_hashes'] else HERE/'delta'/n) for n in a['all_episode_hashes']}

def verify():
    a=read(HERE/'inputs.json')
    for n,d in a['base_files'].items(): assert sha(BASE/n)==d,('base',n)
    for n,d in a['inputs'].items(): assert sha(HERE/n)==d,('extension',n)
    paths=episode_paths()
    assert len(paths)==690 and len(a['base_episode_hashes'])==663 and len(a['added_episode_paths'])==27
    assert set(a['base_episode_hashes'])|set(a['added_episode_paths'])==set(paths)
    assert not set(a['base_episode_hashes'])&set(a['added_episode_paths'])
    for n,p in paths.items(): assert sha(p)==a['all_episode_hashes'][n],n
    for n,d in a['base_episode_hashes'].items(): assert d==a['all_episode_hashes'][n]
    for manifest in ('runtime_manifest.json','pretest_analysis_manifest.json'):
        for n,d in read(BASE/manifest)['files'].items():
            parts=PureWindowsPath(n).parts
            p=BASE/a['source_files'][parts[-1]] if parts[0]=='sp2027-r4' else EXP.joinpath(*parts)
            assert sha(p)==d,(manifest,n)
    split=read(BASE/'split.json');freeze=read(BASE/'pretest_analysis_manifest.json')
    assert sha(BASE/'calibration.json')==freeze['calibration_sha256']
    es=[read(p) for p in paths.values()]
    expected={(arm,t,r) for arm in ('baseline','rules') for t in split['train']+split['test'] for r in range(3)}
    assert {(e['prompt'],e['task'],e['repeat']) for e in es}==expected and len(es)==len(expected)
    fp=es[0]['inference_fingerprint']
    assert fp['model']=='gpt-6.1-sol' and fp['reasoning_effort']=='low'
    assert fp['protocol_sha256']==sha(BASE/'protocol.json') and fp['runtime_manifest_sha256']==sha(BASE/'runtime_manifest.json')
    assert all(sha(BASE/n)==d for n,d in fp['files'].items())
    assert all(e['inference_fingerprint']==fp for e in es)
    decisions=defaultdict(list);requests=set();results=set();records=0
    train_times=[];test_times=[]
    for archive in archives():
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for n in z.namelist():
                parts=n.split('/')
                if len(parts)!=6 or parts[-1] not in ('request.json','result.json'):continue
                d=json.loads(z.read(n));assert d['inference_fingerprint']==fp,n
                if parts[-1]=='request.json':
                    assert n not in requests;requests.add(n)
                    assert set(d)=={'role','messages','tools','inference_fingerprint'}
                else:
                    assert n not in results;results.add(n);records+=1
                    assert d.get('reported_model','gpt-6.1-sol')=='gpt-6.1-sol'
                    assert d.get('requested_model','gpt-6.1-sol')=='gpt-6.1-sol'
                    assert d.get('reasoning_effort','low')=='low'
                    assert d.get('instruction_sources',[])==[]
                    tid=int(parts[2].split('-')[1])
                    (train_times if tid in split['train'] else test_times).append(d['collected_utc'])
                    decisions[parts[1],parts[2],parts[3]].append((parts[4],d))
    assert {n[:-12]+'result.json' for n in requests}==results
    assert max(train_times)<freeze['frozen_utc']<min(test_times)
    for folder in (EXP/'reviewer-audit',EXP/'sp2027-r2',EXP/'sp2027-r2/agent',EXP/'sp2027-r3'):sys.path.insert(0,str(folder))
    import retail_replay as old
    ns,tools,base,tasks=old.load_tau()
    reward=Counter();status=defaultdict(Counter)
    for e in es:
        key=e['prompt'],f"task-{e['task']:03d}-repeat-{e['repeat']}"
        agents=[d for _,d in sorted(decisions[*key,'agent'])]
        users=[d for _,d in sorted(decisions[*key,'user'])]
        assert len(agents)+len(users)==e['model_calls'],key
        actual=[(d['answer']['action'],json.loads(d['answer']['arguments_json'])) for d in agents if d['answer']['action']!='respond']
        assert actual==[(c['name'],c['kwargs']) for c in e['calls']],key
        assert [d['answer']['content'] for d in agents if d['answer']['action']=='respond']==[m['content'] for m in e['agent_messages'] if m['role']=='assistant' and 'content' in m],key
        assert [d['answer']['content'] for d in users]==[m['content'] for m in e['user_messages'] if m['role']=='assistant'],key
        for k,v in e['usage'].items():assert sum(d['usage'].get(k,0) for d in agents+users)==v,(key,k)
        for c in e['calls']:
            assert c['req_text']==json.dumps({'name':c['name'],'arguments':c['kwargs']},sort_keys=True)
            assert c['req']==len(c['req_text'].encode()) and c['resp']==len(c['resp_text'].encode())
        env=old.make_env(ns,tools,base,tasks[e['task']]);gold=old.make_env(ns,tools,base,tasks[e['task']])
        for c in e['calls']:
            if c['name'] in tools:
                try:env.step(ns['Action'](name=c['name'],kwargs=c['kwargs']))
                except Exception:pass
        for action in tasks[e['task']].actions:gold.step(action)
        assert (env.data==gold.data)==e['db_eq'],key
        output=all(any(m.get('role')=='assistant' and o.lower() in m.get('content','').lower().replace(',','') for m in e['agent_messages']) for o in tasks[e['task']].outputs)
        assert output==e['r_outputs'] and e['native_reward']==int(e['db_eq'] and output),key
        if e['task'] in split['test']:reward[e['prompt']]+=e['native_reward'];status[e['prompt']][e['status']]+=1
    sessions=read(HERE/'sessions.json');assert len(sessions)==2760
    lookup={(s['prompt'],s['condition'],s['task'],s['repeat']):s for s in sessions};assert len(lookup)==2760
    with zipfile.ZipFile(HERE/'captures.zip') as z:
        assert z.testzip() is None and len(z.namelist())==2760
        for n in z.namelist():
            c=json.loads(z.read(n));assert c==lookup[c['prompt'],c['condition'],c['task'],c['repeat']]
            path=f"runs/{c['prompt']}/task-{c['task']:03d}-repeat-{c['repeat']}/episode.json"
            assert c['episode_sha256']==a['all_episode_hashes'][path]
            assert c['calibration_sha256']==freeze['calibration_sha256']
    v=read(HERE/'validation.json');assert v['status']=='VERIFIED' and v['episodes']==690 and v['model_calls']==records==11586
    assert read(HERE/'pipeline_status.json')['stage']=='analysis_verified_manuscript_pending'
    out={'status':'FULL_COHORT_EXTENSION_VERIFIED','episodes':690,'base_episodes_unchanged':663,'new_episodes':27,'model_decisions':records,'tls_sessions':2760,'test_reward_counts':dict(reward),'test_status_counts':dict(status),'frozen_before_test':True,'checks':['base bytes and new input hashes','exact 690-cell grid','original runtime and pretest analysis hashes','model requests and outputs','all actions and assistant/user messages aligned','all native states and required outputs rescored','usage and serialized lengths','capture/session/episode linkage'],'scope':'Executable verification by the authors; not external independent replication.'}
    return out

if __name__=='__main__':
    result=verify()
    if '--save' in sys.argv:(HERE/'extension_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
