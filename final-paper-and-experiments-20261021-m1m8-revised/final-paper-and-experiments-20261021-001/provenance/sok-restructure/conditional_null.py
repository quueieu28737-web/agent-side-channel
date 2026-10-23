"""Post hoc W1 reference: fixed predictions and task-label permutations.

This implements the plan's task-exchangeability reference, NOT a population
independence or equivalence test: tasks within one customer can be dependent.
Original customer-cluster intervals and the frozen criterion remain primary.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,sys
import numpy as np
P=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
F=P/'experiments/sp2027-r4-full-20261023'

def main():
    data=json.loads((F/'predictions.json').read_text())
    saved=json.loads((F/'results.json').read_text())
    cells=defaultdict(list)
    for row in data:cells[row['prompt'],row['condition'],row['target'],row['view']].append(row)
    output=[]
    for key,rows in sorted(cells.items()):
        u=rows[0]['units'];assert all(r['units']==u for r in rows)
        tasks=sorted({x['task_id'] for x in u});index={t:i for i,t in enumerate(tasks)}
        positions=np.array([index[x['task_id']] for x in u])
        labels=np.array([next(x['y'] for x in u if x['task_id']==t) for t in tasks])
        assert all(x['y']==labels[index[x['task_id']]] for x in u)
        rng=np.random.default_rng(20261023)
        # A common assignment sequence is used across prompts, views and conditions.
        Y=np.stack([labels,*[rng.permutation(labels) for _ in range(2000)]])[:,positions]
        A=np.array([r['predictions'] for r in rows],dtype=float)
        ba=.5*((Y@A.T)/Y.sum(axis=1)[:,None]+((1-Y)@(1-A).T)/(1-Y).sum(axis=1)[:,None])
        maxima=ba.max(axis=1)
        ref=next(r for r in saved['results'] if (r['prompt'],r['condition'],r['target'],r['view'])==key)
        assert abs(maxima[0]-ref['suite_ba'])<1e-12
        q=float(np.quantile(maxima[1:],.95))
        output.append(dict(zip(('prompt','condition','target','view'),key))|{
            'observed_ba':float(maxima[0]),'reference_mean':float(maxima[1:].mean()),
            'reference_q95':q,'reference_tail_fraction':float((1+(maxima[1:]>=maxima[0]-1e-12).sum())/2001),
            'positive_excess_over_q95':max(0,float(maxima[0])-q),
            'tasks':len(tasks),'positive_tasks':int(labels.sum()),'attackers':len(rows)})
    result={'status':'CONDITIONAL_TASK_PERMUTATION_REFERENCE_PASS','seed':20261023,'permutations':2000,
            'source_predictions_sha256':hashlib.sha256((F/'predictions.json').read_bytes()).hexdigest(),
            'scope':'Post hoc fixed-prediction task-label exchangeability reference. Repeats of a task retain one label; customer dependence is not preserved. Tail fractions are conditional reference values, not customer-valid population p-values or evidence of equivalence.',
            'cells':output}
    encoded=json.dumps(result,indent=2)+'\n'
    if '--check' in sys.argv:assert (HERE/'conditional_null_results.json').read_text()==encoded
    else:(HERE/'conditional_null_results.json').write_text(encoded,encoding='utf-8',newline='\n')
    print(json.dumps({'status':result['status'],'cells':len(output),'baseline_network':[r for r in output if r['prompt']=='baseline' and r['view']=='network' and r['condition'] in ('raw','shape_const')]},indent=2))

if __name__=='__main__':main()
