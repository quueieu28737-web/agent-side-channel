"""Check complete observed captures and recompute published metrics; no new traffic."""
import argparse
import datetime as dt
import json
import zipfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from r6common import *
from analyze import captures, model_sha, weights, metric_draws, brief, resources, detector_metrics

def capture_sha(name):
    p=HERE/name
    if p.exists():return sha(p)
    with zipfile.ZipFile(HERE/'captures.zip') as z:
        return hashlib.sha256(z.read(name)).hexdigest()

def main():
    cfg=read(HERE/'frozen.json');af=read(HERE/'attacker_freeze.json')
    for n,h in cfg['source_sha256'].items():assert sha(HERE/n)==h,n
    for n,h in af['source_sha256'].items():assert sha(HERE/n)==h,n
    assert af['frozen_sha256']==sha(HERE/'frozen.json')
    assert not af['test_captures_present_at_fit']
    assert all(model_sha(n)==h for n,h in af['models'].items())
    source,split,cal=inputs();original={key(e):e for e in source}
    assert cfg['calibration_sha256']==sha(R4/'calibration.json')
    for k,h in cfg['training_episode_hashes'].items():assert digest(original[k])==h
    tr=captures('train');te=captures('test')
    assert len(tr)==2484 and len(te)==1656
    assert not {r['user'] for r in tr}&{r['user'] for r in te}
    assert len({r['user'] for r in tr})==29 and len({r['user'] for r in te})==24
    for part,rows in (('train',tr),('test',te)):
        receipt=read(HERE/f'{part}_complete.json')
        assert receipt['frozen_sha256']==sha(HERE/'frozen.json')
        assert receipt['count']==len(rows)
        for n,h in receipt['files'].items():assert capture_sha(n)==h,n
        expected={(key(e),c) for e in source if e['task'] in split[part] for c in CONDITIONS}
        assert {(key(r),r['condition']) for r in rows}==expected
    early=0;fixed=0;max_parallel=0;failures=[]
    for r in tr+te:
        label=key(r)+'-'+r['condition']; e=original[key(r)]
        assert r['source_episode_sha256']==digest(e)
        assert r['frozen_sha256']==sha(HERE/'frozen.json')
        for k in ('task','prompt','repeat','user','has_cancel','has_return','native_reward'):assert r[k]==e[k]
        assert all(t>=0 for d,n,t in r['records'])
        assert r['wire_bytes']==sum(n+5 for d,n,t in r['records'])
        real=[q for q in r['requests'] if q['kind']=='real']
        assert len(real)==len(e['calls'])==r['real_calls_completed']
        assert [q['name'] for q in real]==[c['name'] for c in e['calls']]
        backend={q['id']:q for q in r['backend']};done={q['id']:q['time_ns'] for q in r['completions']}
        timeline=[]
        for q in r['requests']:
            assert q['queued_ns']<=q['released_ns']<=done[q['id']]
            b=backend[q['id']]
            assert b['received_ns']<=b['enqueued_ns']<=b['start_ns']<=b['end_ns']<=done[q['id']]
            timeline.extend([(q['released_ns'],1),(done[q['id']],-1)])
        active=0;peak=0
        for _t,delta in sorted(timeline):active+=delta;peak=max(peak,active)
        assert active==0 and peak<=(2 if r['condition']=='shadow_parallel2' else 1)
        max_parallel=max(max_parallel,peak)
        for prev,nxt in zip(real,real[1:]):assert nxt['released_ns']>=done[prev['id']]
        if r['status']!='complete' or not r['response_equal'] or not r['db_equal']:failures.append(label)
        if r['period_ns']:
            fixed+=1
            assert r['slots']==133 and len(r['records'])==266
            assert r['client_cells_received']==r['server_cells_received']==133
            assert Counter(d for d,n,t in r['records'])=={1:133,-1:133}
            assert {n for d,n,t in r['records']}=={4120}
            assert r['pending_bytes_at_end']==0
            assert r['finish_ns']>=r['period_ns']*r['slots']
            assert all(q['kind']=='real' for q in r['requests'])
            for sent in (r['client_send'],r['server_send']):
                assert len(sent)==133 and [s['slot'] for s in sent]==list(range(133))
                for s in sent:
                    assert s['bytes']==4096 and 0<=s['useful_bytes']<=4092
                    early+=s['time_ns']<s['deadline_ns']
        if r['task'] in split['test']:
            # This legacy-named wall-clock field is recorded at receipt creation,
            # not the measurement origin. The pipeline receipt separately binds order.
            assert dt.datetime.fromisoformat(r['start_utc'])>dt.datetime.fromisoformat(af['fitted_utc'])
    assert early==0 and fixed==1380
    assert not failures, failures
    tc=read(HERE/'training_cuts.json')
    for item in tc['detectors'].values():
        for fold in item['folds']:assert not set(fold['train_customers'])&set(fold['heldout_customers'])
    pred=read(HERE/'predictions.json');res=read(HERE/'results.json');draws={}
    for k,cell in pred.items():
        y=np.array(cell['labels']);w=weights(cell['customers']);bd=[];ad=[]
        for name,m in cell['models'].items():
            ba,au=metric_draws(y,m['scores'],m['predictions'],w);bd.append(ba);ad.append(au)
            assert res['cells'][k]['models'][name]=={'ba':brief(ba),'auroc':brief(au)}
        ba=np.nanmax(bd,axis=0);au=np.nanmax(ad,axis=0);draws[k]=ba
        assert res['cells'][k]['ba']==brief(ba) and res['cells'][k]['auroc']==brief(au)
        assert res['cells'][k]['meets_absolute_criterion']==bool(np.nanquantile(ba[1:],.975)<.60 and au[0]<.65)
    for arm in ('baseline','rules'):
        for target in ('cancel','return'):
            raw='|'.join((arm,'raw','suite',target))
            for cond in CONDITIONS:
                k='|'.join((arm,cond,'suite',target));sz='|'.join((arm,cond,'size_order',target))
                assert res['contrasts'][k+'-raw']==brief(draws[k]-draws[raw])
                assert res['contrasts'][k+'-size']==brief(draws[k]-draws[sz])
    dp=read(HERE/'detector_predictions.json')
    for k,v in dp.items():
        assert res['detectors'][k]==detector_metrics(np.array(v['y']),np.array(v['scores']),np.array(v['customers']))
    assert res['resources']==resources(te)
    receipt={'status':'LIVE_TIMING_TUNNEL_CAPTURE_SPLIT_ATTACK_AND_NUMERIC_CHECKS_PASS',
             'training_sessions':len(tr),'test_sessions':len(te),'total_sessions':len(tr)+len(te),
             'source_model_runs':690,'new_model_calls':0,'tunnel_sessions':fixed,'early_cell_sends':early,
             'failures':failures,'max_outstanding_calls':max_parallel,
             'frozen_sha256':sha(HERE/'frozen.json'),'attacker_freeze_sha256':sha(HERE/'attacker_freeze.json'),
             'results_sha256':sha(HERE/'results.json'),'prediction_cells':len(pred),
             'scope':'Measured live local tool RPC chain, fixed source trajectories, relay-observed TLS arrival times; not new LLM/production/independent-population runs'}
    if '--save' in sys.argv:write(HERE/'validation.json',receipt)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
