"""Bind the restored E6 main table to its preserved historical result file."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;P=O.parents[1]
data=json.loads((P/'experiments/sp2027-r3/e6_dispatch_results.json').read_text())
text=(P/'manuscript/tables/r7-e6-main.tex').read_text()
names=['none','cancel_p50_shadow','cancel_p100_shadow','cancel_p100_live','cancel_const2_shadow','decoy1_shadow','decoy2_shadow','shape_eq_shadow']
lines=[l for l in text.splitlines() if ' & ' in l and ('100\\%' in l or '0\\%' in l)]
assert len(lines)==len(names)
for name,line in zip(names,lines):
 cells=[v.strip() for v in line.split('&')]
 vals=[next(v for v in data if (v['cover'],v['target'])==(name,t)) for t in ('cancel','return')]
 assert cells[1]=='/'.join(f"{v['best_ba']*100:.1f}" for v in vals),(name,cells[1])
 assert float(cells[2])==round(vals[0]['call_overhead'],2)
 assert int(re.match(r'(\d+)',cells[3]).group(1))==round(vals[0]['db_equality']*100)
 assert all(v['tasks']==115 and v['units']==345 for v in vals)
print('RESTORED_E6_MAIN_TABLE_EXACT_HISTORICAL_VALUES_PASS')
