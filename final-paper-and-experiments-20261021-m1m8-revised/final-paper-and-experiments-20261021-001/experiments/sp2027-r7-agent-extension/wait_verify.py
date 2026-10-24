from common import *
import time,subprocess,sys
while not (HERE/'formal_collection.json').exists():time.sleep(20)
if read(HERE/'formal_collection.json')['completed_runs']==150:
 r=subprocess.run([sys.executable,'-B',str(HERE/'verify_formal.py')],text=True,capture_output=True)
 write(HERE/'validation_process.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})

