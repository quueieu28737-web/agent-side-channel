"""Read-only integrity checks, including real-fragment preservation by adapters."""
import argparse
from r7common import *
import adapters
def main():
    f=read(HERE/'freeze.json');assert f['source_sha256']==source_hashes()
    assert f['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    assert f['r6_captures_sha256']==sha(R6/'captures.zip')
    cal=read(HERE/'calibration.json');assert f['calibration_sha256']==sha(HERE/'calibration.json')
    train=rows('train');test=rows('test');assert not {r['user'] for r in train}&{r['user'] for r in test}
    assert len(train)==414*len(CONDITIONS) and len(test)==276*len(CONDITIONS)
    assert set(cal['short_customers'])<set(cal['all_train_customers'])
    for part,rs in [('train',train),('test',test)]:
        assert f['data_sha256'][part]==sha(HERE/(part+'.zip'))
        assert len({(key(r),r['condition']) for r in rs})==len(rs)
        for r in rs:
            a=r['records'];assert all(a[i][2]<=a[i+1][2] for i in range(len(a)-1))
            assert r['wire_bytes']==sum(n+5 for d,n,t in a)
            if r['condition'] in SIMULATED:assert r['integrity']['real_fragments']==r['integrity']['kept']
            else:assert r['integrity']['db_equal'] and r['integrity']['response_equal']
        # Regenerate every transformation, retaining every real input fragment.
        original={key(r):r for r in captures(part) if r['condition']=='raw'}
        for r in rs:
            if r['condition'] in SIMULATED:assert adapters.transform(original[key(r)],r['condition'],cal)==r
    checks=['input_hashes','train_test_customer_disjoint','complete_grid','all_transformations_reproduced','all_real_fragments_preserved','all_measured_state_checks']
    if (HERE/'results.json').exists():
        from run import summarize
        p=read(HERE/'predictions.json');result=read(HERE/'results.json');assert summarize(p)==result
        assert len(result['cells'])==len(CONDITIONS)*4
        old=read(R6/'results.json')
        for arm in ('baseline','rules'):
            for c in MEASURED:
                for t in ('cancel','return'):
                    assert result['cells']['|'.join((arm,c,t))]['ba']['point']+1e-12>=old['cells']['|'.join((arm,c,'suite',t))]['ba']['point']
        checks.extend(['all_metrics_recomputed','all_E13_attackers_retained'])
    result={'status':'PASS','checks':checks,'train_transformed_sessions':len(train),'test_transformed_sessions':len(test),
            'independent_customers':len({r['user'] for r in train+test}),'freeze_sha256':sha(HERE/'freeze.json')}
    if '--save' in sys.argv:write(HERE/'validation.json',result)
    print(json.dumps(result))
if __name__=='__main__':main()
