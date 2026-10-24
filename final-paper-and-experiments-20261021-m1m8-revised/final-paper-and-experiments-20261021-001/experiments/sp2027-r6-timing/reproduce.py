"""Recompute frozen models and compare JSON semantics without writing predictions.

The frozen analysis uses tuple spans in memory and JSON arrays on disk. Its
literal --check comparison therefore rejects identical serialized spans. This
wrapper leaves the frozen analysis bytes unchanged and normalizes only the JSON
representation before comparing every saved output.
"""
import json
import sys
import analyze
from r6common import HERE, read, write, sha

checked={}
def compare_json(path,obj):
    normalized=json.loads(json.dumps(obj,ensure_ascii=False,allow_nan=False))
    assert read(path)==normalized,('Recomputed JSON differs',path.name)
    checked[path.name]=sha(path)

if __name__=='__main__':
    analyze.save=compare_json
    analyze.evaluate()
    assert set(checked)=={'detector_predictions.json','predictions.json','test_cuts.json','results.json'}
    receipt={'status':'FROZEN_MODELS_ALL_PREDICTIONS_AND_METRICS_REPRODUCED',
             'outputs':checked,'attacker_freeze_sha256':sha(HERE/'attacker_freeze.json'),
             'analysis_sha256':sha(HERE/'analyze.py'),'reproduction_code_sha256':sha(HERE/'reproduce.py'),
             'comparison':'Exact JSON-semantic equality; tuple spans normalize to JSON arrays. No tolerance or prediction change.'}
    if '--save' in sys.argv:write(HERE/'reproduction_validation.json',receipt)
    print(json.dumps(receipt,indent=2))
