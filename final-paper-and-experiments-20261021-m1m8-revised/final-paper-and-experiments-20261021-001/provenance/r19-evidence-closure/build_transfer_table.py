"""Generate paired-transfer/cost table from saved predictions and TLS captures."""
from pathlib import Path
import json,hashlib,sys,random
from collections import Counter
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';E=P/'experiments';D=E/'sp2027-r14-transfer-boundaries'
read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
rows=read(D/'full_suite_results.json');paired=read(D/'paired_transfer_intervals.json')
names={'sp2027-r11-minimax':'MiniMax','sp2027-r12-glm':'GLM'}
out=[];inputs={}
def scheduled_count(e,cal):
 # Independently execute only the frozen scheduler's count/RNG logic.
 # No tool invocation, network capture, or model request is performed.
 rng=random.Random(20261021+e['task']*100003+e['repeat']*7919+(e['prompt']=='rules')*13)
 seen=Counter();emitted=Counter();pools={v:[d for d in ds if d['user']!=e['user']] for v,ds in cal['donors'].items()}
 def deficits():return {v:n-seen[v]-emitted[v] for v,n in cal['template'].items() if n>seen[v]+emitted[v]}
 def add(v):
  if pools.get(v):rng.choice(pools[v]);emitted[v]+=1
 for c in e['calls']:
  df=deficits()
  if df and rng.random()<cal['shape_emit_probability']:add(rng.choices(list(df),weights=list(df.values()))[0])
  seen[c['name']]+=1
 rest=[v for v,n in deficits().items() for _ in range(n)];rng.shuffle(rest)
 for v in rest:add(v)
 return len(e['calls'])+sum(emitted.values())
for target in names:
 ids=set(read(E/target/'formal_plan.json')['test'])
 raw=[s for s in read(E/target/'network_sessions.json') if s['condition']=='raw' and s['task'] in ids]
 assert len(raw)==46
 assert all(sum(d=='c2s' for d,n in r['records'])==len(r['calls']) for r in raw)
 episodes={e['task']:e for f in (E/target/'formal').glob('*/task-*/episode.json') if (e:=read(f))['task'] in ids}
 assert len(episodes)==46
 rawcalls=sum(len(s['calls']) for s in raw);rawbytes=sum(s['application_wire_bytes'] for s in raw)
 for source,condition in [(target,'transferred_joint'),(next(n for n in names if n!=target),'transferred_joint'),(target,'write_only_padding')]:
  captures=[]
  for f in (D/'transfer_captures'/source/target/condition).glob('*.json'):
   s=read(f)
   if s['task'] in ids:captures.append(s);inputs[f.relative_to(P).as_posix()]=sha(f)
  assert len(captures)==46
  cal=read(E/source/'network_calibration.json')
  for s in captures:
   expected=scheduled_count(episodes[s['task']],cal) if condition=='transferred_joint' else len(episodes[s['task']]['calls'])
   assert expected==sum(d=='c2s' for d,n in s['records']),(target,source,condition,s['task'])
  calls=sum(sum(d=='c2s' for d,n in s['records']) for s in captures)
  wire=sum(s['application_wire_bytes'] for s in captures)
  r={'target':target,'source':source,'condition':condition,'test_tasks':46,'test_calls':calls,'raw_test_calls':rawcalls,'call_ratio':calls/rawcalls,'test_bytes':wire,'raw_test_bytes':rawbytes,'byte_ratio':wire/rawbytes}
  for label in ['cancel','return']:
   v=next(x for x in rows if (x['study'],x['source'],x['target'],x['condition'],x['label'])==('calibration_transfer',source,target,condition,label))
   assert abs(v['bytes_ratio']-wire/rawbytes)<1e-12
   r[label]={'ba':v['suite_ba'],'ci95':v['ci95']}
   if source!=target or condition=='write_only_padding':r[label]['paired']=next(x for x in paired if (x['target'],x['source'],x['condition'],x['label'])==(target,source,condition,label))
  out.append(r)
t=[r'\begin{table*}[t]\centering\footnotesize',r'\caption{Calibration transfer and write-only padding on each target model\textquotesingle s 46 test tasks (24 customers). BA is the endpoint-suite maximum; paired $\Delta$ is relative to target-local joint shaping (percentage points). Costs divide summed test bytes/calls by undefended target-model totals.}\label{tab:calibration-transfer}',r'\begin{tabularx}{\textwidth}{@{}llrrYYrr@{}}\toprule',r'Target & Calibration / intervention & Cancel BA & Return BA & $\Delta$ cancel [95\% CI] & $\Delta$ return [95\% CI] & Bytes$\times$ & Calls$\times$\\\midrule']
for r in out:
 label=names[r['source']]+' joint' if r['condition']=='transferred_joint' else 'Write padding'
 def delta(k):
  if 'paired' not in r[k]:return '--'
  d=r[k]['paired'];return f"${d['difference']*100:+.1f}$ [{d['ci95'][0]*100:.1f}, {d['ci95'][1]*100:.1f}]"
 t.append(f"{names[r['target']]} & {label} & {r['cancel']['ba']*100:.1f} & {r['return']['ba']*100:.1f} & {delta('cancel')} & {delta('return')} & {r['byte_ratio']:.2f} & {r['call_ratio']:.2f}"+r'\\')
t += [r'\bottomrule\end{tabularx}',r'\par\smallskip\raggedright The seven attacks include protected refits, decoded-tool, target-call-count and total-exchange-count rules. Nominal intervals reselect both maxima on 2,000 common customer draws, conditional on the fitted attackers. Each source calibration uses only source training data; target attackers use target training data. Write padding executes no cover calls. These are local TLS replays of fixed model trajectories; no live planner latency or utility is inferred from these costs.',r'\end{table*}']
outputs={M/'tables/r14-calibration-transfer.tex':'\n'.join(t)+'\n',O/'transfer-costs.json':json.dumps({'rows':out,'capture_hashes':inputs,'method':'One request TLS record per call in these captures; validated against raw session call arrays. Byte ratios are sums of application wire bytes, including TLS record headers.','sources':{p.name:sha(p) for p in [D/'full_suite_results.json',D/'paired_transfer_intervals.json']}},indent=2)+'\n'}
for f,s in outputs.items():
 if '--check' in sys.argv:assert f.read_text()==s,str(f)
 else:f.write_text(s,encoding='utf8',newline='\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['cancel','return']} for r in out]))
