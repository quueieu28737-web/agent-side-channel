import time,json,random,sys
from pathlib import Path
from collections import Counter
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent/'sp2027-r12-glm'))
from network_replay import invoke,old
class Controller:
 def __init__(self,tid,arm,tools,base):
  self.tid=tid;self.arm=arm;self.tools=tools;self.shadow=old.fast_clone(base);self.cal=json.loads((D/'source_calibration.json').read_text());self.seen=Counter();self.cover=Counter();self.rows=[];self.rng=random.Random(tid)
 def response(self,name,obs):
  start=time.monotonic();self.seen[name]+=1;cover_name=None;cover_error=None
  if self.arm=='joint':
   deficits=[v for v,n in self.cal['template'].items() if self.seen[v]+self.cover[v]<n]
   if deficits:
    cover_name=self.rng.choice(sorted(deficits));donor=self.rng.choice(self.cal['donors'][cover_name]);reply=invoke(self.tools,self.shadow,cover_name,donor['kwargs']);self.cover[cover_name]+=1;cover_error=reply.startswith('Error:');time.sleep(.02)
  planned=.02+(.2 if not self.rows and self.tid%5==0 else 0);time.sleep(planned)
  elapsed=time.monotonic()-start;timeout=(planned+(.02 if cover_name else 0))>.12
  self.rows.append(dict(real_action=name,cover_action=cover_name,cover_error=cover_error,elapsed_seconds=elapsed,timeout=timeout))
  return 'Error: gateway response deadline exceeded; operation may have executed. Check state before retrying.' if timeout else obs
 def save(self,d):
  (d/'live_metrics.json').write_text(json.dumps(dict(arm=self.arm,rows=self.rows,real_calls=len(self.rows),cover_calls=sum(self.cover.values()),timeouts=sum(x['timeout'] for x in self.rows),post_timeout_actions=sum(len(self.rows)-i-1 for i,x in enumerate(self.rows) if x['timeout']),scope='Live planner with stateful isolated cover, fixed emulated delay and response deadline; no TLS/WAN security claim'),indent=2))
