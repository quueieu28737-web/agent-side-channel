"""Read-only common-seven sensitivity from existing D predictions; no fitting."""
import sys,json,hashlib
from pathlib import Path
h=Path(__file__).resolve().parent;root=h.parents[1];d=root/'experiments/sp2027-r7-robustness';sys.path.insert(0,str(d));import r7common as D
import numpy as np
pred=D.read(d/'predictions.json');allres=D.read(d/'results.json');cells={};draws={};aucs={};names=None
for key,u in pred.items():
 common={n:v for n,v in u['models'].items() if not n.startswith('E13/')};assert len(common)==7
 if names is None:names=sorted(common)
 assert sorted(common)==names
 w=D.r6.weights(u['customers']);bs=[];aas=[];per={}
 for n,v in common.items():
  b,a=D.r6.metric_draws(u['labels'],v['scores'],v['predictions'],w);bs.append(b);aas.append(a);per[n]={'ba':float(b[0]),'auroc':float(a[0])}
 b=np.nanmax(bs,axis=0);a=np.nanmax(aas,axis=0);draws[key]=b;aucs[key]=a
 cells[key]={'ba':D.r6.brief(b),'auroc':D.r6.brief(a),'suite_size':7,'strongest_ba':[n for n,v in per.items() if abs(v['ba']-b[0])<1e-12],'attackers':per,'original_full_union_ba':allres['cells'][key]['ba'],'original_full_union_size':allres['cells'][key]['suite_size']}
points={}
for arm in ['baseline','rules']:
 for cond in D.CONDITIONS:
  c=arm+'|'+cond;pair=np.maximum(draws[c+'|cancel'],draws[c+'|return'])
  points[c]={'cancel':cells[c+'|cancel']['ba'],'return':cells[c+'|return']['ba'],'two_target_max_ba':D.r6.brief(pair),'resources':allres['resources'][c]}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'scope':'Unfrozen posthoc audit sensitivity only. All original D full-union results remain unchanged. Common suite excludes names beginning E13/ and retains all seven R7 models on every one of 13 conditions, both prompts.','sources':{p.name:sha(p) for p in [d/'predictions.json',d/'results.json',d/'run.py',d/'freeze.json']},'common_models':names,'bootstrap':'Original D.r6.weights and metric_draws; 2000 common customer draws; maximum reselected per draw. two_target_max_ba uses draw-wise max of cancel and return.','cells':cells,'points':points}
(root/'provenance/r7-review/common-suite-audit.json').write_text(json.dumps(record,indent=2),encoding='utf8');(h/'common-suite-audit.json').write_text(json.dumps(record,indent=2),encoding='utf8');np.savez_compressed(h/'common-suite-bootstrap.npz',**draws);print('COMMON7 AUDIT',len(cells),'cells',len(points),'prompt/condition points',names)

