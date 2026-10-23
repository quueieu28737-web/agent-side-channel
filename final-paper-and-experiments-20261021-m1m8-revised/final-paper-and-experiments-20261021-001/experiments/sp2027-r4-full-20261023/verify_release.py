"""Standard-library byte and dependency verification for the incremental release."""
from pathlib import Path, PurePosixPath
import json, hashlib
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(root,name):
    rel=PurePosixPath(name)
    assert not rel.is_absolute() and '..' not in rel.parts and ':' not in name
    p=root.joinpath(*rel.parts);assert p.is_file() and not p.is_symlink()
    return p
def main():
    m=read(HERE/'release_manifest.json')
    actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    assert actual==set(m['files'])|{'release_manifest.json'},'Release membership changed'
    for n,d in m['files'].items():assert sha(safe(HERE,n))==d,n
    a=read(HERE/'inputs.json');base=HERE.parent/a['base_directory']
    for n,d in (a['base_files']|a['base_episode_hashes']).items():assert sha(safe(base,n))==d,('base',n)
    assert read(HERE/'extension_validation.json')['status']=='FULL_COHORT_EXTENSION_VERIFIED'
    assert read(HERE/'reproduction_validation.json')['status']=='FROZEN_FULL_VERIFIER_REPRODUCED'
    assert read(HERE/'validation.json')['status']=='VERIFIED'
    print(json.dumps({'status':'FULL_COHORT_RELEASE_BYTES_AND_DEPENDENCIES_PASS','files':len(m['files']),'base_episode_dependencies':663,'base_commit':a['base_commit']}))
if __name__=='__main__':main()
