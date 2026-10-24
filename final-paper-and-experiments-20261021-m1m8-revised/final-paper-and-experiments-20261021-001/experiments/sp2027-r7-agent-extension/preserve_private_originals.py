from common import *
import datetime,re,shutil
private=HERE.parents[3]/'revision-preview'/'r7-agent-originals-20261024'
rows=read(HERE/'raw_evidence_inventory.json')
for r in rows:assert sha(private/r['path'])==r['original_sha256'],r['path']
assert all(not (HERE/n).exists() for n in ['connectivity','pilot','formal'])
write(HERE/'private_originals_location.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'outside_publication_package':True,'workspace_relative_location':'revision-preview/r7-agent-originals-20261024','directories':['connectivity','pilot','formal'],'original_files_hash_checked':len(rows),'all_original_sha256_match_inventory':True,'inventory_sha256':sha(HERE/'raw_evidence_inventory.json'),'compact_manifest_sha256_unchanged':sha(HERE/'compact_manifest.json')})
# Original process logs are retained outside the package; publication copies only replace HOME prefixes.
logdir=private/'process-logs';logdir.mkdir(exist_ok=True);record=[]
for name in ['network_process_log.json','public_validation_process.json']:
 p=HERE/name;original=p.read_bytes();dest=logdir/name;assert not dest.exists();shutil.move(str(p),str(dest));count=[0]
 def clean(obj):
  if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items()}
  if isinstance(obj,list):return [clean(v) for v in obj]
  if isinstance(obj,str):
   s,n=re.subn(r'(?i)[a-z]:[\\/]+Users[\\/]+[^\\/:"<>|\r\n]+','<USER_HOME>',obj);count[0]+=n;return s
  return obj
 write(p,clean(json.loads(original.decode('utf-8-sig'))))
 record.append({'path':name,'original_sha256':hashlib.sha256(original).hexdigest(),'public_sha256':sha(p),'HOME_prefix_replacements':count[0]})
write(HERE/'PROCESS_LOG_REDACTION.json',{'rule':'Publication copies replace Windows HOME prefixes only; original process logs retained byte-for-byte outside publication package alongside original model evidence. Scientific values and return codes unchanged.','logs':record})
print(read(HERE/'private_originals_location.json'))
