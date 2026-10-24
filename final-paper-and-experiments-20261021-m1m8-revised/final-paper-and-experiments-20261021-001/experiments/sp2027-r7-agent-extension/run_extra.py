from common import *
from collect import episode
from concurrent.futures import ThreadPoolExecutor,as_completed
import time,traceback
if __name__=='__main__':
    failures=0
    jobs=[(t,a) for t in [2,3,4] for a in PROMPTS]
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending={pool.submit(episode,t,0,a,HERE/'pilot'):(t,a) for t,a in jobs}
        for f in as_completed(pending):
            try:
                r=f.result();failures=0;print(json.dumps({'task':r['task'],'arm':r['prompt'],'reward':r['native_reward'],'calls':len(r['calls']),'elapsed':r['elapsed_seconds']}),flush=True)
            except Exception as e:
                failures+=1;write(HERE/('extra-error-'+str(pending[f])+'.json'),{'error':str(e),'traceback':traceback.format_exc()});print(str(e),flush=True)
            if failures>=3:
                for other in pending:other.cancel()
                break
