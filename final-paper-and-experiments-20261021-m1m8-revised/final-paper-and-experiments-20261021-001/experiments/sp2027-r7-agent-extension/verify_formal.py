"""Completeness, retained model provenance, and independent sandbox reward recomputation."""
from common import *
import copy
from types import SimpleNamespace

def main():
 p=read(HERE/'formal_plan.json');expected={(t,a) for t in p['train']+p['test'] for a in p['prompts']};paths=list((HERE/'formal').glob('*/task-*/episode.json'));rows=[read(x) for x in paths]
 assert len(rows)==150 and {(r['task'],r['prompt']) for r in rows}==expected
 assert len(set(r['user'] for r in rows if r['task'] in p['train']) & set(r['user'] for r in rows if r['task'] in p['test']))==0
 for name,h in p['files'].items():assert sha(HERE/name)==h, name
 n=0;rewards=0;calls=0;tokens=0
 for ep,r in zip(paths,rows):
  ns,tools,base,tasks=load();task=tasks[r['task']]
  env=old.make_env(ns,tools,base,task);env.terminate_tools=['transfer_to_human_agents'];env.calculate_reward=lambda:SimpleNamespace(reward=0.0,info=None)
  for c in r['calls']:
   try:
    if c['name'] in tools:env.step(ns['Action'](name=c['name'],kwargs=c['kwargs']))
   except Exception:pass
  gold=old.make_env(ns,tools,base,task)
  for a in task.actions:gold.step(a)
  h=lambda data:ns['consistent_hash'](ns['to_hashable'](copy.deepcopy(data)))
  eq=h(env.data)==h(gold.data)
  out=all(any(m.get('role')=='assistant' and o.lower() in m.get('content','').lower().replace(',','') for m in r['agent_messages']) for o in task.outputs)
  assert eq==r['db_eq'] and out==r['r_outputs'] and int(eq and out)==r['native_reward'],str(ep)
  for rp in ep.parent.glob('*/*/result.json'):
   res=read(rp);assert res['requested_model']==res['reported_model']=='gpt-6-luna';assert res['reasoning_effort']=='low';assert res['instruction_sources']==[]
   attempt=rp.parent/res['attempt'];tr=read(attempt/'thread_response.json');assert tr['model']=='gpt-6-luna' and tr['modelProvider']=='openai'
   assert (attempt/'events.jsonl').stat().st_size>0
   n+=1;tokens+=res['usage'].get('output_tokens',0)
  rewards+=r['native_reward'];calls+=len(r['calls'])
 write(HERE/'formal_validation.json',{'complete':True,'runs':len(rows),'distinct_tasks':75,'train_customers':p['train_counts']['customers'],'test_customers':p['test_counts']['customers'],'real_tool_calls':calls,'model_calls':n,'native_reward_sum':rewards,'reward_recomputed_runs':150,'output_tokens':tokens,'plan_sha256':sha(HERE/'formal_plan.json'),'claims':'same provider second model; existing retail/public customers; no independent human audit; no live cover'})
 print(read(HERE/'formal_validation.json'))
if __name__=='__main__':main()
