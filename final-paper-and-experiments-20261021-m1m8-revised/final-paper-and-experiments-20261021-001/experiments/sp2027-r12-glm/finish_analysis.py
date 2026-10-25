"""Wait for completed replay; run the frozen analyses once, without model credentials."""
from common import *
import time,subprocess,datetime,traceback

def main():
    while True:
        state=read(HERE/'status.json') if (HERE/'status.json').exists() else {}
        if state.get('state')=='blocked':
            write(HERE/'analysis_status.json',{'state':'blocked_by_collection','collection':state});return
        if state.get('state')=='collected_and_replayed_pending_analysis':break
        time.sleep(30)
    freeze=read(HERE/'analysis_freeze.json')
    for name,digest in freeze['source_hashes'].items():assert sha(HERE/name)==digest,name
    for name in ('evaluate_network.py','evaluate_d2.py','localize_network.py','verify_results.py'):
        write(HERE/'analysis_status.json',{'state':'running','step':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        subprocess.run([sys.executable,str(HERE/name)],check=True)
    write(HERE/'analysis_status.json',{'state':'verified_pending_manuscript','utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})

if __name__=='__main__':
    try:main()
    except Exception:
        write(HERE/'analysis_status.json',{'state':'blocked','traceback':traceback.format_exc()});raise
