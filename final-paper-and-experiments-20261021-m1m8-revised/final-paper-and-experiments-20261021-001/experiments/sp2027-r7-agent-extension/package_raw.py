"""Publish documented path-redacted copies; original raw evidence remains unchanged."""
from common import *
import zipfile,re

def main():
 paths=sorted(p for sub in ['connectivity','pilot','formal'] for p in (HERE/sub).rglob('*') if p.is_file())
 inventory=[];payload=[];home=str(Path.home());substitutions=0
 secret=re.compile(r'(?i)(authorization\s*[:=]|bearer\s+[A-Za-z0-9._-]+|"(?:access_token|refresh_token|api_key|apiKey)"\s*:)')
 for p in paths:
  original=p.read_bytes();text=original.decode('utf-8-sig');count=[0]
  if secret.search(text):raise RuntimeError('Credential-like content requires manual audit: '+str(p.relative_to(HERE)))
  def clean(obj):
   if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items()}
   if isinstance(obj,list):return [clean(v) for v in obj]
   if isinstance(obj,str):
    for prefix in [home,home.replace('\\','/')]:
     count[0]+=obj.count(prefix);obj=obj.replace(prefix,'<USER_HOME>')
    return obj
   return obj
  if p.suffix=='.jsonl':public=''.join(json.dumps(clean(json.loads(line)),ensure_ascii=False)+'\n' for line in text.splitlines() if line.strip()).encode('utf-8')
  elif p.suffix=='.json':public=(json.dumps(clean(json.loads(text)),ensure_ascii=False,indent=1,allow_nan=False)+'\n').encode('utf-8')
  else:
   value=clean(text);public=value.encode('utf-8')
  if re.search(r'(?i)[a-z]:[\\/]+Users[\\/]+',public.decode('utf-8')):raise RuntimeError('Unredacted user path: '+str(p.relative_to(HERE)))
  name=str(p.relative_to(HERE)).replace('\\','/');payload.append((name,public));substitutions+=count[0]
  inventory.append({'path':name,'original_bytes':len(original),'original_sha256':hashlib.sha256(original).hexdigest(),'public_bytes':len(public),'public_sha256':hashlib.sha256(public).hexdigest(),'user_home_replacements':count[0]})
 write(HERE/'raw_evidence_inventory.json',inventory)
 policy={'rule':'Parse JSON/JSONL, recursively replace current Windows user-home prefix (backslash or slash spelling) by <USER_HOME>; serialize UTF-8. No task/response/reward/tool scientific values otherwise changed. Original files retained byte-for-byte.','replacements':substitutions,'credential_scan':'No Authorization/Bearer/access_token/refresh_token/api_key/apiKey patterns; archive construction fails closed if any present.','absolute_user_path_scan':'No drive:/Users path in public copies; fails closed.','originals_retained':True}
 write(HERE/'PUBLIC_REDACTION.json',policy)
 target=HERE/'raw-evidence-public.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in payload:z.writestr(name,data)
  for name in ['raw_evidence_inventory.json','PUBLIC_REDACTION.json']:z.write(HERE/name,name)
 write(HERE/'raw_archive.json',{'path':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'file_count':len(paths),'below_100MiB':target.stat().st_size<100*1024**2,'originals_retained':True,'public_redacted_copy':True})
 print(read(HERE/'raw_archive.json'))
if __name__=='__main__':main()
