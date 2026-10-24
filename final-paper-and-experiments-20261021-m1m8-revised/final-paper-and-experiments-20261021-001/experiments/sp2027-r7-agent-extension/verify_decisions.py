"""Verify every retained model decision against events, role histories and actual dispatch."""
from common import *

USAGE_KEYS=('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')
EVENT_USAGE_KEYS=('inputTokens','cachedInputTokens','outputTokens','reasoningOutputTokens')

def verify(root,destination):
 plan=read(HERE/'formal_plan.json');ns,tools,base,tasks=load();rows=[];total_models=0;unknown=0;rejected=0
 for ep in sorted((root/'formal').glob('*/task-*/episode.json')):
  e=read(ep);histories={'agent':e['agent_messages'],'user':e['user_messages']};usage={k:0 for k in USAGE_KEYS};answers={'agent':[],'user':[]};model_calls=0;tool_index=0;rejects=[]
  for role in ['agent','user']:
   results=sorted((ep.parent/role).glob('*/result.json'))
   assert [int(p.parent.name) for p in results]==list(range(len(results))),str(ep)
   for i,rp in enumerate(results):
    res=read(rp);req=read(rp.parent/'request.json');attempt=rp.parent/res['attempt'];answer=read(attempt/'answer.json')
    events=[json.loads(line) for line in (attempt/'events.jsonl').read_text(encoding='utf-8-sig').splitlines() if line]
    final=[x['params']['item']['text'] for x in events if x.get('method')=='item/completed' and x.get('params',{}).get('item',{}).get('type')=='agentMessage']
    assert final and res['answer']==answer==json.loads(final[-1]),str(rp)
    assert req['role']==role and req['inference_fingerprint']==res['inference_fingerprint']==e['inference_fingerprint']
    assert res['requested_model']==res['reported_model']=='gpt-6-luna' and res['reasoning_effort']=='low'
    assert len(req['messages'])==2+2*i
    assert req['messages']==histories[role][:len(req['messages'])],str(rp)
    last_usage=[x['params']['tokenUsage']['total'] for x in events if x.get('method')=='thread/tokenUsage/updated']
    assert last_usage and res['usage']=={a:last_usage[-1].get(b,0) for a,b in zip(USAGE_KEYS,EVENT_USAGE_KEYS)}
    for k in USAGE_KEYS:usage[k]+=res['usage'].get(k,0)
    model_calls+=1
    try:
     args=json.loads(answer['arguments_json'])
     if not isinstance(args,dict):raise ValueError('Arguments must be an object')
     if role=='user' and answer['action']!='respond':raise ValueError('User returned tool action')
     action=answer['action'];content=answer['content']
    except (ValueError,KeyError,TypeError) as exc:
     assert e['status']=='protocol_error' and i==len(results)-1 and len(req['messages'])==len(histories[role]),str(rp)
     rejects.append({'role':role,'index':i,'error':str(exc)});rejected+=1;continue
    n=len(req['messages']);history=histories[role]
    if role=='user':
     assert history[n]=={'role':'assistant','content':content},str(rp)
    elif action=='respond':
     assert history[n]=={'role':'assistant','content':content},str(rp)
    else:
     assert history[n]=={'role':'assistant','tool_action':{'name':action,'arguments':args}},str(rp)
     assert history[n+1]['role']=='tool' and history[n+1]['name']==action
     c=e['calls'][tool_index];tool_index+=1
     expected=json.dumps({'name':action,'arguments':args},sort_keys=True)
     assert c['name']==action and c['kwargs']==args and c['req_text']==expected and c['resp_text']==history[n+1]['content']
     assert c['req']==len(expected.encode()) and c['resp']==len(c['resp_text'].encode())
     assert c['err']==(c['resp_text'].startswith('Error:') or c['resp_text'].startswith('Unknown action'))
     if action not in tools:unknown+=1
    answers[role].append({'index':i,'action':action,'content':content,'history_length':n})
   assert len(results)==len(answers[role])+sum(x['role']==role for x in rejects)
   if results:
    last=len(results)-1;last_n=2+2*last
    was_rejected=any(x['role']==role and x['index']==last for x in rejects)
    if was_rejected:expected_end=last_n
    elif role=='user':expected_end=last_n+1
    elif answers[role][-1]['action']=='respond' and e['status'] in ['user_stop','protocol_error']:expected_end=last_n+1
    else:expected_end=last_n+2
    assert len(histories[role])==expected_end,str(ep)
   elif role=='agent':assert not histories[role]
  assert model_calls==e['model_calls'] and usage==e['usage'] and tool_index==len(e['calls'])
  # Cross-role messages: initial user greeting, then one simulator request per real agent response.
  user_requests=[read(p.parent/'request.json') for p in sorted((ep.parent/'user').glob('*/result.json'))]
  if user_requests:assert user_requests[0]['messages'][-1]=={'role':'user','content':'Hi! How can I help you today?'}
  responds=[a for a in answers['agent'] if a['action']=='respond']
  assert len(user_requests)==1+len(responds) and e['responds']==len(responds)
  if answers['user'] and e['agent_messages']:
   assert e['agent_messages'][1]=={'role':'user','content':answers['user'][0]['content']}
  for j,a in enumerate(responds):
   assert user_requests[j+1]['messages'][-1]=={'role':'user','content':a['content']}
   reply=next((x for x in answers['user'] if x['index']==j+1),None)
   following=a['history_length']+1
   if reply is not None:
    if following<len(e['agent_messages']):assert e['agent_messages'][following]=={'role':'user','content':reply['content']}
    else:assert e['status']=='user_stop' and j==len(responds)-1
   else:assert e['status']=='protocol_error' and j==len(responds)-1
  if e['status']=='protocol_error':assert rejects,'Unexplained protocol_error'
  else:assert not rejects
  total_models+=model_calls;rows.append({'task':e['task'],'prompt':e['prompt'],'model_calls':model_calls,'tool_dispatch_attempts':len(e['calls']),'protocol_rejections':rejects,'aligned':True})
 assert len(rows)==150
 out={'complete':True,'episodes':len(rows),'model_calls':total_models,'unknown_tool_attempts':unknown,'tool_dispatch_attempts':sum(r['tool_dispatch_attempts'] for r in rows),'real_tool_calls':sum(r['tool_dispatch_attempts'] for r in rows)-unknown,'protocol_rejected_decisions':rejected,'checks':['result.answer == attempt.answer.json == last completed agentMessage JSON','role request messages exactly match final history prefixes','action arguments and next assistant/tool record match','tool order/name/kwargs/request/response UTF8 lengths match','user simulation answers and cross-role response links match','per-call usage matches final raw usage event; per-episode usage/model_calls match'],'episodes_detail':rows}
 write(destination,out);return out

if __name__=='__main__':print(json.dumps(verify(HERE,HERE/'decision_alignment.json'),ensure_ascii=False))

