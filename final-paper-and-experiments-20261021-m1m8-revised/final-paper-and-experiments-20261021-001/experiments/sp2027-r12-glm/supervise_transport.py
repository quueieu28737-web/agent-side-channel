"""Transport-only bounded recovery; frozen inference sources remain unchanged."""
from pathlib import Path
import json, datetime, subprocess, sys, time, runpy, urllib.request
E=Path(__file__).resolve().parent

def count():return len(list((E/'formal').glob('*/task-*/episode.json')))
def state(value,**kw):
    (E/'supervisor_status.json').write_text(json.dumps(dict(state=value,completed=count(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw),indent=2))

if '--worker' in sys.argv:
    original=urllib.request.urlopen
    def patient_open(*args,**kwargs):
        kwargs['timeout']=600
        start=time.monotonic()
        try:return original(*args,**kwargs)
        except Exception as exc:
            # Exception class and elapsed time only: never log request headers/credentials.
            with (E/'transport_events.jsonl').open('a') as f:
                f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),error=type(exc).__name__,elapsed_seconds=round(time.monotonic()-start,3)))+'\n')
            raise
    urllib.request.urlopen=patient_open
    runpy.run_path(str(E/'run.py'),run_name='__main__')
else:
    failures=0; attempt=0
    while True:
        before=count();attempt+=1
        state('running',attempt=attempt,no_progress_failures=failures)
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        with (E/f'supervised-{stamp}.stdout.log').open('w') as out,(E/f'supervised-{stamp}.stderr.log').open('w') as err:
            rc=subprocess.call([sys.executable,'-u',str(Path(__file__).resolve()),'--worker'],stdout=out,stderr=err,cwd=E)
        if rc==0:
            state('analyzing')
            rc=subprocess.call([sys.executable,str(E/'finish_analysis.py')],cwd=E)
            state('verified_pending_manuscript' if rc==0 else 'blocked_analysis')
            break
        s=json.loads((E/'status.json').read_text())
        error=s.get('error','')
        transient=('Transport failure:' in error or any('HTTP '+str(c) in error for c in (408,429,500,502,503,504)))
        failures=failures+1 if count()==before else 0
        if not transient or failures>=3:
            state('blocked',error=error,no_progress_failures=failures);break
        state('backoff',seconds=60,no_progress_failures=failures,error=error)
        time.sleep(60)
