"""Unchanged inherited saved-probability arithmetic only; no fit/main/counts."""
import collections,json,math
def read_json(path): return json.loads(path.read_text(encoding="utf-8-sig"))

def verify_probabilities(root, bootstrap=False):
    summary=read_json(root/'h2/summary.json'); groups=collections.defaultdict(list)
    for line in (root/'h2/predictions.jsonl').read_text(encoding='utf-8').splitlines():
        row=json.loads(line); groups[row['condition']].append(row)
    assert set(groups)=={'common','document_proxy','clean','shuffle_0','shuffle_1','shuffle_2'}
    effects={}; conditions={}
    for name,rows in groups.items():
        by_question=collections.defaultdict(list)
        for row in rows:
            y=row['classes'].index(row['label']); losses=[]
            for field in ['coarse','combined']:
                p=row[field]; assert len(p)==len(row['classes']) and all(math.isfinite(v) and v>=0 for v in p)
                assert abs(math.fsum(p)-1)<1e-12
                losses.append(-math.log(max(min(p[y],1.0),1e-6)))
            by_question[row['question_hash']].append(losses[0]-losses[1])
        per={q:math.fsum(values)/len(values) for q,values in by_question.items()}
        point=math.fsum(per.values())/len(per)
        assert abs(point-summary['conditions'][name]['increment']['mean'])<1e-12
        effects[name]=per; conditions[name]={'rows':len(rows),'questions':len(per),'increment':point}
        if name=='common':
            assert len(rows)==30 and len(per)==10
            assert all(n==1 for n in collections.Counter((r['question_hash'],r['label']) for r in rows).values())
    assert sum(len(r) for r in groups.values())==5705
    assert all(row['coarse']==row['combined'] for name in ['shuffle_0','shuffle_1','shuffle_2'] for row in groups[name])
    clean=effects['clean']
    assert all(set(effects['shuffle_'+str(i)])==set(clean) for i in range(3))
    primary={
        'C1_common_question_increment':effects['common'],
        'C2_first_document_proxy_increment':effects['document_proxy'],
        'C3_clean_minus_mean_shuffled_increment':{q:clean[q]-math.fsum(effects['shuffle_'+str(i)][q] for i in range(3))/3 for q in clean},
    }
    interval_status='NOT_REQUESTED'
    if bootstrap:
        import numpy as np
        for name,per in primary.items():
            x=np.asarray([per[q] for q in sorted(per)]); rng=np.random.default_rng(20261018)
            values=[float(x[rng.integers(0,len(x),len(x))].mean()) for _ in range(3000)]
            bounds=np.percentile(values,[.8333333333333334,99.16666666666667])
            expected=summary['primary'][name]
            assert abs(float(x.mean())-expected['mean'])<1e-12
            assert max(abs(float(bounds[0])-expected['lower']),abs(float(bounds[1])-expected['upper']))<1e-12
        interval_status='RECONSTRUCTED_FROM_SAVED_PROBABILITIES'
    return {'prediction_rows':5705,'conditions':conditions,'bootstrap':interval_status,'fits_performed':0,'experiment_model_calls':0,'scope':'Fixed saved probabilities; not capture authentication, causal evidence or external replication.'}
