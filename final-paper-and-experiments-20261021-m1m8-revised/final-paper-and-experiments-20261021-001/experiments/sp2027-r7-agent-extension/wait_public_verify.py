from common import *
import time,subprocess,sys
while not (HERE/'formal_collection.json').exists():time.sleep(20)
if read(HERE/'formal_collection.json')['completed_runs']==150:
 while not ((HERE/'raw_archive.json').exists() and (HERE/'network_results.json').exists()):
  if (HERE/'network_process_log.json').exists() and any(x['returncode'] for x in read(HERE/'network_process_log.json')):raise SystemExit('Network analysis failed; see log')
  time.sleep(20)
 r=subprocess.run([sys.executable,'-B',str(HERE/'verify_public.py'),'--network'],text=True,capture_output=True)
 write(HERE/'public_validation_process.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})

