"""Exact saved-call/record alignment and frozen cohort preparation. No fitting."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
H=Path(__file__).resolve().parent;E=H.parent
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x): (H/n).write_text(json.dumps(x,indent=2),encoding="utf8")
def records(c):
 out=[]
 for d,key in [("c2s","req"),("s2c","resp")]:
  n=c[key]+4
  while n:
   k=min(n,16384);out.append([d,k+24]);n-=k
 return out
paths=[E/"sp2027-r4-snapshot-20261023/sessions.json",E/"sp2027-r4-full-20261023/sessions.json"]
sessions={}
for p in paths:
 for s in read(p):
  if s["condition"]=="raw":sessions[s["prompt"],s["task"],s["repeat"]]=s
rr=[r for r in read(H/"actual_attribute_instances.json") if r["verb"]=="return_delivered_order_items" and r["single_requested_item"]]
sources={str(p.relative_to(E)):sha(p) for p in paths};out=[];checked=set()
for r in rr:
 arm,tid,rep=r["prompt"],r["task"],r["repeat"]
 rel=Path("runs")/arm/f"task-{tid:03d}-repeat-{rep}"/"episode.json"
 p=E/"sp2027-r4-snapshot-20261023"/rel
 if not p.exists():p=E/"sp2027-r4-full-20261023/delta"/rel
 e=read(p);s=sessions[arm,tid,rep];sources[str(p.relative_to(E))]=sha(p)
 assert s["episode_sha256"]==sha(p)
 assert len(s["calls"])==len(e["calls"])
 seq=[];bounds=[]
 for c,t in zip(e["calls"],s["calls"]):
  assert all(c[k]==t[k] for k in ["name","req","resp","err"])
  assert c["req"]==len(c["req_text"].encode()) and c["resp"]==len(c["resp_text"].encode())
  a=len(seq);seq+=records(c);bounds.append([a,len(seq)])
 assert seq==s["records"]
 i=r["call_index"];a,b=bounds[i];projected=s["records"][a:b]
 assert projected==records(e["calls"][i])
 out.append(dict(r,record_start=a,record_end=b,records=projected,episode_path=str(p.relative_to(E)),episode_sha256=sha(p)))
 checked.add((arm,tid,rep))
write("aligned_calls.json",out)
write("alignment.json",dict(passed=True,eligible_call_rows=len(out),unique_episodes=len(checked),method="Exact full raw-session ordered-call equality plus per-call deterministic TLS fragmentation; every concatenated record equals saved socket-replay records; slice boundaries exact. Oracle known-call projection, not unaided network boundary discovery.",source_hashes=sources,timing="No measured timing; direction and record length only."))
print("aligned",len(out),"calls from",len(checked),"episodes")
