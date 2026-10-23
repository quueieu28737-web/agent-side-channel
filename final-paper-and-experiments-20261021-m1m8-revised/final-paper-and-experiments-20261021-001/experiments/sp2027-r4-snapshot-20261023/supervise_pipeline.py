"""Operational recovery only; never changes frozen inference or analysis files.

Resume temporary collection faults with backoff. Stop after three consecutive
attempts without new complete episodes, or immediately for quota/analysis faults.
"""
import datetime
import shutil
import subprocess
import time
from common import *
from lock_runtime import verify_runtime

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def count(): return sum(1 for _ in (HERE/'runs').glob('*/task-*/episode.json'))

def archive_failure():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=HERE/'infrastructure'/('supervisor-resume-'+stamp)
    dest.mkdir(parents=True)
    for name in ('pipeline_status.json','train_errors.json','test_errors.json'):
        p=HERE/name
        if p.exists():p.rename(dest/name)
    for name in ('train-server-sol.log','test-server-sol.log','collect_test.log'):
        p=HERE/'infrastructure'/name
        if p.exists():shutil.copy2(p,dest/name)
    write(dest/'resume.json',{'utc':now(),'model':MODEL,'reasoning_effort':'low',
        'workers':2,'episodes':count(),'planned_episodes':690,
        'scope':'Operational recovery; frozen model, prompts, split, calibration and analysis retained'})
    return dest

def main():
    lock=HERE/'supervisor.lock'
    with lock.open('x',encoding='utf-8') as f:f.write(str(os.getpid()))
    state={'started_utc':now(),'model':MODEL,'reasoning_effort':'low','workers':2,
        'planned_episodes':690,'consecutive_no_progress_failures':0,'attempts':[]}
    def save(stage,**extra):
        state.update(stage=stage,updated_utc=now(),episodes=count(),**extra)
        write(HERE/'supervisor_status.json',state)
    try:
        verify_runtime()
        assert (HERE/'train_collection.json').exists(),'Training must already be complete'
        while True:
            verify_runtime()
            before=count();dest=archive_failure();save('running')
            with (dest/'pipeline.log').open('w',encoding='utf-8') as log:
                proc=subprocess.Popen([sys.executable,'-B',str(HERE/'continue_pipeline.py')],
                    cwd=HERE,stdout=log,stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                state['pipeline_pid']=proc.pid;save('running')
                while proc.poll() is None:time.sleep(10)
            after=count()
            state['attempts'].append({'archive':str(dest.relative_to(HERE)),
                'finished_utc':now(),'exit_code':proc.returncode,'before':before,'after':after})
            if proc.returncode==0:
                valid=read(HERE/'validation.json')
                assert after==690 and valid['status']=='VERIFIED'
                save('analysis_verified_manuscript_pending');return
            errors=[]
            for name in ('train_errors.json','test_errors.json'):
                if (HERE/name).exists():errors.extend(read(HERE/name))
            text='\n'.join(str(e.get('error','')) for e in errors)
            if any(s in text for s in ('usageLimitExceeded','hit your usage limit','insufficient_quota')):
                save('blocked_quota',error=text);return
            transient=any(s in text for s in ('serverOverloaded','Model turn timeout',
                'Transport closed','App-server exited','responseStreamDisconnected',
                'Connection failed','RPC timeout'))
            if not transient:
                save('blocked_nontransient',error=text or 'Pipeline failed outside collection; inspect pipeline log');return
            state['consecutive_no_progress_failures']=0 if after>before else state['consecutive_no_progress_failures']+1
            if state['consecutive_no_progress_failures']>=3:
                save('blocked_repeated_no_progress',error=text);return
            delay=180*(1+state['consecutive_no_progress_failures'])
            save('backoff',retry_after_seconds=delay,error=text)
            # This local background process waits; the interactive agent is free.
            time.sleep(delay)
    except Exception as exc:
        save('blocked_supervisor',error=str(exc));raise
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':main()
