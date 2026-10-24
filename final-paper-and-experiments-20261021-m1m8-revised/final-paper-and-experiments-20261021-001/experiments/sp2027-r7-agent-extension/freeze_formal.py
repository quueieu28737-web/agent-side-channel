from common import *
import datetime
s=read(HERE/'split.json');train=[x for x in s['train'] if x not in [0,1,2,3,4]][:29];test=s['test'];ids=train+test
ns,tools,base,tasks=load()
plan={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':MODEL,'effort':'low','domain':'existing-public-retail','runs':150,'task_count':75,'train':train,'test':test,'prompts':PROMPTS,'repeats':[0],'workers':2,'per_call_timeout_seconds':180,'no_result_stop':3,'pilot_included':False,'new_customers':False,'selection':'All 46 inherited test tasks plus first 29 inherited training tasks excluding pilot 0..4; fixed before formal collection','prior_exposure':'All 115 public tasks previously used in development; neither unseen environment nor independent human validation. Same provider second model. Different cohort from Sol prevents direct causal model comparison.','train_only_calibration':True,'tasks':[{'task':i,'customer':tasks[i].user_id,'label':s['labels'][i],'partition':'train' if i in train else 'test'} for i in ids],'files':{n:sha(HERE/n) for n in ['common.py','collect_formal.py','rpc_backend.py','action.schema.json','model_instructions.txt','split.json','protocol.json']}}
for part,ls in [('train',train),('test',test)]:
 plan[part+'_counts']={'tasks':len(ls),'customers':len(set(tasks[i].user_id for i in ls)),'cancel_positive_tasks':sum(bool(s['labels'][i]&1) for i in ls),'return_positive_tasks':sum(bool(s['labels'][i]&2) for i in ls)}
assert len(ids)==75 and len(set(ids))==75
assert not set(tasks[i].user_id for i in train)&set(tasks[i].user_id for i in test)
write(HERE/'formal_plan.json',plan);print(json.dumps({k:v for k,v in plan.items() if k in ['train_counts','test_counts','runs']}))
