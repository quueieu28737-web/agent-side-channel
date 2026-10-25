from pathlib import Path
import sys,json,tempfile,datetime
from concurrent.futures import ThreadPoolExecutor
D=Path(__file__).resolve().parent;E=D.parent
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import network_replay as nr
import evaluate_network as en
names=['sp2027-r11-minimax','sp2027-r12-glm']
ns,tools,base,tasks=nr.load()
plan={'scope':'Post hoc calibration transfer and write-only padding; model trajectories unchanged. Attacker refit on target model training clients under each transferred defense; source calibration never uses target test clients.','sources':{n:nr.sha(E/n/'network_calibration.json') for n in names},'conditions':['transferred_joint','write_only_padding'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
nr.write(D/'calibration_transfer_plan.json',plan)
with tempfile.TemporaryDirectory() as tmp:
 contexts=nr.tlslab.make_contexts(Path(tmp),'1.2')
 jobs=[]
 for target in names:
  episodes=[nr.read(p) for p in (E/target/'formal').glob('*/task-*/episode.json')]
  for source in names:
   jobs.extend((source,target,e,'transferred_joint') for e in episodes)
  jobs.extend((target,target,e,'write_only_padding') for e in episodes)
 def run(job):
  source,target,e,condition=job
  dest=D/'transfer_captures'/source/target/condition/f"task-{e['task']:03d}.json"
  if dest.exists():return
  cal=nr.read(E/source/'network_calibration.json')
  if condition=='transferred_joint':calls,flags=nr.cover_episode(e,cal,tools,base)
  else:calls=e['calls'];flags={}
  ex=[]
  for c in calls:
   mode='const' if condition=='transferred_joint' or c['name'] in en.ev.WRITES else 'raw'
   ex.append((nr.frame(c['req_text'],mode,True,cal['caps']),nr.frame(c['resp_text'],mode,False,cal['caps'])))
  seq=nr.tlslab.run_session(*contexts,ex)
  row={k:e[k] for k in ['task','user','has_cancel','has_return','repeat','seed','prompt']}
  row.update(source=source,target=target,condition=condition,records=seq,flags=flags,application_wire_bytes=sum(n+5 for d,n in seq),calibration_sha256=nr.sha(E/source/'network_calibration.json'))
  nr.write(dest,row)
 with ThreadPoolExecutor(max_workers=2) as pool:
  for i,_ in enumerate(pool.map(run,jobs)):
   if i%50==0:print('CAPTURE',i,'/',len(jobs),flush=True)
nr.write(D/'capture_status.json',{'state':'complete','sessions':len(jobs)})
