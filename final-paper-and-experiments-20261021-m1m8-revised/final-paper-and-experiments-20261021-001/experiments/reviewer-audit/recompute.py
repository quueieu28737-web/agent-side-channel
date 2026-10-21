"""Offline reviewer corrections; no model APIs or production services.
Run with Python + numpy + cryptography + pydantic. Raw observations are retained.
TLS costs are application-record wire bytes, excluding handshakes/TCP/IP.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, json, hashlib, argparse
import numpy as np
import retail_replay as old

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2),encoding='utf-8')

def metrics(rows,pred,scores=None):
    y=np.array([r['real_has_cancel'] for r in rows]); pred=np.array(pred)
    ids=sorted(set(r['task_id'] for r in rows)); ts=[]; labels=[]
    for tid in ids:
        ix=np.array([i for i,r in enumerate(rows) if r['task_id']==tid])
        labels.append(int(y[ix[0]])); ts.append(float(np.mean(pred[ix]==y[ix])))
    ts=np.array(ts); labels=np.array(labels)
    rng=np.random.default_rng(20261021)
    draws=rng.integers(0,len(ts),(10000,len(ts)))
    acc_ci=np.quantile(ts[draws].mean(axis=1),[.025,.975]).tolist()
    # Stratify by true task label; seeds remain within their task.
    strata=[ts[labels==c] for c in [0,1]]
    bd=[s[rng.integers(0,len(s),(10000,len(s)))].mean(axis=1) for s in strata]
    ba_ci=np.quantile((bd[0]+bd[1])/2,[.025,.975]).tolist()
    cm=[[int(np.sum((y==a)&(pred==b))) for b in [0,1]] for a in [0,1]]
    result={'accuracy':float(np.mean(ts)),'acc_ci95':acc_ci,
            'balanced_accuracy':float(np.mean([s.mean() for s in strata])),
            'ba_ci95':ba_ci,'confusion_units':cm}
    if scores is not None:
        s=np.array(scores); dif=s[y==1,None]-s[y==0][None,:]
        result['auroc']=float(np.mean((dif>0)+.5*(dif==0)))
    return result

def retail():
    # Reexecute pinned tool implementations and keep all task/seed/position observations.
    summary=old.run_retail_privacy_and_utility(); save('retail_utility.json',summary)
    rows=json.loads((OUT/'retail_units.json').read_text())
    ids=sorted(set(r['task_id'] for r in rows if r['eligible']))
    train=set(ids[:48]); test=set(ids[48:]); policies=list(dict.fromkeys(r['policy'] for r in rows))
    fields=['obs_saw_cancel','obs_write_count','obs_write_bytes']
    def X(rs):return [[r[k] for k in fields] for r in rs]
    bt=[r for r in rows if r['policy']=='baseline' and r['position']=='before' and r['task_id'] in train]
    d0=old.fit_multifeature_linear(X(bt),[r['real_has_cancel'] for r in bt])
    results=[]; predictions=[]
    for policy in policies:
        for position in ['before','after']:
            tr=[r for r in rows if r['policy']==policy and r['position']==position and r['task_id'] in train]
            te=[r for r in rows if r['policy']==policy and r['position']==position and r['task_id'] in test]
            d2=old.fit_multifeature_linear(X(tr),[r['real_has_cancel'] for r in tr])
            pd0=old.predict_multifeature_linear(d0,X(te)); pd2=old.predict_multifeature_linear(d2,X(te))
            # Same ridge linear score as prior classifier (not calibrated probabilities).
            mu,sd,w=d2
            scores=np.column_stack([np.ones(len(te)),(np.array(X(te))-mu)/sd])@w
            # Policy-aware rule using public fixed insertion position and allowed tool names only.
            filtered=[]
            count=[]
            for r in te:
                seq=r['dispatch']
                if policy not in ['baseline','discard','shadow']:
                    seq=seq[1:] if position=='before' else seq[:-1]
                filtered.append(int(any(t[0]=='cancel_pending_order' for t in seq)))
                count.append(int(r['obs_cancel_count']>=2))
            methods={'D0':(pd0,None),'D2_legacy_linear':(pd2,scores),
                     'majority':([0]*len(te),None),'known_position_filter':(filtered,None)}
            if policy in ['live_mutation','live_decoy_account']:methods['cancel_count_ge2']=(count,None)
            report={'policy':policy,'position':position,'methods':{}}
            for name,(pred,score) in methods.items():
                report['methods'][name]=metrics(te,pred,score)
                for r,pr in zip(te,pred):predictions.append({k:r[k] for k in ['task_id','seed','position','policy','real_has_cancel']}|{'method':name,'prediction':int(pr)})
            # Paired task-level legacy gain, descriptive only.
            dif=defaultdict(list)
            for r,a,b in zip(te,pd0,pd2):dif[r['task_id']].append(int(b==r['real_has_cancel'])-int(a==r['real_has_cancel']))
            report['legacy_paired_gain']=old.bootstrap_ci([np.mean(v) for v in dif.values()])
            results.append(report)
    save('retail_observers.json',results);save('retail_predictions.json',predictions)
    diagnostics={}
    for policy in ['live_idempotent_item_swap','live_mutation']:
        for pos in ['before','after']:
            rs=[r for r in rows if r['eligible'] and r['policy']==policy and r['position']==pos]
            diagnostics[policy+'_'+pos]={'errors':dict(Counter(r['cover_error_text'] for r in rs if r['cover_error_text'])),
                'baseline_error_free_tasks':len(set(r['task_id'] for r in rs if not r['baseline_errors'])),
                'baseline_error_free_units':sum(not r['baseline_errors'] for r in rs),
                'baseline_error_free_equal_units':sum(r['native_reward'] for r in rs if not r['baseline_errors']),
                'equal_units_by_task':dict(Counter(r['task_id'] for r in rs if r['native_reward']))}
    for split,ss in [('train',train),('test',test)]:
        rs=[r for r in rows if r['task_id'] in ss and r['policy']=='baseline' and r['position']=='before' and r['seed']==old.SEEDS[0]]
        diagnostics[split]={'tasks':len(rs),'positive':sum(r['real_has_cancel'] for r in rs),'negative':sum(1-r['real_has_cancel'] for r in rs),'task_ids':sorted(ss)}
    save('retail_diagnostics.json',diagnostics)
    print('Retail replay and observers complete',flush=True)

def tls():
    items=[json.loads(s) for s in (old.CS_DIR/'data/replay-inputs/e1.jsonl').read_text().splitlines() if s]
    srv,cli=old.make_loopback_cert(OUT/'local-cert')
    eng={'tidal power','heat pumps','solar batteries','water filtration','rail signaling','bicycle gears','data backups','food refrigeration','bridge inspections','acoustic insulation','electric motors','building ventilation'}
    # Cap is fitted to training byte lengths and rounded to 128B. Overflow emits extra 128B frames.
    train_max=max(len(i['text'].encode())+4 for i in items if i['split']=='train')
    cap=((train_max+127)//128)*128
    policies=['unpadded','bucket_256','bucket_512','bucket_1024','fixed_16848','train_cap']
    rng=np.random.default_rng(20261021); cache={}; allrows=[]; results=[]
    def capture(txt,policy):
        key=(txt,policy)
        if key in cache:return cache[key]
        if policy=='train_cap':
            body=txt.encode();msg=len(body).to_bytes(4,'big')+body
            target=max(cap,((len(msg)+127)//128)*128);msg+=b'\0'*(target-len(msg));frames=[msg[j:j+128] for j in range(0,len(msg),128)]
        else:frames=old.build_terminal_frames(txt,policy,rng)
        c=old.run_single_tls_replay(srv,cli,frames)
        assert c['recovered_sha256']==hashlib.sha256(txt.encode()).hexdigest()
        assert c['app_wire_bytes']==sum(len(f)+29 for f in frames)
        cache[key]=c;return c
    for regime in ['T1','T2','T3','T4']:
        data=[]
        for i in items:
            txt=i['text'];lbl=i['label']
            if regime=='T2' and lbl==1:
                txt='. '.join([s.strip() for s in txt.split('.') if s.strip()][:2])+'.'
            if regime=='T3':
                partner=next(j for j in items if j['id']==i['id'][:-1]+'1')
                txt='. '.join([s.strip() for s in partner['text'].split('.') if s.strip()][:2+lbl])+'.'
            if regime=='T4':lbl=int(i['topic'] in eng)
            data.append(dict(i,text=txt,label=lbl))
        a=[[len(i['text'].encode()) for i in data if i['label']==c] for c in [0,1]]
        pooled=np.sqrt(sum((len(v)-1)*np.var(v,ddof=1) for v in a)/(len(data)-2))
        d=abs(np.mean(a[1])-np.mean(a[0]))/pooled
        for policy in policies:
            rr=[]
            for i in data:
                c=capture(i['text'],policy)
                r={k:i[k] for k in ['id','group_id','split','label']}
                r.update(regime=regime,policy=policy,plaintext_bytes=len(i['text'].encode()),**c)
                rr.append(r);allrows.append(r)
            tr=[r for r in rr if r['split']=='train'];te=[r for r in rr if r['split']=='test']
            rule=old.fit_1d_classifier([r['app_payload_bytes'] for r in tr],[r['label'] for r in tr])
            pr=old.predict_1d(rule,[r['app_payload_bytes'] for r in te]);by=defaultdict(list)
            for r,v in zip(te,pr):by[r['group_id']].append(int(v==r['label']))
            results.append({'regime':regime,'policy':policy,'cohen_d':float(d),
                'accuracy_ci95':old.bootstrap_ci([np.mean(v) for v in by.values()]),
                'mean_wire_bytes':float(np.mean([r['app_wire_bytes'] for r in rr])),
                'mean_records':float(np.mean([r['app_records'] for r in rr])),
                'test_n':len(te),'test_topics':len(by),'fit_rule':rule})
        print(regime+' socket replay complete',flush=True)
    for r in results:
        base=next(x for x in results if x['regime']==r['regime'] and x['policy']=='unpadded')['mean_wire_bytes']
        r['matched_unpadded_bytes']=base;r['matched_ratio']=r['mean_wire_bytes']/base
    save('tls_gradient.json',results);save('tls_records.json',allrows)
    save('tls_cap.json',{'training_max_framed_bytes':train_max,'cap_plain_bytes':cap,'overflow_policy':'extra 128B frames; never truncate','test_overflows':sum(len(i['text'].encode())+4>cap for i in items if i['split']=='test'),'training_rule':'round max training framed length to 128B','socket_connections':len(cache)})
    # Monte Carlo replay: each first draw measured on sockets; remaining 49 draws calculated from validated record framing.
    clean=[r for r in allrows if r['regime']=='T1' and r['policy']=='unpadded' and r['split']=='train']
    d0=old.fit_1d_classifier([r['app_payload_bytes'] for r in clean],[r['label'] for r in clean]);e3=[]
    for pol in ['offset_512','bucket_1024','stoch_u512','stoch_u1024','fixed_16848','train_cap']:
        n=50 if pol.startswith('stoch') else 1;rs=[];mc_rng=np.random.default_rng(20261021);wires=[]
        for j in range(n):
            rr=[]
            for i in items:
                if j==0:c=capture(i['text'],pol)
                else:
                    fr=old.build_terminal_frames(i['text'],pol,mc_rng)
                    c={'app_wire_bytes':sum(len(f)+29 for f in fr),'app_payload_bytes':sum(len(f)+24 for f in fr),'app_records':len(fr),'last_record_payload':len(fr[-1])+24}
                rr.append(dict(i,**c));wires.append(c['app_wire_bytes'])
            tr=[r for r in rr if r['split']=='train'];te=[r for r in rr if r['split']=='test']
            fit=lambda r:old.fit_1d_classifier([x['app_payload_bytes'] for x in r],[x['label'] for x in r])
            xt=[r['app_payload_bytes'] for r in te];p0=old.predict_1d(d0,xt);p4=old.predict_1d(fit(tr[:8]),xt);p12=old.predict_1d(fit(tr),xt)
            for r,v0,v4,v12 in zip(te,p0,p4,p12):rs.append({'group_id':r['group_id'],'draw':j,'id':r['id'],'D0':int(v0==r['label']),'D2k4':int(v4==r['label']),'D2k12':int(v12==r['label'])})
        groups=sorted(set(r['group_id'] for r in rs));v={}
        for key in ['D0','D2k4','D2k12']:v[key]=[float(np.mean([r[key] for r in rs if r['group_id']==g])) for g in groups]
        e3.append({'policy':pol,'n_draws':n,'D0':old.bootstrap_ci(v['D0']),'D2k4':old.bootstrap_ci(v['D2k4']),'D2k12':old.bootstrap_ci(v['D2k12']),'gain':old.bootstrap_ci(np.array(v['D2k12'])-v['D0']),'mean_wire_bytes':float(np.mean(wires)),'matched_ratio':float(np.mean(wires))/next(r for r in results if r['regime']=='T1' and r['policy']=='unpadded')['mean_wire_bytes']})
        save('tls_adaptive_units_'+pol+'.json',rs)
    save('tls_adaptive.json',e3)
    print('TLS complete',flush=True)

def scenarios():
    rows=list(csv.DictReader((ROOT/'experiments/revision-m1-m8/m1_validity_benchmark.csv').open(encoding='utf-8')))
    labels=['Compatible','Incompatible','Unresolved'];results={}
    for name in ['headline_baseline_pred','expert1_3check_pred','expert2_3check_pred','always_incompatible','always_unresolved']:
        pred=[r[name] if name in r else ('Incompatible' if name=='always_incompatible' else 'Unresolved') for r in rows]
        results[name]=[[sum(r['ground_truth']==a and p==b for r,p in zip(rows,pred)) for b in labels] for a in labels]
    save('scenario_confusions.json',{'row_truth_column_prediction_order':labels,'matrices':results,'interpretation':'author-constructed illustration, not external validation'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('part',choices=['retail','tls','scenarios']);args=ap.parse_args()
    globals()[args.part]()
