"""Explicit offline RPC adaptations; no new packet timing measurements.

WF outputs carry 512 plaintext bytes + 24 AEAD bytes + 5 TLS header bytes.
Every real fragment is tracked privately for integrity, never given to learners.
Sources and differences: PROTOCOL.md and IMPLEMENTATION.md.
"""
import math
from collections import defaultdict
from r7common import *

def cells(records):
    out=[];start=records[0][2] if records else 0
    for d,n,t in records:
        assert n>24
        for _ in range(math.ceil((n-24)/512)):
            out.append([int(d),536,(t-start)/1e9,len(out)])
    return out

def fit(train):
    raw=[r for r in train if r['condition']=='raw']; counts=[];dur=[];iat=[];means=defaultdict(list)
    for r in raw:
        c=cells(r['records']);counts.append(len(c));dur.append(max(c[-1][2],1e-6) if c else 1e-6)
        means[r['user']].append(len(c))
        for sign in (1,-1):
            ts=np.array([x[2] for x in c if x[0]==sign]);iat.extend(np.diff(ts)[np.diff(ts)>0])
    threshold=float(np.median([np.mean(v) for v in means.values()]))
    short=sorted(u for u,v in means.items() if np.mean(v)<=threshold)
    sr=[r for r in raw if r['user'] in short];sc=[len(cells(r['records'])) for r in sr]
    sd=[max((r['records'][-1][2]-r['records'][0][2])/1e9,1e-6) for r in sr]
    def front(cs,ds):return {'budget':max(1,int(np.median(cs))), 'window':[max(1e-6,float(np.quantile(ds,q))) for q in (.25,.75)]}
    edges=np.geomspace(max(min(iat),1e-6),max(max(iat),1e-5)*1.01,17)
    hist=np.histogram(iat,edges)[0].astype(int)+1
    donors=[]
    for r in raw:
        b=[]
        for d,_,_,_ in cells(r['records']):
            if b and b[-1][0]==d:b[-1][1]+=1
            else:b.append([d,1])
        donors.append({'user':r['user'],'bursts':b})
    return {'front':front(counts,dur),'front_shift':front(sc,sd),'short_customers':short,
            'all_train_customers':sorted(means),'iat_edges':edges.tolist(),'iat_tokens':hist.tolist(),
            'donors':donors,'cell_payload':512,'wf_tls_ciphertext':536,'tamaraw_padL':50,
            'wt_cell_spacing':max(1e-6,float(np.median(iat))/8),'short_customer_mean_cell_threshold':threshold}

def tamaraw(c,rng,fast=False):
    if not c:return [],0.
    periods={1:.004 if fast else .04,-1:.0012 if fast else .012}
    clock={1:periods[1],-1:periods[-1]};out=[];i=0;shift=0.;last=0.
    while i<len(c):
        d=min(clock,key=lambda k:(clock[k],-k));t=clock[d];clock[d]+=periods[d]
        if c[i][0]==d and c[i][2]+shift<=t+1e-12:
            out.append([d,536,t,c[i][3]]);shift=max(shift,t-c[i][2]);last=t;i+=1
        else:out.append([d,536,t,-1])
        assert len(out)<200000,'Unexpected queue expansion'
    for d in (1,-1):
        n=sum(x[0]==d for x in out);target=(n//50+int(rng.geometric(.5)))*50
        for _ in range(target-n):out.append([d,536,clock[d],-1]);clock[d]+=periods[d]
    return sorted(out,key=lambda x:x[2]),last

def front(c,rng,cfg):
    out=[x[:] for x in c]
    if not c:return out,0.
    end=c[-1][2]
    for d in (1,-1):
        w=rng.uniform(*cfg['window']);n=int(rng.integers(1,cfg['budget']+1))
        out.extend([d,536,float(t),-1] for t in rng.rayleigh(w,n) if t<end)
    return sorted(out,key=lambda x:x[2]),end

def wtfpad(c,rng,cal):
    # Finite-trace send/receive-triggered AP. State is per direction.
    # Infinity returns to WAIT; finite BURST timeout enters GAP; real traffic resets BURST.
    # Fresh histograms per session prevent order-dependent train/test state leakage.
    out=[x[:] for x in c];edges=np.array(cal['iat_edges']);original=np.array(cal['iat_tokens'])
    tokens={d:original.copy() for d in (1,-1)};state={1:'BURST',-1:'BURST'};budget=0
    for i,p in enumerate(c[:-1]):
        t=p[2];end=c[i+1][2];state[p[0]]='BURST'
        for d in (p[0],-p[0]):
            x=t;steps=0
            while state[d]!='WAIT' and x<end and steps<64:
                # BURST: infinity prob .1; GAP: geometric mean 4 dummy cells.
                inf=.1 if state[d]=='BURST' else .25
                if rng.random()<inf:state[d]='WAIT';break
                tok=tokens[d]
                if not tok.sum():tok[:]=original
                j=int(rng.choice(len(tok),p=tok/tok.sum()))
                wait=float(rng.uniform(edges[j],edges[j+1]));tok[j]-=1
                if x+wait>=end:break
                x+=wait;out.append([d,536,x,-1]);state[d]='GAP';steps+=1
            if steps==64:budget+=1
    return sorted(out,key=lambda x:x[2]),(c[-1][2] if c else 0.),budget

def walkie(c,rng,cal,user):
    pool=[d for d in cal['donors'] if d['user']!=user];donor=pool[int(rng.integers(len(pool)))]['bursts']
    # Align by directional turns, preserving all true packets. Real trace is already
    # sequential RPC half duplex; no hypothetical browser modification is evaluated.
    bursts=[]
    for p in c:
        if bursts and bursts[-1][0]==p[0]:bursts[-1][1].append(p)
        else:bursts.append([p[0],[p]])
    out=[];time=0.;shift=0.;last=0.;j=0;delta=cal['wt_cell_spacing']
    for d,ps in bursts:
        if j<len(donor) and donor[j][0]!=d:
            for _ in range(donor[j][1]):time+=delta;out.append([donor[j][0],536,time,-1])
            j+=1
        count=max(len(ps),donor[j][1] if j<len(donor) else 0);j+=1
        for p in ps:
            time=max(time+delta,p[2]+shift);shift=max(shift,time-p[2]);out.append([d,536,time,p[3]]);last=time
        for _ in range(count-len(ps)):time+=delta;out.append([d,536,time,-1])
    for d,n in donor[j:]:
        for _ in range(n):time+=delta;out.append([d,536,time,-1])
    return out,last

def transform(r,cond,cal):
    out={k:r[k] for k in ('task','prompt','repeat','user','has_cancel','has_return','native_reward')}
    c=cells(r['records']);rng=np.random.default_rng(seed(r,cond));cap=0
    if cond=='bucket1024':
        rec=[[d,math.ceil((n-24)/1024)*1024+24,t-r['records'][0][2]] for d,n,t in r['records']]
        last=(rec[-1][2]/1e9 if rec else 0.);nreal=len(c);nkept=nreal
    else:
        if cond.startswith('tamaraw'):a,last=tamaraw(c,rng,cond.endswith('fast'))
        elif cond.startswith('front'):a,last=front(c,rng,cal[cond])
        elif cond=='wtfpad':a,last,cap=wtfpad(c,rng,cal)
        elif cond=='walkie_talkie':a,last=walkie(c,rng,cal,r['user'])
        else:raise ValueError(cond)
        kept=[p[3] for p in a if p[3]>=0]
        assert kept==list(range(len(c))),'Dropped or reordered real payload'
        assert all(p[2]+1e-12>=c[p[3]][2] for p in a if p[3]>=0),'Real packet sent before available'
        rec=[[d,n,int(round(t*1e9))] for d,n,t,idx in a];nreal=len(c);nkept=len(kept)
    out.update(condition=cond,records=rec,wire_bytes=sum(n+5 for d,n,t in rec),
        calls=r['real_calls_expected'],last_real_ms=last*1000,traffic_ms=rec[-1][2]/1e6 if rec else 0.,
        evidence='offline_trace_transform',integrity={'real_fragments':nreal,'kept':nkept,'ap_gap_caps':cap})
    return out

def measured(r):
    o={k:r[k] for k in ('task','prompt','repeat','user','has_cancel','has_return','native_reward','condition','records','wire_bytes')}
    o.update(calls=len(r['requests']),last_real_ms=r['marks']['last_real_ns']/1e6,
             traffic_ms=r['finish_ns']/1e6,evidence='measured_E13',integrity={'db_equal':r['db_equal'],'response_equal':r['response_equal']})
    return o
