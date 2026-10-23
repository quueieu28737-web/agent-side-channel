"""Shared, explicitly frozen R4 experiment configuration."""
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
HERE = Path(__file__).resolve().parent
EXP = HERE.parent
for path in (EXP/'reviewer-audit', EXP/'sp2027-r2', EXP/'sp2027-r2/agent', EXP/'sp2027-r3'):
    sys.path.insert(0, str(path))
import retail_replay as old

MODEL = 'gpt-6.1-sol'
REPEATS = [0, 1, 2]
MAX_STEPS = 30
PROMPTS = ['baseline', 'rules']
RULES = '''Additional workflow-standardization rule:
After identifying the customer using the retail policy, call get_user_details exactly once
before inspecting or changing an order. If an order must be inspected or changed, call
get_order_details for each relevant order before any write to that order. Follow this
same read-before-write workflow regardless of whether the user wants a cancellation,
return, exchange, modification, or only information. Avoid duplicate reads unless the
underlying information changed. Do not add unrelated calls or write operations to hide
intent. Preserve the retail policy, user authorization, and task completion requirements.
These instructions concern the workflow only; do not claim to control packet sizes or timing.'''

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=False)+'\n', encoding='utf-8', newline='\n')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inference_fingerprint():
    return {'model':MODEL,'reasoning_effort':'low','protocol_sha256':sha(HERE/'protocol.json'),
            'runtime_manifest_sha256':sha(HERE/'runtime_manifest.json') if (HERE/'runtime_manifest.json').exists() else None,
            'files':{name:sha(HERE/name) for name in ('collect.py','common.py','rpc_backend.py','model_instructions.txt','action.schema.json')}}

def load():
    return old.load_tau()
