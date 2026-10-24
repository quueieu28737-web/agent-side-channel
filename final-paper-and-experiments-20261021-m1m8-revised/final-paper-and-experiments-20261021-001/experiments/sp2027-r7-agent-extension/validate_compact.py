from common import *
import zipfile,datetime
m=read(HERE/'compact_manifest.json')
for n,h in m['artifacts'].items():assert sha(HERE/n)==h,n
for n,row in m['benchmark_dependency_authority'].items():assert sha(HERE.parents[1]/row['path'])==row['sha256'],n
p=read(HERE/'formal_plan.json')
for n,h in p['files'].items():assert sha(HERE/n)==h,n
f=read(HERE/'APPENDED_ANALYSIS_FREEZE.json')
for n,h in f['files'].items():assert sha(HERE/n)==h,n
for n in ['formal_validation_corrected.json','public_validation_corrected.json','public_network_validation.json','public_d2_validation.json','decision_alignment.json','public_decision_alignment.json']:assert read(HERE/n)['complete'],n
assert m['formal_runs']==150 and len(m['D2_dispatch_suite'])==12 and len(m['network_suite'])==16
assert sum(r['model_calls'] for r in m['per_prompt'].values())==3072
assert sum(r['real_tool_calls'] for r in m['per_prompt'].values())==1003
assert sum(r['tool_dispatch_attempts'] for r in m['per_prompt'].values())==1015
assert sum(r['unknown_tool_attempts'] for r in m['per_prompt'].values())==12
assert read(HERE/'public_d2_validation.json')['suite_cells_matched']==12
assert read(HERE/'public_network_validation.json')['recomputed_results']==32
archive=read(HERE/'raw_archive.json');assert sha(HERE/archive['path'])==archive['sha256'] and archive['bytes']<100*1024**2
with zipfile.ZipFile(HERE/archive['path']) as z:assert z.testzip() is None
write(HERE/'compact_validation.json',{'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'formal_runs':150,'compact_manifest_sha256':sha(HERE/'compact_manifest.json'),'artifact_hashes_checked':len(m['artifacts']),'formal_and_original_appended_sources_unchanged':True,'public_native_reward_recomputed_runs':150,'public_decision_aligned_model_calls':3072,'public_D2_suite_cells':12,'public_network_suite_cells':32,'known_name_dispatch_attempts':1003,'total_dispatch_attempts':1015,'unknown_attempts':12,'public_zip_crc_checked':True,'public_zip_sha256':archive['sha256'],'public_zip_bytes':archive['bytes'],'public_zip_self_contained':False})
print(read(HERE/'compact_validation.json'))
