"""Attacker inputs use only observed TLS record direction, size and arrival time."""
import numpy as np

def exchanges(records):
    out=[]
    for d,n,t in records:
        if d==1:out.append([n,0])
        elif out:out[-1][1]+=n
    return out

def summary(out, prefix, a):
    a = np.asarray(a, dtype=float)
    if not len(a):
        a = np.array([0.])
    for k,v in zip(('min','q25','median','q75','q95','max'), np.quantile(a,[0,.25,.5,.75,.95,1])):
        out[prefix+k] = float(v)
    out[prefix+'mean'] = float(a.mean())
    out[prefix+'std'] = float(a.std())

def features(records, view):
    r = np.asarray(records, dtype=float).reshape(-1,3)
    out = {'count':len(r)}
    if not len(r):
        return out
    d,n,t=r.T; t=(t-t[0])/1e6
    gaps=np.diff(t,prepend=0)
    size=view in ('size_order','joint','flush_stripped_joint')
    timing=view in ('timing_direction','joint','flush_stripped_joint')
    out['direction_changes']=float(np.sum(np.diff(d)!=0))
    for sign,label in ((1,'up'),(-1,'down')):
        mask=d==sign; out[label+'_count']=int(mask.sum())
        if size:
            summary(out,label+'_size_',n[mask]);out[label+'_bytes']=float(n[mask].sum())
        if timing:
            summary(out,label+'_gap_',np.diff(t[mask]));
    if size:
        summary(out,'size_',n)
        out['total_bytes']=float(n.sum())
        # Preserve the strong legacy network view: coarse request/response
        # histograms and exchange lengths. Leading tunnel downlink cells are
        # represented by directional summaries, not assigned to a fictional RPC.
        ex=exchanges(records)
        for i,v in enumerate(np.histogram(n[d==1],bins=96,range=(0,1536))[0]):out[f'req_hist_{i}']=int(v)
        for i,v in enumerate(np.histogram(np.log2(np.array([b for a,b in ex])+1),bins=22,range=(4,15))[0]):out[f'resp_hist_{i}']=int(v)
        for i,(a,b) in enumerate(ex[:24]):out[f'exchange_{i}_req']=a;out[f'exchange_{i}_resp']=b
    if timing:
        out['duration_ms']=float(t[-1]); summary(out,'gap_',gaps[1:])
        for threshold in (.1,1,5,20):
            out[f'burst_gap_le_{threshold}']=float(np.mean(gaps[1:]<=threshold)) if len(r)>1 else 0.
        idx=int(np.argmax(gaps));out['max_gap_position']=idx/len(r)
        out['prefix_records']=idx;out['suffix_records']=len(r)-idx
        summary(out,'prefix_gap_',gaps[:idx]);summary(out,'suffix_gap_',gaps[idx+1:])
        # Largest-gap change-point attacker does not use the true flush boundary.
        if size:
            summary(out,'prefix_size_',n[:idx]);summary(out,'suffix_size_',n[idx:])
    for label,indices in (('first',range(min(32,len(r)))),('last',range(max(0,len(r)-32),len(r)))):
        for pos,i in enumerate(indices):
            out[f'{label}_{pos}_dir']=float(d[i])
            if size:out[f'{label}_{pos}_size']=float(n[i])
            if timing:out[f'{label}_{pos}_gap']=float(gaps[i])
    return out

def local_features(records):
    """Offline full-trace record detector; no execution annotations are features."""
    r=np.asarray(records,dtype=float).reshape(-1,3)
    if not len(r):return []
    d,n,t=r.T;t=(t-t[0])/1e6
    gaps=np.diff(t,prepend=0);duration=max(t[-1],1e-9)
    out=[]
    for i in range(len(r)):
        f={'position':i/len(r),'count':len(r),'time_fraction':float(t[i]/duration),
           'remaining_ms':float(t[-1]-t[i]),'elapsed_ms':float(t[i])}
        for j in range(-4,5):
            k=i+j
            if 0<=k<len(r):
                f[f'd{j}']=float(d[k]);f[f'n{j}']=float(n[k]);f[f'gap{j}']=float(gaps[k])
        out.append(f)
    return out

def cutpoint(probabilities):
    """Maximum-likelihood single transition from pre-flush to flush."""
    p=np.clip(probabilities,1e-5,1-1e-5)
    left=np.r_[0,np.cumsum(np.log1p(-p))]
    right=np.r_[np.cumsum(np.log(p)[::-1])[::-1],0]
    return int(np.argmax(left+right))
