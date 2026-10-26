"""Deterministic sensitivity of archived judgments; no recoding or new experiments."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json

O=Path(__file__).resolve().parent;P=O.parents[1]
S=P/'provenance/r19-evidence-closure'
QUERIES={
 'inference_utility':['R7','R8'],
 'inference_cost':['R7','R9'],
 'adapted_inference':['R4','R5','R7'],
 'inference_utility_cost':['R7','R8','R9'],
 'adapted_inference_utility_cost':['R4','R5','R7','R8','R9'],
}
RELAXATIONS={'B':'B','B_P':'BP','B_question':'B?',
             'B_P_question':'BP?','all_nonmissing_statuses':'BP?U'}
def read(name):return list(csv.DictReader((S/name).open(encoding='utf-8-sig',newline='')))
def save(name,v):(O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def write(name,rows):
 with (O/name).open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def frac(n,d):return n/d if d else None

def analyze():
 rows=read('record-audit.csv');pairs=read('pair-inventory.csv')
 mitig=[r for r in rows if r['scope']=='mitigation']
 related=[r for r in pairs if r['related_subset']=='true']
 same=[r for r in pairs if r['same_family']=='true']
 assert len(rows)==39 and len(mitig)==33 and len(pairs)==741
 assert len({r['record_id'] for r in rows})==39
 assert len({tuple(sorted((r['left_unit'],r['right_unit']))) for r in pairs})==741
 memberships=[];joins=[];relax=[]
 for q,fields in QUERIES.items():
  eligible=[r for r in mitig if all(r[k]!='-' for k in fields)]
  bound=[r for r in eligible if all(r[k]=='B' for k in fields)]
  joins.append({'query':q,'required_items':','.join(fields),'starting_records':33,
   'excluded_records':33-len(eligible),'eligible_records':len(eligible),
   'bound_records':len(bound),'bound_families':len({r['family'] for r in bound}),
   'bound_configurations':len({r['configuration_group'] for r in bound}),
   'eligible_families':len({r['family'] for r in eligible}),
   'eligible_configurations':len({r['configuration_group'] for r in eligible})})
  for r in mitig:
   excluded=[k for k in fields if r[k]=='-']
   memberships.append({'query':q,'record_id':r['record_id'],'family':r['family'],
    'configuration_group':r['configuration_group'],'required_items':','.join(fields),
    'item_statuses':';'.join(k+'='+r[k] for k in fields),
    'eligible':not excluded,'bound':r in bound,
    'inapplicable_items':','.join(excluded),'source_locator':r['source_locator'],
    'archived_rationale':r['rationale']})
  for rule,allowed in RELAXATIONS.items():
   selected=[r for r in eligible if all(r[k] in allowed for k in fields)]
   relax.append({'query':q,'rule':rule,'accepted_statuses':allowed,'eligible_records':len(eligible),
    'selected_records':len(selected),'families':len({r['family'] for r in selected}),
    'configurations':len({r['configuration_group'] for r in selected}),
    'record_ids':';'.join(r['record_id'] for r in selected)})
 cohorts=[]
 for cohort in sorted({r['cohort'] for r in related}):
  rr=[r for r in related if r['cohort']==cohort];c=Counter(r['descriptive'] for r in rr)
  cohorts.append({'cohort':cohort,'pairs':len(rr),'compatible':c['COMPATIBLE'],
   'incompatible':c['INCOMPATIBLE'],'unresolved':c['UNRESOLVED']})
 loo=[];joint_loo=[]
 for family in sorted({r['family'] for r in rows}):
  rr=[r for r in related if family not in (r['left_family'],r['right_family'])]
  ss=[r for r in same if family not in (r['left_family'],r['right_family'])]
  c=Counter(r['descriptive'] for r in rr);sc=Counter(r['descriptive'] for r in ss)
  loo.append({'removed_family':family,'related_pairs':len(rr),'compatible':c['COMPATIBLE'],
   'unresolved':c['UNRESOLVED'],'compatible_fraction':frac(c['COMPATIBLE'],len(rr)),
   'same_family_pairs':len(ss),'same_family_incompatible':sc['INCOMPATIBLE'],
   'same_family_incompatible_fraction':frac(sc['INCOMPATIBLE'],len(ss))})
  if family not in {r['family'] for r in mitig}:continue
  for q,fields in QUERIES.items():
   ee=[r for r in mitig if r['family']!=family and all(r[k]!='-' for k in fields)]
   bb=[r for r in ee if all(r[k]=='B' for k in fields)]
   joint_loo.append({'removed_family':family,'query':q,'eligible_records':len(ee),
    'bound_records':len(bb),'bound_families':len({r['family'] for r in bb}),
    'bound_configurations':len({r['configuration_group'] for r in bb})})
 c=Counter(r['descriptive'] for r in related)
 def span(key):return [min(r[key] for r in loo),max(r[key] for r in loo)]
 result={'revision':'R25-audit-sensitivity','base_commit':'5db4235ed1e8e9d152c7cb9b98587ebf5ca5d916',
  'input_sha256':{n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['record-audit.csv','pair-inventory.csv']},
  'no_new_experiments':True,'archived_labels_changed':False,
  'records':39,'mitigation_records':33,'contextual_records':6,'all_pairs':741,
  'related_pairs':len(related),'related_verdicts':dict(c),
  'related_unresolved_completion_range':[c['COMPATIBLE'],c['COMPATIBLE']+c['UNRESOLVED']],
  'same_family_pairs':len(same),'same_family_families':len({r['left_family'] for r in same}),
  'same_family_incompatible_pairs':sum(r['descriptive']=='INCOMPATIBLE' for r in same),
  'same_family_incompatible_families':len({r['left_family'] for r in same if r['descriptive']=='INCOMPATIBLE'}),
  'leave_family_out_compatible_fraction_range':span('compatible_fraction'),
  'leave_family_out_same_family_incompatible_fraction_range':span('same_family_incompatible_fraction'),
  'joins':joins,'cohorts':cohorts,
  'interpretation':'Finite-corpus bookkeeping and counterfactual status-rule sensitivity, not sampling confidence, independent coder agreement, or framework validation. All source labels and cohort assignments remain unchanged. Relaxing P or ? or U is not evidence that the original same-configuration claim holds; P can encode a known incomplete or mismatched binding. Only B is treated as supported. U remains unreported under the archived reading scope.'}
 write('query-membership.csv',memberships);write('joint-accounting.csv',joins)
 write('status-relaxation.csv',relax);write('pair-cohorts.csv',cohorts)
 write('leave-family-out.csv',loo);write('joint-leave-family-out.csv',joint_loo)
 save('analysis.json',result)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 print('STATUS_RELAXATION')
 for r in relax:print(r['query'],r['rule'],r['selected_records'],r['eligible_records'])
if __name__=='__main__':analyze()
