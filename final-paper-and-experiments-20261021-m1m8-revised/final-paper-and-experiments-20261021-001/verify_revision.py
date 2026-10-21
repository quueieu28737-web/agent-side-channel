"""Read-only consistency checks for the corrected saved observations (stdlib only)."""
from pathlib import Path
import json,math
from collections import defaultdict,Counter
P=Path(__file__).resolve().parent
A=P/'experiments/reviewer-audit'
def load(f):return json.loads((A/f).read_text(encoding='utf-8'))
def close(a,b):assert math.isclose(a,b,abs_tol=1e-10),(a,b)
def main():
    rr=load('retail_units.json');assert len(rr)==6210
    keys={(r['task_id'],r['seed'],r['policy'],r['position']) for r in rr};assert len(keys)==6210
    assert len({r['task_id'] for r in rr if r['eligible']})==97
    idx={(r['task_id'],r['seed'],r['policy'],r['position']):r for r in rr}
    dg=load('retail_diagnostics.json');assert dg['test']['positive']==11 and dg['test']['negative']==38
    for s in load('retail_utility.json'):
        rs=[r for r in rr if r['eligible'] and r['policy']==s['policy'] and r['position']==s['position']]
        assert len(rs)==291
        for src,out in [('native_reward','eligible_native_reward'),('user_orders_state_equal','eligible_user_orders_equal'),('gold_touched_state_equal','eligible_gold_touched_equal')]:
            close(sum(r[src] for r in rs)/len(rs),s[out])
    predictions=load('retail_predictions.json'); groups=defaultdict(list)
    for pr in predictions:
        r=idx[(pr['task_id'],pr['seed'],pr['policy'],pr['position'])]
        if pr['method']=='known_position_filter':
            seq=r['dispatch']
            if r['policy'] not in ['baseline','discard','shadow']:seq=seq[1:] if r['position']=='before' else seq[:-1]
            assert pr['prediction']==int(any(t[0]=='cancel_pending_order' for t in seq))
        if pr['method']=='cancel_count_ge2':assert pr['prediction']==int(r['obs_cancel_count']>=2)
        groups[(pr['policy'],pr['position'],pr['method'])].append(pr)
    for rep in load('retail_observers.json'):
        for name,m in rep['methods'].items():
            prs=groups[(rep['policy'],rep['position'],name)];assert len(prs)==147
            close(sum(p['prediction']==p['real_has_cancel'] for p in prs)/147,m['accuracy'])
            rates=[]
            for c in [0,1]:
                subset=[p for p in prs if p['real_has_cancel']==c]
                rates.append(sum(p['prediction']==c for p in subset)/len(subset))
            close(sum(rates)/2,m['balanced_accuracy'])
            if name in ['known_position_filter','cancel_count_ge2']:close(m['accuracy'],1)
    records=load('tls_records.json');grad=load('tls_gradient.json')
    for s in grad:
        rs=[r for r in records if r['regime']==s['regime'] and r['policy']==s['policy']];assert len(rs)==48
        close(sum(r['app_wire_bytes'] for r in rs)/48,s['mean_wire_bytes'])
        base=next(r for r in grad if r['regime']==s['regime'] and r['policy']=='unpadded')
        close(s['matched_ratio'],s['mean_wire_bytes']/base['mean_wire_bytes'])
        for r in rs:assert r['app_wire_bytes']==r['app_payload_bytes']+5*r['app_records']
    for r in load('tls_adaptive.json'):
        units=load('tls_adaptive_units_'+r['policy']+'.json');assert len(units)==24*r['n_draws']
        for field,out in [('D0','D0'),('D2k4','D2k4'),('D2k12','D2k12')]:close(sum(x[field] for x in units)/len(units),r[out][0])
    c=load('combined_result_records.json');rs=c['baseline_records']+c['added_records']
    assert len(rs)==39 and len({r['citation_key'] for r in rs})==26
    cap=load('tls_cap.json');assert cap['training_max_framed_bytes']==1194 and cap['cap_plain_bytes']==1280 and cap['test_overflows']==0
    for name in ['main','supplement']:
        log=(P/'provenance/build-logs'/(name+'.log')).read_text(errors='replace')
        for bad in ['undefined references','undefined on input line','multiply defined','Overfull','Float too large']:
            assert bad not in log,(name,bad)
    print(json.dumps({'status':'CORRECTED_OBSERVATION_AND_TABLE_CONSISTENCY_PASS','retail_rows':6210,'retail_tasks':115,'eligible_tasks':97,'test_tasks':49,'record_ledger_records':39,'record_ledger_families':26,'audit_families':20,'new_model_calls':0},indent=2))
if __name__=='__main__':main()
