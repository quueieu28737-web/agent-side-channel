"""Bounded one-shot continuation: training -> frozen attackers -> test -> evaluation."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent

def status(stage,**extra):
    obj={'stage':stage,'updated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),**extra}
    (HERE/'pipeline_status.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(obj),flush=True)

def main():
    lock=HERE/'.continuation.lock'
    with lock.open('x') as f:f.write(str(os.getpid()))
    try:
        status('waiting_for_training')
        deadline=time.monotonic()+1800
        while not (HERE/'train_complete.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('Training wait exceeded 30 minutes')
            p=HERE/'collection_status.json'
            if p.exists() and time.time()-p.stat().st_mtime>180:raise RuntimeError('Training progress stale for 180 seconds')
            time.sleep(5)
        receipt=json.loads((HERE/'train_complete.json').read_text())
        assert receipt['count']==2484 and not receipt['failures']
        for stage,script,args in (
            ('fitting_training_attackers','analyze.py',['fit']),
            ('collecting_test','experiment.py',['test']),
            ('evaluating_frozen_test','analyze.py',['evaluate'])):
            status(stage)
            if stage=='collecting_test':assert (HERE/'attacker_freeze.json').exists()
            subprocess.run([sys.executable,'-B',str(HERE/script),*args],cwd=HERE,check=True)
        status('measured_and_evaluated')
    except Exception as e:
        status('failed',error=repr(e));raise
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
