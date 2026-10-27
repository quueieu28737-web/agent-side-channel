"""Recompute R34 descriptive counts from record cells and mode/index tables.

This validates deterministic accounting, not independent source coding.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re,csv
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
d=json.loads((M/'data/reporting-patterns.json').read_text())
for f,h in d['source_sha256'].items():assert hashlib.sha256((M/f).read_bytes()).hexdigest()==h,f
rows={};modes={};added=[];context=[]
for line in (M/'tables/r19-record-audit.tex').read_text().splitlines():
 if line.count('&')<10 or r'\cite{' not in line:continue
 cols=line.split('&');rid=cols[0].split('~')[0].replace(r'\allowbreak{}','').replace(r'$\dagger$','').strip()
 f=re.search(r'\\cite\{([^}]+)\}',cols[0])[1]
 vals=[c.strip() for c in cols[1:10]]
 rows[rid]=(f,vals)
for line in (M/'tables/r9-record-index.tex').read_text().splitlines():
 if not line.startswith(r'\textsf{'):continue
 rid=re.search(r'\\textsf\{([^}]+)\}',line)[1]
 modes[rid]=line.split('&')[1].strip()
 if r'^{\dagger}' in line:added.append(rid)
 if r'^{\ddagger}' in line:context.append(rid)
assert set(rows)==set(modes) and len(rows)==39
assert len(added)==len(context)==6 and not set(added)&set(context)
mit={k:v for k,v in rows.items() if k not in context}
variants={'all':mit,'without_CachePrune':{k:v for k,v in mit.items() if v[0]!='wu2026cacheprune'},
 'without_final_search':{k:v for k,v in mit.items() if k not in added},
 'without_CachePrune_or_final_search':{k:v for k,v in mit.items() if k not in added and v[0]!='wu2026cacheprune'}}

def aggregate(records):
 out={}
 for f in sorted({v[0] for v in records.values()}):
  items=[]
  for j in range(9):
   codes={v[1][j] for v in records.values() if v[0]==f}
   items.append(next(c for c in ['B','P','?','U','A','-'] if c in codes))
  out[f]=items
 return out

checks=0
for name,rs in variants.items():
 families=aggregate(rs)
 for j in (4,5,7,8,9):
  for key,ok in [('strict',{'B'}),('partial_accepted',{'B','P'})]:
   saved=d['field_patterns'][name][f'R{j}'][key]
   eligible={f for f,v in families.items() if v[j-1]!='-'}
   bound={f for f in eligible if families[f][j-1] in ok}
   assert eligible==set(saved['eligible_ids']) and bound==set(saved['bound_ids'])
   assert (len(bound),len(eligible))==(saved['bound'],saved['eligible']);checks+=1
 for key,ok in [('strict',{'B'}),('partial_accepted',{'B','P'})]:
  ic={};sep=[]
  for f in families:
   infer={k for k,v in rs.items() if v[0]==f and v[1][6] in ok}
   cost={k for k,v in rs.items() if v[0]==f and v[1][8] in ok}
   if infer and cost:
    ic[f]=infer&cost
    if not ic[f]:sep.append(f)
  saved=d['inference_cost_conjunction'][name][key]
  assert saved['families']==len(ic) and saved['separate_only']==len(sep)
  assert all(set(r['joint'])==ic[r['family']] for r in saved['rows']);checks+=1

families=aggregate(mit)
assert [d['field_patterns']['all'][f'R{j}']['strict']['bound'] for j in (7,9,8,4,5)]==[16,11,4,4,2]
assert [d['field_patterns']['all'][f'R{j}']['partial_accepted']['bound'] for j in (7,9,8,4,5)]==[17,15,6,9,2]
same={f:v for f,v in families.items() if all(v[j-1]!='-' for j in (7,8,9))}
assert len(same)==14
for j in (7,8,9):
 for key,ok in [('strict',{'B'}),('partial_accepted',{'B','P'})]:
  saved=d['common_R7_R8_R9_families'][f'R{j}'][key]
  assert set(saved['eligible_ids'])==set(same)
  assert set(saved['bound_ids'])=={f for f,v in same.items() if v[j-1] in ok};checks+=1
for j in (4,5):
 for key in ['strict','partial_accepted']:
  broad=d['broad_adaptation_applicability'][f'R{j}'][key]
  assert broad['eligible']==20 and broad['bound']==d['field_patterns']['all'][f'R{j}'][key]['bound'];checks+=1

core={}
for line in (M/'tables/core-family-map.tex').read_text().splitlines():
 if r'\cite{' not in line or '&' not in line:continue
 cols=line.split('&');f=re.search(r'\\cite\{([^}]+)\}',cols[0])[1]
 parts=cols[1].strip(' $').split(r'\,\to\,')
 core[f]=(set(map(int,parts[0].split(','))),set(map(int,parts[1].strip(' $').split(','))),set(re.search(r'\\texttt\{([^}]+)\}',cols[2])[1].split(',')))
assert len(core)==58
agent={f for f in families if 5 in core[f][0] and core[f][2]&{'I','II'}}
assert agent==set(d['agent_privacy_attribution_utility']) and len(agent)==4
assert Counter(families[f][7] for f in agent)=={'P':2,'U':2}
for variant in variants:
 assert d['agent_sensitivity'][variant]['strict']['bound']==0
 assert d['agent_sensitivity'][variant]['partial_accepted']['bound']==2
 checks+=1
assert Counter(modes[k] for k in mit)=={'Ex':14,'Tr':6,'Si':5,'Co':6,'Un':2}
network={k for k,v in mit.items() if 3 in core[v[0]][1]}
assert len(network)==12 and Counter(modes[k] for k in network)=={'Ex':6,'Tr':4,'Un':2}
for key,ids in [('all_records',set(rows)),('mitigation',set(mit)),('network_receiver_mitigation',network),('without_final_search',set(mit)-set(added))]:
 saved=d['measurement_modes'][key];assert saved['records']==len(ids)
 assert saved['counts']==dict(Counter(modes[k] for k in ids))
 assert all(set(v)=={k for k in ids if modes[k]==mode} for mode,v in saved['ids'].items());checks+=1
groups=d['source_layer_coverage'];assert [len(v['core_ids']) for v in groups.values()]==[8,8,22,15,5]
assert [len(v['mitigation_ids']) for v in groups.values()]==[1,4,10,4,1]
assert len({k for v in groups.values() for k in v['core_ids']})==58
for g in groups.values():assert set(g['mitigation_ids'])==set(g['core_ids'])&set(families);checks+=1
type2={f for f,v in core.items() if 'II' in v[2]};assert len(type2)==13 and len(type2&set(families))==2
assert len(d['holdout_entries']['model'])==3 and len(d['holdout_entries']['harness_topology'])==2
assert len(d['holdout_entries']['task_input_user'])==13 and sum(r['mitigation_family'] for r in d['holdout_entries']['task_input_user'])==4
assert not any(r['mitigation_family'] for r in d['holdout_entries']['model'])
raw=list(csv.DictReader((M/'data/family-index.csv').open(encoding='utf8')))
for axis,entries in d['holdout_entries'].items():
 assert {r['family'] for r in entries}=={r['citation_key'] for r in raw if r[axis]=='H'};checks+=1
checks+=7
out={'status':'R34_REPORTING_ACCOUNTING_PASS','checks':checks,'source_files_hashed':len(d['source_sha256']),
     'records':39,'mitigation_records':33,'mitigation_families':20,'new_source_judgments':0,
     'scope':'Programmatic accounting and sensitivity verification; not independent coding reliability.'}
(O/'reporting-check.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(out))
