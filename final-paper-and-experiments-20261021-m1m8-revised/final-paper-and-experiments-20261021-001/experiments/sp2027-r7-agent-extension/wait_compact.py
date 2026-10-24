from common import *
import time,subprocess,sys
needed=['formal_summary.json','D2_suite.json','network_results.json','constant_output_diagnostic.json','public_network_validation.json','formal_validation.json']
while not all((HERE/n).exists() for n in needed):time.sleep(20)
r=subprocess.run([sys.executable,'-B',str(HERE/'make_compact.py')],text=True,capture_output=True)
write(HERE/'compact_process.json',{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
