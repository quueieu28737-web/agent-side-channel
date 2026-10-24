from common import *
import time,subprocess,sys
needed=['formal_validation.json','public_validation.json','decision_alignment.json','public_decision_alignment.json']
while not all((HERE/n).exists() for n in needed):time.sleep(20)
r=subprocess.run([sys.executable,'-B',str(HERE/'correct_verification_receipts.py')],text=True,capture_output=True)
write(HERE/'correction_process.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
