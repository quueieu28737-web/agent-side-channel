from common import *
import numpy as np
from collections import Counter

def main():
 plan=read(HERE/'formal_plan.json');rows=[read(p) for p in (HERE/'formal').glob('*/task-*/episode.json')];out={}
 for arm in PROMPTS:
  for part,ids in [('all',plan['train']+plan['test']),('train',plan['train']),('test',plan['test'])]:
   r=[s for s in rows if s['prompt']==arm and s['task'] in ids]
   if not r:continue
   out[arm+'_'+part]={'runs':len(r),'customers':len(set(x['user'] for x in r)),'reward_sum':sum(x['native_reward'] for x in r),'success_rate':float(np.mean([x['native_reward'] for x in r])),'mean_episode_seconds':float(np.mean([x['elapsed_seconds'] for x in r])),'median_episode_seconds':float(np.median([x['elapsed_seconds'] for x in r])),'p95_episode_seconds':float(np.quantile([x['elapsed_seconds'] for x in r],.95)),'real_tool_calls':sum(len(x['calls']) for x in r),'model_calls':sum(x['model_calls'] for x in r),'status_counts':dict(Counter(x['status'] for x in r))}
 attempts=list((HERE/'formal').glob('*/*/*/*/attempt-*'))
 out['collection']={'completed_runs':len(rows),'unique_tasks':len(set(r['task'] for r in rows)),'customers':len(set(r['user'] for r in rows)),'attempts':len(attempts),'logged_infrastructure_errors':len(list((HERE/'formal').rglob('infrastructure_error.json'))),'automatic_retries':0,'plan_sha256':sha(HERE/'formal_plan.json'),'elapsed_seconds_including_pilot_wait':read(HERE/'formal_collection.json')['elapsed_seconds'],'same_provider_second_model':True}
 write(HERE/'formal_summary.json',out);print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
