"""Matched-attack sensitivity from saved predictions; never changes frozen fits."""
from pathlib import Path
import json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];D=P/'experiments/sp2027-r7-robustness'
sys.path.insert(0,str(D))
from r7common import read,sha
from run import summarize

pred=read(D/'predictions.json')
common=set.intersection(*(set(v['models']) for v in pred.values()))
assert len(common)==7 and not any(n.startswith('E13/') for n in common)
matched={k:dict(v,models={n:a for n,a in v['models'].items() if n in common}) for k,v in pred.items()}
result=summarize(matched)
result.update({'comparison':'Same seven R7 models in every measured and simulated condition; full heterogeneous unions remain separately reported',
 'common_attackers':sorted(common),'input_predictions_sha256':sha(D/'predictions.json'),
 'full_results_sha256':sha(D/'results.json'),'new_model_fits':0,'new_model_calls':0})
path=D/'common-suite.json'
if '--check' in sys.argv:assert read(path)==result
else:path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print('MATCHED_SEVEN_MODEL_SUITE_CHECKED' if '--check' in sys.argv else 'MATCHED_SEVEN_MODEL_SUITE_WRITTEN')
