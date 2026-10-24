import time, traceback, datetime
from common import *
from collect import episode
if __name__=='__main__':
    start=time.monotonic(); failures=0; results=[]; errors=[]
    ids=[0,1,2,3,4]
    write(HERE/'pilot_plan.json',{'task_ids':ids,'arms':PROMPTS,'repeats':[0],'runs':len(ids)*2,'new_customer_count':0,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    for tid in ids:
        for arm in PROMPTS:
            began=time.monotonic()
            try:
                r=episode(tid,0,arm,HERE/'pilot'); results.append(r);failures=0
                print(json.dumps({'task':tid,'arm':arm,'reward':r['native_reward'],'calls':len(r['calls']),'elapsed':r['elapsed_seconds']}),flush=True)
            except Exception as exc:
                failures+=1;errors.append({'task':tid,'arm':arm,'error':str(exc),'elapsed_seconds':time.monotonic()-began,'traceback':traceback.format_exc()})
                write(HERE/'pilot_errors.json',errors);print(json.dumps(errors[-1]),flush=True)
            write(HERE/'pilot_summary.json',{'completed_runs':len(results),'target_runs':10,'elapsed_seconds':time.monotonic()-start,'reward_sum':sum(r['native_reward'] for r in results),'errors':len(errors),'consecutive_failures':failures,'T2_scale_achieved':False})
            if failures>=3:raise SystemExit('Stopped after three consecutive failures without new result')

