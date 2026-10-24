from common import *
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r3'/'deps'))
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r7-agent-deps'))
import datetime,importlib.metadata
names=['numpy','scikit-learn','scipy','joblib','threadpoolctl','cloudpickle','cryptography']
write(HERE/'dependency_versions.json',{'python':sys.version,'packages':{n:importlib.metadata.version(n) for n in names}})
files=['evaluate_d2.py','network_replay.py','evaluate_network.py','D2_analysis_plan.json','NETWORK_ANALYSIS_PLAN.json','verify_formal.py','verify_public.py','package_raw.py','run_formal.py','summarize.py','REPRODUCE.md','dependency_versions.json']
external=[EXP/'sp2027-r2'/'e67_eval.py',EXP/'sp2027-r2'/'e6_e7_retail_cover.py',EXP/'sp2027-r2'/'tlslab.py',EXP/'sp2027-r3'/'reanalyze.py']
write(HERE/'APPENDED_ANALYSIS_FREEZE.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'appended analysis, separate from formal collection freeze; no test outputs available at freeze','formal_plan_sha256':sha(HERE/'formal_plan.json'),'collection_status_at_freeze':read(HERE/'formal_status.json'),'training_trajectories':58,'test_trajectories':92,'additional_LLM_requests':0,'files':{n:sha(HERE/n) for n in files},'inherited_helpers':{str(p.relative_to(EXP)).replace('\\','/'):sha(p) for p in external}})
print(read(HERE/'dependency_versions.json'));print(read(HERE/'formal_status.json'))
