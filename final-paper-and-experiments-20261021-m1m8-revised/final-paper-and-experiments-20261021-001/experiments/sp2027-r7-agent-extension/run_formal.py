from common import *
from collect_formal import episode
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import time,datetime,traceback
if __name__=='__main__':
    plan=read(HERE/'formal_plan.json')
    for n,h in plan['files'].items():
        assert sha(HERE/n)==h, 'Frozen source mismatch '+n
    start=time.monotonic();errors=[];complete=[];failures=0
    # Pilot runs use separate namespaces and are never counted in formal results.
    while len(list((HERE/'pilot').glob('*/task-*/episode.json')))<10:
        write(HERE/'formal_status.json',{'state':'waiting_for_pilot','pilot_completed':len(list((HERE/'pilot').glob('*/task-*/episode.json'))),'formal_completed':0,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        time.sleep(10)
    jobs=iter((t,a) for t in plan['train']+plan['test'] for a in plan['prompts'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending={}
        def add():
            try:t,a=next(jobs)
            except StopIteration:return False
            pending[pool.submit(episode,t,0,a,HERE/'formal')]=(t,a,time.monotonic());return True
        add();add()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for f in done:
                t,a,began=pending.pop(f)
                try:
                    r=f.result();complete.append(r);failures=0
                    print(json.dumps({'completed':len(complete),'task':t,'arm':a,'reward':r['native_reward'],'seconds':r['elapsed_seconds']}),flush=True)
                except Exception as e:
                    failures+=1;errors.append({'task':t,'arm':a,'elapsed_seconds':time.monotonic()-began,'error':str(e),'traceback':traceback.format_exc()});write(HERE/'formal_errors.json',errors)
                    print(json.dumps(errors[-1]),flush=True)
                write(HERE/'formal_status.json',{'state':'stopped_no_results' if failures>=3 else 'collecting','completed_runs':len(complete),'target_runs':150,'errors':len(errors),'consecutive_failures':failures,'elapsed_seconds':time.monotonic()-start,'reward_sum':sum(r['native_reward'] for r in complete),'plan_sha256':sha(HERE/'formal_plan.json'),'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
                if failures<3:add()
            if failures>=3:
                for f in pending:f.cancel()
                break
    write(HERE/'formal_collection.json',{'completed_runs':len(complete),'target_runs':150,'errors':errors,'elapsed_seconds':time.monotonic()-start,'T2_run_count_achieved':len(complete)>=150,'plan_sha256':sha(HERE/'formal_plan.json')})
