"""Train-only calibration and online shadow cover. No model calls here."""
import argparse
import math
import random
import statistics
import tempfile
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from common import *
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r3'/'deps'))
sys.path.insert(0,str(HERE.parents[3]/'revision-preview'/'r7-agent-deps'))
REPEATS=[0]
from e6_e7_retail_cover import invoke,frame
import tlslab

CONDITIONS=['raw','padding_only','shape_only','shape_const']

def episodes(partition):
    rows=[]
    for arm in PROMPTS:
        for tid in read(HERE/'formal_plan.json')[partition]:
            for rep in REPEATS:
                p=HERE/'formal'/arm/f'task-{tid:03d}-repeat-{rep}'/'episode.json'
                if not p.exists(): raise RuntimeError('Missing required episode: '+str(p))
                row=read(p)
                assert row['inference_fingerprint']==inference_fingerprint(),'Episode version mismatch'
                assert (row['task'],row['repeat'],row['prompt'])==(tid,rep,arm)
                rows.append(row)
    return rows

def fit_calibration(rows,ns,tools,base):
    allowed=set(read(HERE/'formal_plan.json')['train'])
    assert rows and all(e['task'] in allowed for e in rows)
    tmpl=Counter();donors=defaultdict(list);lengths=[]
    for e in rows:
        counts=Counter(c['name'] for c in e['calls'] if c['name'] in tools)
        for name,n in counts.items():tmpl[name]=max(tmpl[name],n)
        for c in e['calls']:
            lengths.append((c['req'],c['resp']))
            if c['name'] in tools:
                donors[c['name']].append({'task':e['task'],'user':e['user'],'name':c['name'],'kwargs':c['kwargs']})
    # Deduplicate donors, retaining provenance. All come from training trajectories.
    donors={v:list({json.dumps(d,sort_keys=True):d for d in ds}.values()) for v,ds in sorted(donors.items())}
    for v,ds in donors.items():
        for d in ds:
            req=json.dumps({'name':v,'arguments':d['kwargs']},sort_keys=True)
            resp=invoke(tools,old.fast_clone(base),v,d['kwargs'])
            lengths.append((len(req.encode()),len(resp.encode())))
    if not lengths: raise RuntimeError('No training calls; defense cannot be calibrated')
    return {'training_tasks':sorted(allowed),'training_episodes':len(rows),
        'template':dict(sorted(tmpl.items())),'donors':donors,
        'caps':{'req':int(math.ceil((max(q for q,r in lengths)+4)/256)*256),
                'resp':int(math.ceil((np.quantile([r for q,r in lengths],.95)+4)/1024)*1024)},
        'calibration_lengths':len(lengths),'shape_emit_probability':.6,
        'split_sha256':sha(HERE/'formal_plan.json'),'protocol_sha256':sha(HERE/'protocol.json'),
        'training_episode_hashes':{str((HERE/'formal'/e['prompt']/f"task-{e['task']:03d}-repeat-{e['repeat']}"/'episode.json').relative_to(HERE)):
           sha(HERE/'formal'/e['prompt']/f"task-{e['task']:03d}-repeat-{e['repeat']}"/'episode.json') for e in rows}}

def cover_episode(e,cal,tools,base):
    rng=random.Random(20261021+e['task']*100003+e['repeat']*7919+(e['prompt']=='rules')*13)
    seen=Counter();emitted=Counter();calls=[];missing=Counter()
    pools={v:[d for d in ds if d['user']!=e['user']] for v,ds in cal['donors'].items()}
    shadow=old.fast_clone(base)
    def deficits():
        return {v:n-seen[v]-emitted[v] for v,n in cal['template'].items() if n>seen[v]+emitted[v]}
    def add(v):
        if not pools.get(v):missing[v]+=1;return
        d=rng.choice(pools[v]);resp=invoke(tools,shadow,v,d['kwargs'])
        req=json.dumps({'name':v,'arguments':d['kwargs']},sort_keys=True)
        calls.append({'name':v,'kind':'cover','req_text':req,'resp_text':resp,'req':len(req.encode()),
                      'resp':len(resp.encode()),'err':resp.startswith('Error:'),'donor_task':d['task']})
        emitted[v]+=1
    for c in e['calls']:
        df=deficits()
        if df and rng.random()<cal['shape_emit_probability']:
            add(rng.choices(list(df),weights=list(df.values()))[0])
        seen[c['name']]+=1;calls.append(dict(c,kind='real'))
    rest=[v for v,n in deficits().items() for _ in range(n)]
    rng.shuffle(rest)
    for v in rest:add(v)
    counts=Counter(c['name'] for c in calls)
    return calls,{'template_overflow':any(counts[v]>cal['template'].get(v,0) for v in counts),
                  'template_underfill':any(counts[v]<n for v,n in cal['template'].items()),
                  'missing_donor_attempts':dict(missing)}

def capture(e,cal,tools,base,contexts,dest):
    result=[];shape,flags=cover_episode(e,cal,tools,base)
    for cond in CONDITIONS:
        path=dest/e['prompt']/f"task-{e['task']:03d}-repeat-{e['repeat']}-{cond}.json"
        if path.exists():
            r=read(path);assert r['calibration_sha256']==sha(HERE/'network_calibration.json')
            assert r['episode_sha256']==sha(HERE/'formal'/e['prompt']/f"task-{e['task']:03d}-repeat-{e['repeat']}"/'episode.json')
            result.append(r);continue
        calls=shape if cond.startswith('shape') else [dict(c,kind='real') for c in e['calls']]
        fr='const' if cond in ('padding_only','shape_const') else 'raw'
        ex=[(frame(c['req_text'],fr,True,cal['caps']),frame(c['resp_text'],fr,False,cal['caps'])) for c in calls]
        seq=tlslab.run_session(*contexts,ex)
        # Request messages in this benchmark are shorter than a TLS fragment.
        assert sum(d=='c2s' for d,n in seq)==len(calls)
        overflow=sum(c['req']+4>cal['caps']['req'] or c['resp']+4>cal['caps']['resp'] for c in calls)
        r={k:e[k] for k in ('task','repeat','seed','prompt','user','has_cancel','has_return','native_reward','db_eq','status')}
        r.update({'condition':cond,'calls':[{k:c[k] for k in ('name','kind','req','resp','err')}|
             ({'donor_task':c['donor_task']} if 'donor_task' in c else {}) for c in calls],
            'records':seq,'application_wire_bytes':sum(n+5 for d,n in seq),
            'framing_overflow_messages':overflow if fr=='const' else 0,
            'template_flags':flags if cond.startswith('shape') else None,
            'calibration_sha256':sha(HERE/'network_calibration.json'),
            'episode_sha256':sha(HERE/'formal'/e['prompt']/f"task-{e['task']:03d}-repeat-{e['repeat']}"/'episode.json'),
            'measurement':'TLS 1.2 loopback replay of real model trajectory; provider link and wall-clock timing excluded'})
        write(path,r);result.append(r)
    return result

def validate_calibration():
    cal=read(HERE/'network_calibration.json')
    assert cal['split_sha256']==sha(HERE/'formal_plan.json')
    assert cal['protocol_sha256']==sha(HERE/'protocol.json')
    assert cal['training_tasks']==read(HERE/'formal_plan.json')['train']
    expected={str((HERE/'formal'/arm/f'task-{tid:03d}-repeat-{rep}'/'episode.json').relative_to(HERE))
              for tid in cal['training_tasks'] for arm in PROMPTS for rep in REPEATS}
    assert set(cal['training_episode_hashes'])==expected
    for name,digest in cal['training_episode_hashes'].items():assert sha(HERE/name)==digest
    return cal

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['calibrate','capture']);ap.add_argument('--workers',type=int,default=8)
    a=ap.parse_args();ns,tools,base,tasks=load()
    if a.action=='calibrate':
        cal=fit_calibration(episodes('train'),ns,tools,base)
        if (HERE/'network_calibration.json').exists():assert read(HERE/'network_calibration.json')==cal,'Frozen calibration changed'
        else:write(HERE/'network_calibration.json',cal)
        print(json.dumps({k:cal[k] for k in ('training_episodes','template','caps','calibration_lengths')}));return
    cal=validate_calibration();rows=episodes('train')+episodes('test');out=[]
    with tempfile.TemporaryDirectory(prefix='luna-tls-') as tmp:
        contexts=tlslab.make_contexts(Path(tmp),'1.2')
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            fs=[pool.submit(capture,e,cal,tools,base,contexts,HERE/'network_captures') for e in rows]
            for i,f in enumerate(as_completed(fs)):
                out.extend(f.result())
                if (i+1)%25==0:print('captured episodes',i+1,'/',len(rows),flush=True)
    out.sort(key=lambda e:(e['prompt'],e['task'],e['repeat'],e['condition']))
    write(HERE/'network_sessions.json',out);print('TLS_CAPTURES',len(out),flush=True)

if __name__=='__main__':main()

