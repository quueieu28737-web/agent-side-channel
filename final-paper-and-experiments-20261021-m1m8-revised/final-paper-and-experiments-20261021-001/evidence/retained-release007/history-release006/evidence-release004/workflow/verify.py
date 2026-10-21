"""Read-only verification of the released, saved workflow decomposition."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import csv
import hashlib
import json
import math
from pathlib import Path


def load_csv(path):
    with path.open(encoding='utf8', newline='') as stream:
        return list(csv.DictReader(stream))


def verify(directory, project=None):
    roots=load_csv(directory/'root-scores.csv')
    queries=load_csv(directory/'query-components.csv')
    result=json.loads((directory/'result.json').read_text(encoding='utf8'))
    cross=load_csv(directory/'decision-count-cross.csv')
    assert len(roots)==1590 and len(queries)==4770
    assert len({(r['case_id'],r['arm']) for r in roots})==1590
    grouped=defaultdict(list)
    for q in queries:
        grouped[int(q['index'])].append(q)
    missing=[]
    primary={a:[] for a in ('R','T','V')}
    for root in roots:
        group=grouped[int(root['index'])]
        assert len(group)==3 and len({q['query_id'] for q in group})==3
        is_missing=root['missing']=='True'
        assert all(q['missing']==root['missing'] for q in group)
        if is_missing:
            assert root['joint_correct_queries']=='' and all(q['joint_correct']=='' for q in group)
            score=None
            missing.append(int(root['index']))
        else:
            successes=sum(q['joint_correct']=='True' for q in group)
            assert successes==int(root['joint_correct_queries'])
            assert all(q['schema_correct']=='True' and q['evidence_ids_correct']=='True' for q in group)
            for q in group:
                assert (q['joint_correct']=='True') == (q['decision_correct']=='True' and q['counts_correct']=='True')
            score=Fraction(successes,3)
        if root['partition']=='primary_test':
            primary[root['arm']].append(score)
    assert missing==[37] and all(len(v)==512 for v in primary.values())
    arm_bounds={}
    for arm,values in primary.items():
        known=sum((v for v in values if v is not None),Fraction())
        missing_n=values.count(None)
        arm_bounds[arm]=(known/512,(known+missing_n)/512)
        saved=result['primary']['arms'][arm]
        assert math.isclose(float(arm_bounds[arm][0]),saved['mean_lower'],abs_tol=1e-12)
        assert math.isclose(float(arm_bounds[arm][1]),saved['mean_upper'],abs_tol=1e-12)
    lo=arm_bounds['V'][0]-arm_bounds['T'][1]
    hi=arm_bounds['V'][1]-arm_bounds['T'][0]
    half_width=math.sqrt(2*math.log(40)/512)
    envelope=[max(-1,float(lo)-half_width),min(1,float(hi)+half_width)]
    assert all(math.isclose(x,y,abs_tol=1e-12) for x,y in zip(envelope,result['primary_envelope']['bounds']))
    for row in cross:
        rows=[q for q in queries if q['partition']==row['partition'] and q['arm']==row['arm']]
        counts=Counter((q['decision_correct']=='True',q['counts_correct']=='True') for q in rows if q['missing']!='True')
        for field,key in [('decision_right_counts_right',(True,True)),('decision_right_counts_wrong',(True,False)),
                          ('decision_wrong_counts_right',(False,True)),('decision_wrong_counts_wrong',(False,False))]:
            assert counts[key]==int(row[field])
    original_hashes_checked=0
    if project:
        hashes=json.loads((directory/'input-hashes.json').read_text(encoding='utf8'))
        for path,digest in hashes.items():
            assert hashlib.sha256((project/path).read_bytes()).hexdigest()==digest
            original_hashes_checked+=1
    return {'status':'SAVED_DECOMPOSITION_ARITHMETIC_PASS','model_calls':0,'fits':0,
            'roots':1590,'query_rows':4770,'missing_root_slot':37,
            'original_source_files_checked':original_hashes_checked,
            'primary_V_minus_T_bounds':[float(lo),float(hi)],'conditional_envelope':envelope,
            'not_independent_researcher_validation':True,'not_a_replacement_primary_endpoint':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path,nargs='?',default=Path(__file__).parent/'attempt-002')
    parser.add_argument('--project',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.directory,args.project),indent=2))
