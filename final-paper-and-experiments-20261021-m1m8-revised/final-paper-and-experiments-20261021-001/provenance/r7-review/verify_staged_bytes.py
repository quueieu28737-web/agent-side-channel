"""Check Git's index stores staged publication files without byte conversion."""
from pathlib import Path
import subprocess,hashlib,json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
raw=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=R)
changed=set(subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'],cwd=R).decode('utf8').split('\0'))
count=0
for entry in raw.split(b'\0'):
 if not entry:continue
 meta,name=entry.split(b'\t',1);path=name.decode('utf8')
 if path not in changed:continue
 mode,blob,stage=meta.decode().split();assert stage=='0',path
 data=(R/path).read_bytes();digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 assert digest==blob,('INDEX_BYTES_DIFFER',path)
 assert len(data)<100*1024**2,('GITHUB_FILE_LIMIT',path)
 count+=1
assert count>0,'No staged changes to check'
print(json.dumps({'status':'STAGED_BYTES_AND_PER_FILE_SIZE_PASS','files':count}))
