from pathlib import Path
import json,time,subprocess,sys
E=Path(__file__).resolve().parent
while True:
 s=json.loads((E/'status.json').read_text())
 if s['state']=='blocked':break
 if s['state']=='complete_pending_analysis':
  r=subprocess.run([sys.executable,str(E/'verify_and_analyze.py')],cwd=E)
  (E/'analysis_status.json').write_text(json.dumps({'state':'verified_pending_manuscript' if r.returncode==0 else 'blocked_analysis','returncode':r.returncode}))
  break
 time.sleep(30)
