"""Bind every released episode to its actual structured model decisions."""
from common import *
import zipfile
from collections import defaultdict

def verify():
    decisions=defaultdict(list)
    for archive in ('model-records-baseline.zip','model-records-rules.zip','additional-completed-records.zip'):
        with zipfile.ZipFile(HERE/archive) as z:
            for name in z.namelist():
                parts=name.split('/')
                if len(parts)==6 and parts[-1]=='result.json':
                    decisions[parts[1],parts[2],parts[3]].append((parts[4],json.loads(z.read(name))))
    es=[read(p) for p in (HERE/'runs').glob('*/*/episode.json')]
    subset=read(HERE/'analysis_split.json');primary=set(subset['train']+subset['test'])
    ns,tools,base,tasks=load();extras=0
    for e in es:
        key=e['prompt'],f"task-{e['task']:03d}-repeat-{e['repeat']}"
        agents=[d for _,d in sorted(decisions[*key,'agent'])]
        users=[d for _,d in sorted(decisions[*key,'user'])]
        assert len(agents)+len(users)==e['model_calls']
        actual=[(d['answer']['action'],json.loads(d['answer']['arguments_json'])) for d in agents if d['answer']['action']!='respond']
        assert actual==[(c['name'],c['kwargs']) for c in e['calls']],key
        assert [d['answer']['content'] for d in agents if d['answer']['action']=='respond']==[m['content'] for m in e['agent_messages'] if m['role']=='assistant' and 'content' in m],key
        assert [d['answer']['content'] for d in users]==[m['content'] for m in e['user_messages'] if m['role']=='assistant'],key
        for k,v in e['usage'].items():assert sum(d['usage'].get(k,0) for d in agents+users)==v
        for c in e['calls']:
            assert c['req_text']==json.dumps({'name':c['name'],'arguments':c['kwargs']},sort_keys=True)
            assert c['req']==len(c['req_text'].encode()) and c['resp']==len(c['resp_text'].encode())
        if e['task'] not in primary:
            env=old.make_env(ns,tools,base,tasks[e['task']]);gold=old.make_env(ns,tools,base,tasks[e['task']])
            for c in e['calls']:
                if c['name'] in tools:env.step(ns['Action'](name=c['name'],kwargs=c['kwargs']))
            for a in tasks[e['task']].actions:gold.step(a)
            assert (env.data==gold.data)==e['db_eq']
            output=all(any(m.get('role')=='assistant' and o.lower() in m.get('content','').lower().replace(',','') for m in e['agent_messages']) for o in tasks[e['task']].outputs)
            assert output==e['r_outputs'] and e['native_reward']==int(e['db_eq'] and output)
            extras+=1
    assert len(es)==663 and extras==3
    result={'status':'DECISION_ALIGNMENT_PASS','episodes':len(es),'model_decisions':sum(e['model_calls'] for e in es),'additional_episode_state_checks':extras,'checks':['model actions to tool-call sequence','assistant and user messages to model outputs','usage totals','serialized request and response lengths','additional episode state and output scoring']}
    write(HERE/'decision_alignment_validation.json',result)
    return result

if __name__=='__main__':print(json.dumps(verify(),indent=1))
