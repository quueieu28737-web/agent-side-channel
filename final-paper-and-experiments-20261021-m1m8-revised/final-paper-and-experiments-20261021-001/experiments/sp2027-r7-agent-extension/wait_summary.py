from common import *
import time,subprocess,sys
while not (HERE/'formal_collection.json').exists():time.sleep(20)
subprocess.run([sys.executable,'-B',str(HERE/'summarize.py')],check=True)

