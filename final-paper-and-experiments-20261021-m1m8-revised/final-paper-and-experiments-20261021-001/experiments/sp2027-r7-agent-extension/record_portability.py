from common import *
import importlib.metadata,datetime
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r3'/'deps'));sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r7-agent-deps'))
core=read(HERE/'dependency_versions.json');extra={n:importlib.metadata.version(n) for n in ['pydantic','pydantic_core','typing_extensions','annotated-types','typing-inspection','cffi','pycparser']}
all_versions=dict(core['packages'],**extra);write(HERE/'dependency_versions_full.json',{'python':core['python'],'packages':all_versions})
(HERE/'requirements-public.txt').write_text(''.join(n+'=='+v+'\n' for n,v in all_versions.items()),encoding='utf-8')
write(HERE/'PORTABILITY_ADDITION.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Complete pinned public sandbox transitive dependencies including pydantic; no collection or analysis algorithm change','files':{n:sha(HERE/n) for n in ['requirements-public.txt','dependency_versions_full.json']}})
print(extra)
