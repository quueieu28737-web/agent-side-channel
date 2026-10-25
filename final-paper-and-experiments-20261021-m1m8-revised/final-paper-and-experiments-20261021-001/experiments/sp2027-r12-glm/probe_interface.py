"""Task-free native tool compatibility probe; no benchmark inputs."""
from pathlib import Path
import json,hashlib,os
from rpc_backend import server
d=Path(__file__).resolve().parent/'interface-probe'
d.mkdir(exist_ok=True)
result=server().infer('Use next_action to return action respond, arguments_json {}, content OK. No other action.',d,timeout=60)
assert result['answer'].get('action')=='respond', 'Native action response missing'
assert result['returned_model']=='glm-5.3-flash','Unexpected returned model; inspect receipt before freezing'
receipt={'passed':True,'requested_model':'glm-5.3-flash','returned_model':result['returned_model'],
    'native_tool_call':True,'tls_verification':True,'ca_sha256':hashlib.sha256(Path(os.environ['GLM_CA_BUNDLE']).read_bytes()).hexdigest(),
    'usage':result['usage'],'scope':'Task-free capability probe; excluded from formal episodes'}
(d/'verification.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
