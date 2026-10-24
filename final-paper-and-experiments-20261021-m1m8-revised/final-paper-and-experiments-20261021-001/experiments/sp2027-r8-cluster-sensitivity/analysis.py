"""Frozen, fitting-free customer sensitivity for complete saved OOF predictions."""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'sp2027-r7-crossfit'
INPUTS = ['predictions.json', 'detailed_results.json']
SOURCES = ['PROTOCOL.md', 'analysis.py', 'verify.py']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def metric(rows, attack, equal):
    strata = defaultdict(list)
    for r in rows:
        strata[(r['y'], r['customer'] if equal else '*')].append(int(r['attacks'][attack]['pred'] == r['y']))
    vals = {y: [sum(v)/len(v) for (yy, g), v in strata.items() if yy == y] for y in [0, 1]}
    if not vals[0] or not vals[1]:
        return None
    return .5 * (sum(vals[0])/len(vals[0]) + sum(vals[1])/len(vals[1]))

def counts(rows):
    by = defaultdict(set)
    for r in rows:
        by[r['customer']].add(r['y'])
    return dict(episodes=len(rows), positive_episodes=sum(r['y'] for r in rows),
        negative_episodes=sum(1-r['y'] for r in rows), customers=len(by),
        positive_customers=sum(1 in ys for ys in by.values()),
        negative_customers=sum(0 in ys for ys in by.values()),
        mixed_label_customers=sum(len(ys)==2 for ys in by.values()),
        tasks=len({r['episode'].rsplit('-r', 1)[0] for r in rows}))

def summary(rows, attacks):
    out = {}
    for label, equal in [('episode_weight', False), ('customer_equal_within_class', True)]:
        values = {a: metric(rows, a, equal) for a in attacks}
        valid = {a: v for a, v in values.items() if v is not None}
        best = max(valid.values()) if valid else None
        out[label] = dict(suite_max_ba=best, winners=[a for a, v in valid.items() if abs(v-best)<1e-12], by_attack=values)
    return out

def calculate():
    rows = read(SOURCE / 'predictions.json')
    cells = {}
    for arm in ['baseline', 'rules']:
        for cond in ['undefended', 'jointbucket1024', 'jointconstant']:
            for target in ['cancel', 'return']:
                key = '|'.join([arm, cond, target])
                rr = [r for r in rows if (r['prompt'], r['condition'], r['target']) == (arm, cond, target)]
                assert len(rr)==345 and len({r['episode'] for r in rr})==345
                attacks = sorted(rr[0]['attacks'])
                assert len(attacks)==11 and all(sorted(r['attacks'])==attacks for r in rr)
                assert all(r['attacks'][a]['pred'] in [0, 1] for r in rr for a in attacks)
                base = summary(rr, attacks)
                strata = []
                for customer in sorted({r['customer'] for r in rr}):
                    for y in [0, 1]:
                        ss = [r for r in rr if r['customer']==customer and r['y']==y]
                        if ss:
                            strata.append(dict(customer=customer, true_class=y, episodes=len(ss),
                                correct_rate={a: sum(r['attacks'][a]['pred']==y for r in ss)/len(ss) for a in attacks}))
                deletions = []
                for customer in sorted({r['customer'] for r in rr if r['y']==1}):
                    keep = [r for r in rr if r['customer'] != customer]
                    stats = summary(keep, attacks)
                    deletions.append(dict(removed_customer=customer, remaining=counts(keep),
                        valid=stats['episode_weight']['suite_max_ba'] is not None, metrics=stats))
                ranges = {}
                for metric_name in base:
                    vv = [v['metrics'][metric_name]['suite_max_ba'] for v in deletions if v['valid']]
                    ranges[metric_name] = dict(min=min(vv) if vv else None, max=max(vv) if vv else None,
                        valid_deletions=len(vv), invalid_deletions=len(deletions)-len(vv))
                folds = {c: sorted({r['fold'] for r in rr if r['customer']==c}) for c in sorted({r['customer'] for r in rr})}
                assert all(len(v)==1 for v in folds.values())
                cells[key] = dict(denominators=counts(rr), attacks=attacks, metrics=base,
                    customer_class_strata=strata, customer_folds=folds,
                    leave_one_positive_customer_out=deletions, deletion_ranges=ranges)
    return dict(scope='Post hoc deterministic sensitivity conditional on saved fitted OOF predictions; no new customers or retraining uncertainty',
        mixed_label_rule='Customer equal independently within true class; mixed customers contribute to each class stratum',
        frozen_sha256=sha(HERE/'freeze.json'), cells=cells)

def report(result):
    lines = ['# R8 cluster sensitivity', '', result['scope'], '',
        'Customer-equal BA weights each customer equally within each true class; mixed-label customers contribute separately to both class rates. Deletions remove the entire positive customer, including its negative tasks. Ranges are influence ranges, not confidence intervals.', '',
        '| Prompt / condition | Target | Episodes / customers | Positive episodes / customers | Mixed customers | Episode suite BA % | Customer-equal suite BA % | LOO-positive episode BA range % | LOO-positive customer-equal BA range % | Valid deletions |',
        '|---|---|---|---|---:|---:|---:|---|---|---:|']
    for k, v in result['cells'].items():
        arm, cond, target = k.split('|'); d=v['denominators']; m=v['metrics']; r=v['deletion_ranges']
        def ran(name):
            z=r[name]
            return f"{100*z['min']:.4f}–{100*z['max']:.4f}" if z['min'] is not None else 'invalid'
        lines.append(f"| {arm} / {cond} | {target} | {d['episodes']} / {d['customers']} | {d['positive_episodes']} / {d['positive_customers']} | {d['mixed_label_customers']} | {100*m['episode_weight']['suite_max_ba']:.4f} | {100*m['customer_equal_within_class']['suite_max_ba']:.4f} | {ran('episode_weight')} | {ran('customer_equal_within_class')} | {r['episode_weight']['valid_deletions']} |")
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('action', choices=['freeze','run']); args=ap.parse_args()
    if args.action=='freeze':
        assert not (HERE/'freeze.json').exists() and not (HERE/'results.json').exists()
        write(HERE/'freeze.json', dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            source_sha256={n:sha(HERE/n) for n in SOURCES},
            input_sha256={n:sha(SOURCE/n) for n in INPUTS}, results_present=False,
            scope='Internal post hoc analysis freeze before executing these new sensitivity calculations; original test predictions already public'))
        print('FROZEN', sha(HERE/'freeze.json'))
    else:
        f=read(HERE/'freeze.json')
        assert f['source_sha256']=={n:sha(HERE/n) for n in SOURCES}
        assert f['input_sha256']=={n:sha(SOURCE/n) for n in INPUTS}
        assert not (HERE/'results.json').exists(), 'Do not overwrite completed sensitivity'
        result=calculate(); write(HERE/'results.json',result); report(result)
        print('COMPLETED',len(result['cells']),'cells; no fitting or LLM requests')
