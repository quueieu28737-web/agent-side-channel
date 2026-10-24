from common import *
import time,subprocess,sys
while True:
 path=HERE/'formal_collection.json'
 if path.exists():
  data=read(path)
  if data['completed_runs']==150:
   subprocess.run([sys.executable,'-B',str(HERE/'evaluate_d2.py')],check=True)
  else:write(HERE/'D2_unavailable.json',{'reason':'Formal 150 incomplete; no complete planned test analysis','completed_runs':data['completed_runs']})
  break
 time.sleep(20)

