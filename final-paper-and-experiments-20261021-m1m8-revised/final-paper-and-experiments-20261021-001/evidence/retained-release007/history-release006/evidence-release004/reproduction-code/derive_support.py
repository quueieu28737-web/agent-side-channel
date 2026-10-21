"""Make reviewer-facing CSV matrices from completed saved diagnostic outputs.
No estimator imports, fits, network or source changes.
"""
import collections,csv,json,pathlib
HERE=pathlib.Path(__file__).absolute().parent
def write(name,fields,rows):
    with (HERE/name).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
support=json.loads((HERE/'identity-question-form-proxy.json').read_text())
write('identity-question-form-support-long.csv',list(support[0]),support)
families=json.loads((HERE/'identity-dataset-support.json').read_text())
write('identity-dataset-support.csv',list(families[0]),families)
wide=[]
for label in sorted({x['identity'] for x in support}):
    row={'identity':label}
    for x in support:
        if x['identity']==label and x['partition']=='test':
            row[x['question_form_proxy']]=x['rows']
    row['all_rows']=sum(row[x] for x in ('what','which','who','when','where','how','other'))
    wide.append(row)
write('identity-question-form-test-matrix.csv',['identity','what','which','who','when','where','how','other','all_rows'],wide)
summary=json.loads((HERE/'attempt-001/summary.json').read_text())
rows=[]
for group,data in summary['results'].items():
    for label,n in data['identities'].items():
        rows.append({'stratum':group,'identity':label,'test_rows':n,'stratum_rows':data['rows'],
            'stratum_questions':data['questions'],'stratum_not_verified_task_success':True})
write('test-stratum-identity-composition.csv',list(rows[0]),rows)
scores=[]
for group,data in summary['results'].items():
    for name,v in data['programs'].items():
        scores.append({'stratum':group,'program':name,'rows':data['rows'],'questions':data['questions'],
            'question_mean_loss_nats':v['loss'],'question_mean_accuracy':v['accuracy'],
            'analyst_only':name=='failure_only','new_fit':name in ('failure_only','empty_only','activity_only')})
write('all-and-stratified-scores.csv',list(scores[0]),scores)
print('5 CSV exports complete; no fitting')
