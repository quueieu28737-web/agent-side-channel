"""Real model trajectories. Structured actions are executed on the pinned sandbox.

No reference program or reward is included in either model's prompt. Each call
is a fresh bounded Codex app-server inference with full role-labelled history. CLI events,
requests, outputs and usage are cached separately for every repeated episode.
"""
import argparse
import copy
import datetime
import shutil
import subprocess
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from common import *
from episode import USER_SYSTEM

class InfrastructureError(RuntimeError): pass
class ProtocolError(RuntimeError): pass

class Planner:
    def __init__(self, directory, role, cache_only=False):
        self.root=directory/role;self.root.mkdir(parents=True,exist_ok=True)
        self.role=role;self.count=0;self.cache_only=cache_only;self.usage=[]

    def complete(self, messages, schemas=None):
        request={'role':self.role, 'messages':messages, 'tools':schemas or []}
        cache_request=dict(request,inference_fingerprint=inference_fingerprint())
        prompt=('Select the next action in this retail conversation. All tool actions will be executed by the harness. '
                'Use action=respond for a conversation message. '+
                ('You are the simulated user; return action=respond only. ' if self.role=='user' else '')+
                '\n'+json.dumps(request,ensure_ascii=False))
        k=self.count;self.count+=1
        d=self.root/f'{k:03d}';d.mkdir(parents=True,exist_ok=True)
        reqpath=d/'request.json';outpath=d/'result.json'
        if reqpath.exists() and read(reqpath)!=cache_request: raise RuntimeError('Cache request mismatch')
        write(reqpath,cache_request)
        if outpath.exists():
            result=read(outpath)
        else:
            if self.cache_only: raise InfrastructureError('Cache miss')
            from rpc_backend import server, RPCError
            attempt=d/f'attempt-{len(list(d.glob("attempt-*"))):03d}'
            attempt.mkdir()
            try:
                result=server().infer(prompt,attempt,timeout=180)
            except (RPCError,ValueError) as exc:
                write(attempt/'infrastructure_error.json',{'error':str(exc)})
                raise InfrastructureError(str(exc)) from exc
            result.update({'inference_fingerprint':inference_fingerprint(),'attempt':attempt.name,
                'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
            write(outpath,result)
        self.usage.append(result['usage'])
        if result.get('protocol_error'): raise ProtocolError(result['protocol_error'])
        a=result['answer']
        try:
            args=json.loads(a['arguments_json'])
            if not isinstance(args,dict): raise ValueError('Arguments must be an object')
            if self.role=='user' and a['action']!='respond': raise ValueError('User returned a tool action')
            return a['action'],args,a['content']
        except (KeyError,TypeError,ValueError) as e: raise ProtocolError(str(e)) from e

def episode(tid, rep, arm, runroot, cache_only=False):
    d=runroot/arm/f'task-{tid:03d}-repeat-{rep}';d.mkdir(parents=True,exist_ok=True)
    finalpath=d/'episode.json'
    if finalpath.exists():
        saved=read(finalpath)
        if saved.get('inference_fingerprint')!=inference_fingerprint():raise RuntimeError('Episode version mismatch')
        return saved
    ns,tools,base,tasks=load();task=tasks[tid]
    from types import SimpleNamespace
    env=old.make_env(ns,tools,base,task)
    env.terminate_tools=['transfer_to_human_agents']
    env.calculate_reward=lambda: SimpleNamespace(reward=0.0,info=None)
    wiki=(EXP/'tau-cover-bridge/vendor/tau_bench__envs__retail__wiki.md').read_text(encoding='utf-8')
    policy=wiki+('\n\n'+RULES if arm=='rules' else '')
    agent=Planner(d,'agent',cache_only); user=Planner(d,'user',cache_only)
    umsg=[{'role':'system','content':USER_SYSTEM.format(instruction=task.instruction)}]
    def user_reply(text):
        umsg.append({'role':'user','content':text})
        _,_,content=user.complete(umsg)
        umsg.append({'role':'assistant','content':content})
        return content
    class User:
        def step(self,content): return user_reply(content)
        def get_total_cost(self): return 0
    env.user=User()
    schemas=[cls.get_info() for cls in tools.values()]
    from live_controller import Controller
    live=Controller(tid,arm,tools,base)
    calls=[];msgs=[];status='max_steps';start=time.monotonic();responds=0
    try:
        first=user_reply('Hi! How can I help you today?')
        msgs=[{'role':'system','content':policy},{'role':'user','content':first}]
        for step in range(MAX_STEPS):
            name,kw,content=agent.complete(msgs,schemas)
            if name=='respond':
                responds+=1;msgs.append({'role':'assistant','content':content})
                res=env.step(ns['Action'](name='respond',kwargs={'content':content}))
                if res.done: status='user_stop';break
                msgs.append({'role':'user','content':res.observation})
            else:
                msgs.append({'role':'assistant','tool_action':{'name':name,'arguments':kw}})
                if name not in tools:
                    obs='Unknown action '+name;done=False
                else:
                    try:
                        res=env.step(ns['Action'](name=name,kwargs=kw));obs,done=res.observation,res.done
                    except Exception as e:
                        obs='Error: '+type(e).__name__+': '+str(e);done=False
                if not isinstance(obs,str):obs=json.dumps(obs)
                obs=live.response(name,obs)
                req=json.dumps({'name':name,'arguments':kw},sort_keys=True)
                calls.append({'name':name,'kwargs':kw,'req_text':req,'resp_text':obs,
                              'req':len(req.encode()),'resp':len(obs.encode()),
                              'err':obs.startswith('Error:') or obs.startswith('Unknown action')})
                msgs.append({'role':'tool','name':name,'content':obs})
                if done:status='transfer';break
    except ProtocolError as e:
        status='protocol_error';write(d/'protocol_error.json',{'error':str(e)})
    # Reference execution is isolated from model context and used ONLY for scoring.
    gold=old.make_env(ns,tools,base,task)
    for a in task.actions:gold.step(a)
    h=lambda data:ns['consistent_hash'](ns['to_hashable'](copy.deepcopy(data)))
    state_eq=h(env.data)==h(gold.data)
    out_eq=all(any(m.get('role')=='assistant' and o.lower() in m.get('content','').lower().replace(',','') for m in msgs) for o in task.outputs)
    ref=[a.name for a in task.actions]
    result={'task':tid,'repeat':rep,'seed':rep,'prompt':arm,'user':task.user_id,'calls':calls,
        'status':status,'responds':responds,'native_reward':int(state_eq and out_eq),
        'db_eq':state_eq,'r_outputs':out_eq,'has_cancel':int('cancel_pending_order' in ref),
        'has_return':int('return_delivered_order_items' in ref),'agent_messages':msgs,'user_messages':umsg,
        'elapsed_seconds':time.monotonic()-start,'model_calls':agent.count+user.count,
        'usage':{k:sum(u.get(k,0) for u in agent.usage+user.usage) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')},
        'protocol_sha256':sha(HERE/'protocol.json'),'inference_fingerprint':inference_fingerprint()}
    live.save(d)
    write(finalpath,result)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--partition',choices=['pilot','train','test'],required=True)
    ap.add_argument('--workers',type=int,default=6);ap.add_argument('--cache-only',action='store_true')
    a=ap.parse_args();split=read(HERE/'split.json')
    if a.partition!='pilot':
        from lock_runtime import verify_runtime
        verify_runtime()
    if a.partition=='test':
        from defense import validate_calibration
        validate_calibration()
    ids=split['pilot_tasks'] if a.partition=='pilot' else split[a.partition]
    reps=[0] if a.partition=='pilot' else REPEATS
    dest=HERE/('pilot' if a.partition=='pilot' else 'runs')
    jobs=[(t,r,p) for t in ids for r in reps for p in PROMPTS]
    errors=[];n=0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(episode,t,r,p,dest,a.cache_only):(t,r,p) for t,r,p in jobs}
        for f in as_completed(futures):
            job=futures[f]
            try:
                result=f.result();n+=1
                print(json.dumps({'done':n,'total':len(jobs),'task':job[0],'repeat':job[1],'prompt':job[2],
                                  'status':result['status'],'calls':len(result['calls']),'reward':result['native_reward']}),flush=True)
            except Exception as e:
                errors.append({'job':job,'error':str(e),'traceback':traceback.format_exc()})
                write(HERE/(a.partition+'_errors.json'),errors)
                print('INFRASTRUCTURE_ERROR',job,str(e),flush=True)
                # Do not start further work after an unavailable service/account.
                for q in futures:q.cancel()
                break
    if errors:raise SystemExit('Collection incomplete; see error log. Resume same command after resolving infrastructure.')
    write(HERE/(a.partition+'_collection.json'),{'episodes':n,'tasks':len(ids),'repeats':reps,'prompts':PROMPTS,
        'protocol_sha256':sha(HERE/'protocol.json'),'codex_version':subprocess.check_output(['codex','--version'],text=True).strip()})

if __name__=='__main__':main()

