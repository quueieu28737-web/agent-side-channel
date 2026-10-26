"""Independently recompute current counts from the versioned row-level overlay."""
from pathlib import Path
from collections import Counter
from itertools import combinations
import csv,hashlib,json,re
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';S=P/'provenance/r19-evidence-closure'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=load(O/'analysis.json')
for n,h in a['input_sha256'].items():assert sha(P/n)==h,n
old={r['record_id']:r for r in load(S/'record-audit.json')}
current={r['record_id']:r for r in load(O/'record-audit.json')}
assert len(current)==39 and current.keys()==old.keys()
changes=rows(O/'record-cell-changes.csv');assert len(changes)==19
delta={(r['record_id'],r['item']):r for r in changes}
for rid,r in current.items():
 for k,v in old[rid].items():
  if k=='rationale':continue
  if (rid,k) in delta:assert v=='?' and r[k]==delta[rid,k]['new'] and r[k] in ['P','U']
  else:assert r[k]==v,(rid,k)
assert sum(r[f'R{i}']=='?' for r in current.values() for i in range(1,10))==6
assert rows(O/'record-audit.csv')==[{k:str(v) for k,v in r.items()} for r in current.values()]
review=load(O/'family-cell-review.json');assert len(review)==11
assert Counter(r['new'] for r in review)=={'P':4,'U':7}
assert len({(r['family'],r['item']) for r in review})==11
receipts=load(O/'source-receipts.json');assert len(receipts)==9
pins={r['version']:r for r in receipts}
for r in review:
 assert r['old']=='?' and r['retrieved_html_sha256']==pins[r['source_version']]['sha256_html']
 assert r['source_url']==pins[r['source_version']]['url'] and r['source_locator'] and r['reason']

# Read family TeX cells independently; the 180-cell display has no remaining ?.
family={}
for line in (M/'tables/family-audit-matrix.tex').read_text().splitlines():
 if r'\cite{' not in line or ' & ' not in line:continue
 cols=line.split(' & ');key=re.search(r'\\cite\{([^}]+)\}',cols[0])[1]
 family[key]=[re.sub(r'\\textbf\{([^}]+)\}',r'\1',x) for x in cols[1:10]]
assert len(family)==20 and all('?' not in x for x in family.values())
for r in review:assert family[r['family']][int(r['item'][1:])-1]==r['new']
assert Counter(v[3] for v in family.values())=={'B':4,'P':5,'U':2,'--':9},Counter(v[3] for v in family.values())
assert Counter(v[4] for v in family.values())=={'B':2,'P':2,'U':7,'--':9}
table=(M/'tables/r19-record-audit.tex').read_text()
for rid,r in current.items():
 escaped=rid.replace('-',r'-\allowbreak{}')
 line=next(x for x in table.splitlines() if x.startswith(escaped+'~') or x.startswith(escaped+'$'))
 assert line.split(' & ')[1:10]==[r[f'R{i}'] for i in range(1,10)],rid

pairs=rows(O/'pair-inventory.csv');assert pairs==rows(S/'pair-inventory.csv')
assert {frozenset((r['left_unit'],r['right_unit'])) for r in pairs}==set(map(frozenset,combinations(current,2)))
related=[r for r in pairs if r['related_subset']=='true']
assert len(pairs)==741 and len(related)==133
assert Counter(r['descriptive'] for r in related)=={'COMPATIBLE':17,'INCOMPATIBLE':105,'UNRESOLVED':11}
cohorts=load(O/'cohort-rules.json');assert len(cohorts)==9
membership={k:r['cohort'] for r in cohorts for k in r['records']}
assert len(membership)==39 and sum(r['record_count'] for r in cohorts)==39
assert sum(r['pairs'] for r in cohorts)==133 and sum(r['record_count']==1 for r in cohorts)==3
for r in cohorts:assert r['record_count']==len(r['records']) and r['pairs']==len(list(combinations(r['records'],2)))
for r in pairs:assert (membership[r['left_unit']]==membership[r['right_unit']])==(r['related_subset']=='true')
scope=rows(O/'record-scope-and-cohort.csv');assert len(scope)==39
for r in scope:assert membership[r['record_id']]==r['cohort']

qs={'inference_utility':['R7','R8'],'inference_cost':['R7','R9'],'adapted_inference':['R4','R5','R7'],
    'inference_utility_cost':['R7','R8','R9'],'adapted_inference_utility_cost':['R4','R5','R7','R8','R9']}
mit={k:r for k,r in current.items() if r['scope']=='mitigation'};assert len(mit)==33
joint=load(O/'joint-queries.json');stress=rows(O/'status-sensitivity.csv');qmembers=rows(O/'query-membership.csv')
assert len(qmembers)==165 and len(stress)==20
for q,fields in qs.items():
 eligible={k for k,r in mit.items() if all(r[f]!='-' for f in fields)}
 bound={k for k in eligible if all(mit[k][f]=='B' for f in fields)}
 x=next(r for r in joint if r['query']==q)
 assert x['eligible']==len(eligible) and x['bound']==len(bound) and set(x['bound_records'])==bound
 assert x['families']==len({mit[k]['family'] for k in bound}) and x['configurations']==len({mit[k]['configuration_group'] for k in bound})
 for r in [x for x in qmembers if x['query']==q]:
  assert (r['eligible']=='True')==(r['record_id'] in eligible)
  assert (r['bound']=='True')==(r['record_id'] in bound)
 for r in [x for x in stress if x['query']==q]:
  assert int(r['selected'])==sum(all(mit[k][f] in set(r['allowed']) for f in fields) for k in eligible)
assert [(r['bound'],r['eligible']) for r in joint]==[(4,22),(5,22),(2,17),(2,20),(0,14)]
h=load(P/'provenance/r16-synthesis/holdout-matrix.json')
expected={(r['citation_key'],axis) for r in h['rows'] for axis,v in r['axes'].items() if v=='H'}
entries=load(O/'holdout-object-ledger.json');assert len(entries)==19
assert {(r['family'],r['axis']) for r in entries}==expected
for axis in load(O/'holdout-accounting.json'):
 rr=[r for r in entries if r['axis']==axis['axis']]
 assert axis['all_H']==len(rr)
 assert axis['H_in_mitigation_families']==sum(r['family'] in {v['family'] for v in mit.values()} for r in rr)
report={'revision':'R26','passed':True,'record_cells_checked':351,'family_cells_displayed':180,
 'source_receipts':9,'family_cells_reconciled':11,'reclassified_to_partial':4,'reclassified_to_unreported':7,
 'record_cells_updated':19,'record_questions_remaining':6,'new_bound_cells':0,
 'pairs_unchanged':741,'cohort_memberships_checked':39,'question_cohorts':9,'query_memberships_checked':165,
 'strict_joins_unchanged':True,'status_scenarios_checked':20,'holdout_objects_checked':19,
 'new_experiments':0,'new_model_calls':0,'independent_human_recoding_claimed':False}
(O/'data-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(report))
