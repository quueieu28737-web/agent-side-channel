"""R13 / Exp 4 WAN Extension: live tool execution under netem WAN latency and jitter."""
import hashlib
import json
import os
import sys
from pathlib import Path

for key_env in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key_env] = '1'

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
R4 = HERE.parent / 'sp2027-r4-snapshot-20261023'
FULL = HERE.parent / 'sp2027-r4-full-20261023'
R6 = HERE.parent / 'sp2027-r6-timing'

sys.path.insert(0, str(HERE.parent / 'sp2027-r5-crossfit'))
import r5lib as lib

read, write, sha = lib.read, lib.write, lib.sha

CONDITIONS = ['raw', 'padding', 'shadow_serial', 'tunnel_2ms']

WAN_PROFILES = {
    'wan_20ms': {'delay_ms': 20.0, 'jitter_ms': 5.0, 'name': 'WAN 20ms delay, 5ms jitter'},
    'wan_50ms': {'delay_ms': 50.0, 'jitter_ms': 10.0, 'name': 'WAN 50ms delay, 10ms jitter'}
}

SEED = 20261024

def key(e):
    return f"{e['prompt']}-t{e['task']:03d}-r{e['repeat']}"

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def inputs():
    rows, split = lib.all_episodes('full')
    assert len(rows) == 690 and len(split['train']) == 69 and len(split['test']) == 46
    return rows, split, read(R4 / 'calibration.json')

def request(c, i, kind):
    return {'id': i, 'kind': kind, 'name': c['name'], 'kwargs': c['kwargs']}

def invoke(tools, data, c):
    if c['name'] not in tools:
        return 'Unknown action ' + c['name']
    return lib.invoke(tools, data, c['name'], c['kwargs'])
