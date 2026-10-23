"""Continue an already-running training collection, with fail-closed stage gates.

This driver never changes a model, prompt, split, or sample count and never
publishes a manuscript. Run only one instance. Stage logs are retained.
"""
import datetime
import shutil
import subprocess
import time
import traceback
from common import *
from lock_runtime import verify_runtime

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def snapshot_server(partition):
    # Exact cwd comes from the experiment's own saved thread response.
    ids=set(read(HERE/'split.json')[partition])
    candidates=[p for p in (HERE/'runs').glob('*/task-*/**/thread_response.json')
                if int(p.relative_to(HERE/'runs').parts[1].split('-')[1]) in ids]
    if not candidates: return
    for p in sorted(candidates,key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            # A live writer may have created a file but not finished its JSON.
            tmp=Path(read(p)['cwd']);src=tmp/'server.stderr'
            if src.is_file():
                dest=HERE/'infrastructure'/f'{partition}-server-sol.log'
                dest.parent.mkdir(exist_ok=True)
                shutil.copyfile(src,dest)
                return
        except (OSError,ValueError,KeyError):
            continue

def main():
    status={'started_utc':now(),'model':MODEL,'planned_episodes':690,'stage':'waiting_training','completed':[]}
    path=HERE/'pipeline_status.json'
    def save(): status['updated_utc']=now();write(path,status)
    def run(stage,args,partition=None):
        verify_runtime()
        status['stage']=stage;save()
        logs=HERE/'infrastructure';logs.mkdir(exist_ok=True)
        with (logs/(stage+'.log')).open('a',encoding='utf-8') as log:
            proc=subprocess.Popen([sys.executable,'-B',*args],cwd=HERE,stdout=log,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            while proc.poll() is None:
                if partition: snapshot_server(partition)
                time.sleep(10)
            if proc.returncode: raise RuntimeError(f'{stage} failed (exit {proc.returncode}); inspect {stage}.log')
        status['completed'].append({'stage':stage,'finished_utc':now()});save()
        print('COMPLETED',stage,flush=True)
    try:
        verify_runtime();save()
        while not (HERE/'train_collection.json').exists():
            if (HERE/'train_errors.json').exists(): raise RuntimeError('Training collector reported infrastructure errors')
            snapshot_server('train');time.sleep(10)
        from defense import episodes,validate_calibration
        assert len(episodes('train'))==414
        run('calibrate',['defense.py','calibrate'])
        validate_calibration()
        # Preserve the exact pre-test analysis implementation and calibration hash.
        import e67_eval, reanalyze, e6_e7_retail_cover, tlslab
        analysis_files=[HERE/n for n in ('defense.py','evaluate.py','verify_r4.py')]
        analysis_files += [Path(m.__file__) for m in (e67_eval,reanalyze,e6_e7_retail_cover,tlslab)]
        pin={'frozen_utc':now(),'calibration_sha256':sha(HERE/'calibration.json'),
             'protocol_sha256':sha(HERE/'protocol.json'),
             'files':{str(p.relative_to(EXP)):sha(p) for p in analysis_files}}
        frozen=HERE/'pretest_analysis_manifest.json'
        if frozen.exists():
            previous=read(frozen);pin['frozen_utc']=previous['frozen_utc'];assert pin==previous
        else: write(frozen,pin)
        run('collect_test',['collect.py','--partition','test','--workers','2'],'test')
        assert len(episodes('test'))==276
        assert all(sha(EXP/n)==digest for n,digest in pin['files'].items()),'Pre-test analysis implementation changed'
        run('capture',['defense.py','capture','--workers','8'])
        run('evaluate',['evaluate.py'])
        status['stage']='verify';save()
        from verify_r4 import verify
        valid=verify();write(HERE/'validation.json',valid)
        assert valid['status']=='VERIFIED' and valid['episodes']==690
        status['completed'].append({'stage':'verify','finished_utc':now()})
        status['stage']='analysis_verified_manuscript_pending';save()
        print(json.dumps(valid),flush=True)
    except Exception as exc:
        status.update(stage='failed',error=str(exc),traceback=traceback.format_exc());save()
        raise

if __name__=='__main__':main()
