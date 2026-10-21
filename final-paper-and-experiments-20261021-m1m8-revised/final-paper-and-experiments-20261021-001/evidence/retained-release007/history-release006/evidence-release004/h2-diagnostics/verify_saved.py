"""Independent stdlib-only saved-probability and support checks; no source data,
NumPy/sklearn, fitting, network or model calls. Prints JSON, never writes files.
"""
import collections,json,math,pathlib
HERE=pathlib.Path(__file__).absolute().parent
summary=json.loads((HERE/'attempt-001/summary.json').read_text())
rows=[json.loads(x) for x in (HERE/'attempt-001/predictions.jsonl').read_text().splitlines()]
assert len(rows)==1135 and len({r['id'] for r in rows})==1135
def qmean(values,selected):
    groups=collections.defaultdict(list)
    for r,v in zip(selected,values):groups[r['question_hash']].append(v)
    return sum(sum(v)/len(v) for v in groups.values())/len(groups)
checks=0
for name in ('all','flagged','unflagged'):
    selected=[r for r in rows if name=='all' or r['flagged']==(name=='flagged')]
    expected=summary['results'][name]
    assert len(selected)==expected['rows'] and len({r['question_hash'] for r in selected})==expected['questions']
    for model in selected[0]['probabilities']:
        losses=[];correct=[]
        for r in selected:
            p=r['probabilities'][model];assert abs(sum(p)-1)<1e-12 and all(v>=0 for v in p)
            y=r['classes'].index(r['label']);losses.append(-math.log(max(1e-6,min(1,p[y]))))
            correct.append(int(max(range(len(p)),key=p.__getitem__)==y))
        assert abs(qmean(losses,selected)-expected['programs'][model]['loss'])<1e-12
        assert abs(qmean(correct,selected)-expected['programs'][model]['accuracy'])<1e-12
        checks+=2
ledger=json.loads((HERE/'attempt-001/fit_ledger.json').read_text())
assert ledger['planned']==12 and len(ledger['fits'])==12 and all(x['status']=='complete' for x in ledger['fits'])
support=json.loads((HERE/'identity-question-form-proxy.json').read_text())
assert sum(x['rows'] for x in support)==4200
assert {p:sum(x['rows'] for x in support if x['partition']==p) for p in ('train','validation','test')}=={'train':2043,'validation':1022,'test':1135}
print(json.dumps({'status':'PASS','stdlib_independent_score_checks':checks,'fits_read_only':12,
    'source_rows_reconciled':4200,'test_rows':1135,'new_fits_executed_by_verifier':0,'model_api_calls':0},indent=2))
