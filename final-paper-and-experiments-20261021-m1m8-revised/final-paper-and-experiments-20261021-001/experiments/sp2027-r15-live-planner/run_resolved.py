from pathlib import Path
import importlib.util,sys,runpy,json
E=Path(__file__).resolve().parent
# Bind the experiment-local backend before shared modules prepend import paths.
spec=importlib.util.spec_from_file_location('rpc_backend',E/'rpc_backend.py')
module=importlib.util.module_from_spec(spec);sys.modules['rpc_backend']=module;spec.loader.exec_module(module)
assert Path(module.__file__).resolve()==(E/'rpc_backend.py').resolve()
(E/'adapter_resolution.json').write_text(json.dumps({'backend':'rpc_backend.py','timeout_seconds':600,'method':'explicit local module binding before shared imports'}))
runpy.run_path(str(E/'run_live.py'),run_name='__main__')
