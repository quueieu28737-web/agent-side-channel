"""Reproduce byte accounting from saved serialized write requests."""
from pathlib import Path
from collections import defaultdict
import json,sys,numpy as np
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
rows=[]
for model in ['sp2027-r11-minimax','sp2027-r12-glm']:
 values=defaultdict(list)
 for p in sorted((E/model/'formal/baseline').glob('*/episode.json')):
  for c in json.loads(p.read_text())['calls']:
   # Retain the one invalid attempted alias `return` as its own diagnostic row.
   # It is never merged with successful return_delivered_order_items calls.
   if c['name'] not in set(en.ev.WRITES)|{'return'}:continue
   obj=json.loads(c['req_text'])
   size=len(json.dumps(obj,sort_keys=True).encode())
   for field in obj['arguments']:
    reduced=json.loads(json.dumps(obj));del reduced['arguments'][field]
    values[(c['name'],field)].append(size-len(json.dumps(reduced,sort_keys=True).encode()))
 for (verb,field),v in values.items():
  rows.append(dict(model=model,verb=verb,field=field,n=len(v),removed_bytes_mean=float(np.mean(v)),removed_bytes_min=min(v),removed_bytes_max=max(v)))
result={'scope':'Exact serialized request byte accounting; field omission is diagnostic only, not a valid API intervention or causal privacy estimate. Response bytes and timing remain separate.','rows':rows}
existing=json.loads((D/'request_field_accounting.json').read_text())
key=lambda r:(r['model'],r['verb'],r['field'])
assert sorted(existing['rows'],key=key)==sorted(rows,key=key)
print('FIELD_ACCOUNTING_REPRODUCED',len(rows))
