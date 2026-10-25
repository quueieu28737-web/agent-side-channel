"""Bounded collection: train, freeze calibration, test, local TLS replay."""
from common import *
from collect_formal import episode
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import datetime, subprocess, traceback

def status(state,**kw):
    write(HERE/'status.json',{'state':state,'completed':len(list((HERE/'formal').glob('*/task-*/episode.json'))),'target':115,
          'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw})

def collect(partition):
    tasks=iter(read(HERE/'formal_plan.json')[partition])
    with ThreadPoolExecutor(max_workers=10) as pool:
        pending={}
        def add():
            tid=next(tasks,None)
            if tid is not None: pending[pool.submit(episode,tid,0,'baseline',HERE/'formal')]=tid
        for _ in range(10):add()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for f in done:
                tid=pending.pop(f)
                row=f.result()
                print(json.dumps({'task':tid,'partition':partition,'reward':row['native_reward'],'calls':len(row['calls']),'status':row['status']}),flush=True)
                status('collecting_'+partition)
                add()

if __name__=='__main__':
    try:
        freeze=HERE/'source_freeze.json'
        names=['common.py','collect_formal.py','rpc_backend.py','network_replay.py','run.py','protocol.json','formal_plan.json','model_instructions.txt','action.schema.json']
        hashes={n:sha(HERE/n) for n in names}
        if freeze.exists(): assert read(freeze)==hashes,'Frozen implementation changed'
        else: write(freeze,hashes)
        collect('train')
        status('calibrating')
        subprocess.run([sys.executable,str(HERE/'network_replay.py'),'calibrate'],check=True)
        collect('test')
        status('replaying')
        subprocess.run([sys.executable,str(HERE/'network_replay.py'),'capture','--workers','2'],check=True)
        status('collected_and_replayed_pending_analysis')
    except Exception as exc:
        status('blocked',error=str(exc),traceback=traceback.format_exc())
        raise
