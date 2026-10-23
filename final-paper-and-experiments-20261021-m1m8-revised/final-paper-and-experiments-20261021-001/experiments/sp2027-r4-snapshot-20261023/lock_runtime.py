"""Freeze inference implementation and pinned environment before formal collection."""
import platform
import subprocess
from common import *

def current():
    names=[HERE/n for n in ('collect.py','common.py','rpc_backend.py','model_instructions.txt','action.schema.json')]
    names += [EXP/'reviewer-audit/retail_replay.py',EXP/'sp2027-r2/agent/episode.py']
    names += sorted((EXP/'tau-cover-bridge/vendor').glob('*'))
    return {'protocol_sha256':sha(HERE/'protocol.json'),'split_sha256':sha(HERE/'split.json'),
        'files':{str(p.relative_to(EXP)):sha(p) for p in names if p.is_file()},
        'python':platform.python_version(), 'codex':subprocess.check_output(['codex','--version'],text=True).strip()}

def verify_runtime():
    assert read(HERE/'runtime_manifest.json')==current(),'Runtime changed; refuse to mix model data'

if __name__=='__main__':
    path=HERE/'runtime_manifest.json';obj=current()
    if path.exists():assert read(path)==obj
    else:write(path,obj)
    print('INFERENCE_RUNTIME_FROZEN',sha(path))
