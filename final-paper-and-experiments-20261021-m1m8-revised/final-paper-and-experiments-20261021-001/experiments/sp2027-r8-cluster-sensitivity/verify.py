"""Independent direct-weight check of frozen customer sensitivity, stdlib only."""
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'sp2027-r7-crossfit'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b): assert a is None and b is None or a is not None and b is not None and abs(a-b)<1e-12, (a,b)

def check_metric(rows, saved):
    n=Counter(r['y'] for r in rows)
    nc=Counter((r['y'],r['customer']) for r in rows)
    gc={y:len({r['customer'] for r in rows if r['y']==y}) for y in [0,1]}
    for equal, name in [(False,'episode_weight'),(True,'customer_equal_within_class')]:
        values={}
        for a in rows[0]['attacks']:
            if not n[0] or not n[1]: values[a]=None; continue
            total=0.
            for r in rows:
                y=r['y']
                w=.5/(gc[y]*nc[y,r['customer']]) if equal else .5/n[y]
                total+=w*int(r['attacks'][a]['pred']==y)
            values[a]=total
            close(total,saved[name]['by_attack'][a])
        best=max(v for v in values.values() if v is not None) if n[0] and n[1] else None
        close(best,saved[name]['suite_max_ba'])
        winners=sorted(a for a,v in values.items() if v is not None and abs(v-best)<1e-12)
        assert winners==sorted(saved[name]['winners'])

def denominators(rows):
    groups=defaultdict(set)
    for r in rows: groups[r['customer']].add(r['y'])
    return dict(episodes=len(rows),positive_episodes=sum(r['y']==1 for r in rows),negative_episodes=sum(r['y']==0 for r in rows),
        customers=len(groups),positive_customers=sum(1 in y for y in groups.values()),negative_customers=sum(0 in y for y in groups.values()),
        mixed_label_customers=sum(y=={0,1} for y in groups.values()),tasks=len({r['episode'].rsplit('-r',1)[0] for r in rows}))

f=read(HERE/'freeze.json')
assert f['source_sha256']=={n:sha(HERE/n) for n in f['source_sha256']}
assert f['input_sha256']=={n:sha(SOURCE/n) for n in f['input_sha256']}
result=read(HERE/'results.json'); raw=read(SOURCE/'predictions.json'); original=read(SOURCE/'detailed_results.json')
assert len(raw)==4140 and len(result['cells'])==12
checked=0
for key,v in result['cells'].items():
    arm,cond,target=key.split('|'); rows=[r for r in raw if (r['prompt'],r['condition'],r['target'])==(arm,cond,target)]
    assert len(rows)==345 and len({r['episode'] for r in rows})==345
    assert denominators(rows)==v['denominators']
    assert all(len({r['fold'] for r in rows if r['customer']==c})==1 for c in {r['customer'] for r in rows})
    check_metric(rows,v['metrics'])
    # The source report uses a flat result list; locate a unique matching cell.
    old=[r for r in original['results'] if r['prompt']==arm and r['condition']==cond and r['target']==target]
    assert len(old)==1
    oldvalue=old[0].get('suite_ba',old[0].get('ba'))
    if isinstance(oldvalue,dict): oldvalue=oldvalue['point']
    close(oldvalue,v['metrics']['episode_weight']['suite_max_ba'])
    assert {d['removed_customer'] for d in v['leave_one_positive_customer_out']}=={r['customer'] for r in rows if r['y']==1}
    for d in v['leave_one_positive_customer_out']:
        remain=[r for r in rows if r['customer']!=d['removed_customer']]
        assert denominators(remain)==d['remaining']
        check_metric(remain,d['metrics']); checked+=1
    for name, rr in v['deletion_ranges'].items():
        vv=[d['metrics'][name]['suite_max_ba'] for d in v['leave_one_positive_customer_out'] if d['valid']]
        assert rr==dict(min=min(vv) if vv else None,max=max(vv) if vv else None,valid_deletions=len(vv),invalid_deletions=len(v['leave_one_positive_customer_out'])-len(vv))
receipt=dict(status='PASS',utc=dt.datetime.now(dt.timezone.utc).isoformat(),cells=12,deletions_checked=checked,
    input_records=4140,result_sha256=sha(HERE/'results.json'),freeze_sha256=sha(HERE/'freeze.json'),
    checks=['frozen code/input hashes','complete unique OOF grid','customer fold consistency','original episode BA agreement',
        'independent per-row weighting','positive-customer deletion membership and denominators','suite-max winners and ranges'],
    scope='No model fits, no new data; conditional saved-prediction sensitivity only')
(HERE/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
