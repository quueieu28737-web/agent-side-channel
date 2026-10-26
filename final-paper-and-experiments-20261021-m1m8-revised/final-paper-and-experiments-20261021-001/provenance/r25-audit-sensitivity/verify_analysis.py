"""Verify R25 outputs directly against frozen CSVs, without importing the analysis."""
from pathlib import Path
from collections import Counter
from itertools import combinations
import csv,hashlib,json
O=Path(__file__).resolve().parent;P=O.parents[1];S=P/'provenance/r19-evidence-closure'
def csvread(f):return list(csv.DictReader(f.open(encoding='utf-8-sig',newline='')))
audit=csvread(S/'record-audit.csv');pairs=csvread(S/'pair-inventory.csv')
report=json.loads((O/'analysis.json').read_text())
for n,h in report['input_sha256'].items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
records={r['record_id']:r for r in audit};assert len(records)==39
assert {frozenset((r['left_unit'],r['right_unit'])) for r in pairs}==set(map(frozenset,combinations(records,2)))
qsets={'inference_utility':('R7','R8'),'inference_cost':('R7','R9'),
'adapted_inference':('R4','R5','R7'),'inference_utility_cost':('R7','R8','R9'),
'adapted_inference_utility_cost':('R4','R5','R7','R8','R9')}
mitig={k for k,r in records.items() if r['scope']=='mitigation'};assert len(mitig)==33
eligible={q:{k for k in mitig if '-' not in [records[k][f] for f in ff]} for q,ff in qsets.items()}
bound={q:{k for k in eligible[q] if all(records[k][f]=='B' for f in ff)} for q,ff in qsets.items()}
assert [(len(bound[q]),len(eligible[q])) for q in qsets]==[(4,22),(5,22),(2,17),(2,20),(0,14)]
assert eligible['inference_utility']!=eligible['inference_cost']
assert len(eligible['inference_utility']&eligible['inference_cost'])==20
membership=csvread(O/'query-membership.csv')
assert {(r['query'],r['record_id']) for r in membership}==set((q,k) for q in qsets for k in mitig)
assert len(membership)==165
for r in membership:
 q=r['query'];k=r['record_id']
 assert (r['eligible']=='True')==(k in eligible[q])
 assert (r['bound']=='True')==(k in bound[q])
 assert r['inapplicable_items']==','.join(f for f in qsets[q] if records[k][f]=='-')
 assert r['archived_rationale']==records[k]['rationale']
for r in csvread(O/'joint-accounting.csv'):
 q=r['query'];bb=bound[q];ee=eligible[q]
 expected={'starting_records':33,'excluded_records':33-len(ee),'eligible_records':len(ee),
 'bound_records':len(bb),'bound_families':len({records[k]['family'] for k in bb}),
 'bound_configurations':len({records[k]['configuration_group'] for k in bb}),
 'eligible_families':len({records[k]['family'] for k in ee}),
 'eligible_configurations':len({records[k]['configuration_group'] for k in ee})}
 assert all(int(r[k])==v for k,v in expected.items()),q
relaxed=csvread(O/'status-relaxation.csv');assert len(relaxed)==25
for r in relaxed:
 q=r['query'];allowed=set(r['accepted_statuses'])
 kk={k for k in eligible[q] if {records[k][f] for f in qsets[q]}<=allowed}
 assert int(r['selected_records'])==len(kk)
 assert set(r['record_ids'].split(';'))- {''}==kk
 assert int(r['families'])==len({records[k]['family'] for k in kk})
related=[r for r in pairs if r['related_subset']=='true'];same=[r for r in pairs if r['same_family']=='true']
assert Counter(r['descriptive'] for r in related)==Counter(COMPATIBLE=17,INCOMPATIBLE=105,UNRESOLVED=11)
assert report['related_unresolved_completion_range']==[17,28]
assert len(same)==15 and len({r['left_family'] for r in same})==11
assert len({r['left_family'] for r in same if r['descriptive']=='INCOMPATIBLE'})==6
for r in csvread(O/'pair-cohorts.csv'):
 rr=[x for x in related if x['cohort']==r['cohort']]
 assert int(r['pairs'])==len(rr)
 for key,status in [('compatible','COMPATIBLE'),('incompatible','INCOMPATIBLE'),('unresolved','UNRESOLVED')]:
  assert int(r[key])==sum(x['descriptive']==status for x in rr)
loo=csvread(O/'leave-family-out.csv');assert len(loo)==26
for r in loo:
 family=r['removed_family'];rr=[x for x in related if family not in (x['left_family'],x['right_family'])]
 ss=[x for x in same if family not in (x['left_family'],x['right_family'])]
 c=sum(x['descriptive']=='COMPATIBLE' for x in rr);m=sum(x['descriptive']=='INCOMPATIBLE' for x in ss)
 assert (int(r['compatible']),int(r['related_pairs']))==(c,len(rr))
 assert (int(r['same_family_incompatible']),int(r['same_family_pairs']))==(m,len(ss))
 assert abs(float(r['compatible_fraction'])-c/len(rr))<1e-12
 assert abs(float(r['same_family_incompatible_fraction'])-m/len(ss))<1e-12
jointloo=csvread(O/'joint-leave-family-out.csv');assert len(jointloo)==100
for r in jointloo:
 q=r['query'];family=r['removed_family']
 ee={k for k in eligible[q] if records[k]['family']!=family}
 bb=ee&bound[q];assert (int(r['bound_records']),int(r['eligible_records']))==(len(bb),len(ee))
 assert int(r['bound_families'])==len({records[k]['family'] for k in bb})
 assert int(r['bound_configurations'])==len({records[k]['configuration_group'] for k in bb})
cp=next(r for r in jointloo if r['query']=='inference_utility_cost' and r['removed_family']=='wu2026cacheprune')
assert (cp['bound_records'],cp['eligible_records'])==('0','18')
out={'status':'R25_ACCOUNTING_AND_SENSITIVITY_PASS','input_sha256':report['input_sha256'],
     'pairs_checked':741,'query_memberships_checked':165,'query_accounting_rows':5,
     'status_scenarios_checked':25,'pair_cohorts_checked':6,'family_deletions_checked':26,
     'joint_family_deletions_checked':100,'source_labels_changed':False,'new_experiments':0,
     'independent_human_coding_claimed':False}
(O/'data-verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(out))
