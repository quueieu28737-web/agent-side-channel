from common import *
from collect_formal import episode,InfrastructureError
from concurrent.futures import ThreadPoolExecutor
import time,datetime,traceback
jobs=[(t,a) for t in read(HERE/'protocol.json')['sample'] for a in (['baseline','joint'] if t%2==0 else ['joint','baseline'])]
def count():return len(list((HERE/'formal').glob('*/task-*/episode.json')))
def status(s,**kw):write(HERE/'status.json',dict(state=s,completed=count(),target=100,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**kw))
failures=0
while True:
 before=count();status('running',no_progress_failures=failures)
 try:
  with ThreadPoolExecutor(max_workers=10) as pool:
   for row in pool.map(lambda j:episode(j[0],0,j[1],HERE/'formal'),jobs):status('running')
  status('complete_pending_analysis');break
 except InfrastructureError as e:
  failures=failures+1 if count()==before else 0
  status('blocked' if failures>=3 else 'backoff',error=str(e),no_progress_failures=failures)
  if failures>=3:break
  time.sleep(60)
