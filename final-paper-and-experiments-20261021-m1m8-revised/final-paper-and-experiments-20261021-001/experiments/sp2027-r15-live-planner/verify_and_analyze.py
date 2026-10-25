from common import *
import numpy as np,datetime,collections,time
ns,tools,base,tasks=load();plan=read(HERE/'protocol.json');rows=[];checks=0
for tid in plan['sample']:
 for arm in ['baseline','joint']:
  d=HERE/'formal'/arm/f'task-{tid:03d}-repeat-0';r=read(d/'episode.json');m=read(d/'live_metrics.json')
  assert r['inference_fingerprint']==inference_fingerprint()
  actual=old.make_env(ns,tools,base,tasks[tid]);gold=old.make_env(ns,tools,base,tasks[tid])
  for c in r['calls']:
   if c['name'] in tools:
    try:actual.step(ns['Action'](name=c['name'],kwargs=c['kwargs']))
    except Exception:pass
  for a in tasks[tid].actions:gold.step(a)
  equal=ns['consistent_hash'](ns['to_hashable'](actual.data))==ns['consistent_hash'](ns['to_hashable'](gold.data))
  outputs=all(any(msg.get('role')=='assistant' and o.lower() in msg.get('content','').lower().replace(',','') for msg in r['agent_messages']) for o in tasks[tid].outputs)
  assert equal==r['db_eq'] and int(equal and outputs)==r['native_reward']
  assert m['real_calls']==len(r['calls'])==len(m['rows'])
  assert m['timeouts']==sum(v['timeout'] for v in m['rows'])
  # Frozen collection used Windows GetTickCount64 (15.625 ms resolution).
  # A 20 ms sleep can be represented as a 15/16 ms tick difference.
  resolution=time.get_clock_info('monotonic').resolution
  for i,v in enumerate(m['rows']):
   planned=.02+(.2 if i==0 and tid%5==0 else 0)+(.02 if v['cover_action'] else 0)
   assert v['elapsed_seconds']>=planned-resolution-.001
   assert v['timeout']==(planned>.12)
  assert arm=='joint' or m['cover_calls']==0
  results=list(d.glob('*/*/result.json'));assert len(results)==r['model_calls']
  rows.append(dict(task=tid,user=r['user'],arm=arm,reward=r['native_reward'],status=r['status'],**{k:m[k] for k in ['real_calls','cover_calls','timeouts','post_timeout_actions']},latencies=[v['elapsed_seconds'] for v in m['rows']]))
  checks+=8
users=sorted(set(r['user'] for r in rows));diff={u:[] for u in users}
for tid in plan['sample']:
 a=next(r for r in rows if r['task']==tid and r['arm']=='baseline');b=next(r for r in rows if r['task']==tid and r['arm']=='joint');diff[a['user']].append(b['reward']-a['reward'])
rng=np.random.default_rng(20261025);draws=[]
for _ in range(2000):
 picked=rng.choice(users,len(users),replace=True);vals=[v for u in picked for v in diff[u]];draws.append(np.mean(vals))
summary={arm:{'episodes':50,'successes':sum(r['reward'] for r in rows if r['arm']==arm),'protocol_errors':sum(r['status']=='protocol_error' for r in rows if r['arm']==arm),'timeouts':sum(r['timeouts'] for r in rows if r['arm']==arm),'post_timeout_actions':sum(r['post_timeout_actions'] for r in rows if r['arm']==arm),'real_calls':sum(r['real_calls'] for r in rows if r['arm']==arm),'cover_calls':sum(r['cover_calls'] for r in rows if r['arm']==arm),'tool_response_p95_seconds':float(np.quantile([v for r in rows if r['arm']==arm for v in r['latencies']],.95))} for arm in ['baseline','joint']}
write(HERE/'live_analysis.json',{'summary':summary,'paired_reward_difference':np.mean([v for vs in diff.values() for v in vs]),'customer_bootstrap_ci95':np.quantile(draws,[.025,.975]).tolist(),'customers':len(users),'rows':rows,'scope':'Prefix-shadow scheduler with emulated tool delays and injected deadline faults; no episode-end flush or TLS framing; not original full joint deployment or WAN measurement'})
write(HERE/'verification.json',{'passed':True,'episodes':100,'checks':checks,'reward_state_reconstructed':True,'model_request_counts_checked':True,'clock_implementation':time.get_clock_info('monotonic').implementation,'clock_resolution_seconds':resolution,'deadline_schedule_recomputed':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print('LIVE_VERIFIED',summary,flush=True)
