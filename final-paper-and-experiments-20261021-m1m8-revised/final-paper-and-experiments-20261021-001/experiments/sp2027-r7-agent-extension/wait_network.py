from common import *
import time,subprocess,sys
while not (HERE/'formal_collection.json').exists():time.sleep(20)
if read(HERE/'formal_collection.json')['completed_runs']==150:
 commands=[['network_replay.py','calibrate'],['network_replay.py','capture','--workers','2'],['evaluate_network.py']]
 logs=[]
 for args in commands:
  r=subprocess.run([sys.executable,'-B',str(HERE/args[0]),*args[1:]],text=True,capture_output=True)
  logs.append({'command':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});write(HERE/'network_process_log.json',logs)
  if r.returncode:break

