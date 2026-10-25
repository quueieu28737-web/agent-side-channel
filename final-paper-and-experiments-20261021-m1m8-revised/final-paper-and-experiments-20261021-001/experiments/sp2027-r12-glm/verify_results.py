"""Offline cohort, provenance, split, calibration and saved-prediction checks."""
from common import *
from network_replay import episodes,validate_calibration
from evaluate_network import stats
import numpy as np,datetime

def main():
    checks=[]
    def ck(ok,name):
        assert ok,name
        checks.append(name)
    plan=read(HERE/'formal_plan.json'); rows=episodes('train')+episodes('test')
    ck(len(rows)==115 and len({e['task'] for e in rows})==115,'115 unique completed episodes')
    groups={p:{e['user'] for e in rows if e['task'] in plan[p]} for p in ('train','test')}
    ck(not groups['train']&groups['test'],'customer-disjoint partition')
    ck((len(groups['train']),len(groups['test']))==(29,24),'original 29/24 customer counts')
    cal=validate_calibration();ck(cal['training_episodes']==69,'69 training episodes only')
    for name,digest in read(HERE/'source_freeze.json').items():ck(sha(HERE/name)==digest,'source '+name)
    for filename in ('analysis_freeze.json','LOCALIZATION_ADDITION.json'):
        for name,digest in read(HERE/filename)['source_hashes'].items():ck(sha(HERE/name)==digest,'analysis '+name)
    returned=set(); receipts=[]
    for e in rows:
        d=HERE/'formal'/'baseline'/f"task-{e['task']:03d}-repeat-0"
        results=list(d.glob('*/*/result.json'))
        ck(len(results)==e['model_calls'],'model calls '+str(e['task']))
        usage={'input_tokens':0,'output_tokens':0}
        for p in results:
            result=read(p);receipt=read(p.parent/result['attempt']/'response.json')
            returned.add(receipt['model']);receipts.append((e['task'],receipt['utc']))
            ck(result['usage']==receipt['usage'],'usage '+str(p.relative_to(HERE)))
            for k in usage:usage[k]+=result['usage'].get(k,0)
            answer=result['answer']
            if answer:
                ck(len(receipt['tool_calls'])==1 and receipt['tool_calls'][0]['input']==answer,'decision '+str(p.relative_to(HERE)))
            else:ck(e['status']=='protocol_error','malformed response retained as failure')
        ck(all(e['usage'][k]==v for k,v in usage.items()),'episode token accounting '+str(e['task']))
    ck(returned=={'glm-5.3-flash'},'returned model alias')
    boundary=(HERE/'network_calibration.json').stat().st_mtime
    test_first=min(datetime.datetime.fromisoformat(t).timestamp() for task,t in receipts if task in plan['test'])
    ck(test_first>=boundary,'calibration file frozen before first test response')
    sessions=read(HERE/'network_sessions.json');ck(len(sessions)==230,'230 actual TLS sessions')
    for s in sessions:
        ck(s['calibration_sha256']==sha(HERE/'network_calibration.json'),'session calibration '+str((s['task'],s['condition'])))
    for filename in ('network_predictions.json','D2_predictions.json','localization_predictions.json'):
        for p in read(HERE/filename):
            ck(len(p['units'])==len(p['scores'])==len(p['predictions'])==46,'test prediction count '+filename)
            ck({u['task_id'] for u in p['units']}==set(plan['test']),'prediction test IDs '+filename)
            ck(all(np.isfinite(p['scores'])),'finite scores '+filename)
    write(HERE/'verification.json',{'passed':True,'checks':len(checks),'items':checks,'episodes':115,
        'customer_counts':{p:len(v) for p,v in groups.items()},'returned_models':sorted(returned),
        'calibration_precedes_test':True,'scope':'Executable consistency and decision receipts; not independent human or deployment validation',
        'protocol_sha256':sha(HERE/'protocol.json'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print('R12_VERIFICATION_PASS',len(checks),flush=True)

if __name__=='__main__':main()
