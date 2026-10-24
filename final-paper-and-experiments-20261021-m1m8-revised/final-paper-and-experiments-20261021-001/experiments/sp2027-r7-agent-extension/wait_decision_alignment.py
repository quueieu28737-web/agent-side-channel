from common import *
import time,subprocess,sys
while not (HERE/'formal_collection.json').exists():time.sleep(20)
if read(HERE/'formal_collection.json')['completed_runs']==150:
 while not (HERE/'raw_archive.json').exists():time.sleep(20)
 logs=[]
 for name in ['verify_decisions.py','verify_public_decisions.py']:
  r=subprocess.run([sys.executable,'-B',str(HERE/name)],text=True,capture_output=True);logs.append({'command':name,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});write(HERE/'decision_alignment_process.json',logs)
  if r.returncode:break
