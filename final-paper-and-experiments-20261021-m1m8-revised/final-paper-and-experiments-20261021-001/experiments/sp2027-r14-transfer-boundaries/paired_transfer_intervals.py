"""Customer-paired suite-max contrasts conditional on saved fitted attacks."""
from pathlib import Path
import sys,numpy as np
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent/'sp2027-r12-glm'))
import evaluate_network as en
data=[r for r in en.read(D/'full_suite_results.json') if r['study']=='calibration_transfer']
def dist(row):
 return np.fmax.reduce([en.stats.distributions(row['units'],np.array(a['scores']),np.array(a['predictions']),2000)[0] for a in row['attacks'].values()])
rows=[]
for target in sorted({r['target'] for r in data}):
 for label in en.ev.TARGETS:
  local=next(r for r in data if r['source']==target and r['target']==target and r['condition']=='transferred_joint' and r['label']==label)
  dlocal=dist(local)
  for r in data:
   if r['target']!=target or r['label']!=label or r is local:continue
   assert r['units']==local['units']
   delta=dist(r)-dlocal
   rows.append(dict(target=target,source=r['source'],condition=r['condition'],label=label,difference=float(delta[0]),ci95=np.nanquantile(delta[1:],[.025,.975]).tolist(),contrast='condition minus target-local joint, suite max reselected on common customer draws; conditional on fitted predictions'))
en.write(D/'paired_transfer_intervals.json',rows)
for r in rows:print(r['source'],r['target'],r['condition'],r['label'],round(r['difference']*100,1),[round(v*100,1) for v in r['ci95']])
