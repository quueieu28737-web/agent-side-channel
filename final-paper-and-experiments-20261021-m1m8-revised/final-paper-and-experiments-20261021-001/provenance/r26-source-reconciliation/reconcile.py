"""Versioned source reconciliation. No experimental data or historical audit is overwritten.

Judgments below are an explicit targeted reading, not an independent human recoding.
Receipts pin the retrieved official HTML; section/table anchors avoid PDF page ambiguity.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, io, itertools, json, re

O=Path(__file__).resolve().parent; P=O.parents[1]; M=P/'manuscript'
S=P/'provenance/r19-evidence-closure'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v): (O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def csvwrite(n,rows):
 with (O/n).open('w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows)
def texwrite(n,s): (M/n).write_text(s,encoding='utf8',newline='\n')
def esc(s): return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_')
receipts={r['version']:r for r in load(O/'source-receipts.json')}
# Short paraphrases of the specifically inspected reporting scopes, not claims
# that an experiment was not performed anywhere by the source authors.
specs=[
 ('whisperleak2025','Whisper Leak','2511.03675v1','3.2; 6.1-6.3; Tables 3-5; Figure 7','P','U',
  'Training and prompt splits are specified globally; padding uses new captures and batching/injection transform traces. These passages do not map protected training partitions to each mitigation result, or give clean/protected fits on identical defended tests.'),
 ('timewilltell2024','Time Will Tell','2412.15431v1','V-B; VII-B','P','U',
  'The attack fits an input-length-dependent token-count threshold. The fixed-word instruction is evaluated, but its threshold reprofiling and a paired clean/protected-fit contrast are not specified in these passages.'),
 ('wei2024speculation','Speculative decoding','2411.01076v4','4.3-4.4; 6.1; Appendix D','P','U',
  'Fingerprint profiling and padded/aggregated attack outcomes are described. The mitigation result does not identify whether reference profiles are rebuilt on protected traces, nor compare both fits on a shared defended test population.'),
 ('pouryousef2026traffic','Cloud traffic benchmark','2609.31877v1','III-C; IV; V-C1; Figure 9(a)','U','U',
  'The mitigation discussion evaluates fingerprints learned at a fixed configuration under rewritten prompts and changed temperatures. Protected-condition refitting and a matched clean/protected-fit contrast are not reported in this scope.'),
 ('chen2026sparleak','SparLeak','2609.38830v1','6; 7.1; 7.5; Table 4','P','U',
  'Profiling-based attacks and replacement-intensity ASR/ROUGE outcomes are specified. The mitigation table does not bind the attack-training distribution to each intensity or report matched clean/protected-fit tests.'),
 ('zhu2026turing','AHB','2604.09574v1','4.2.2; 5.1.2; Table 1; E.1-E.3',None,'U',
  'Different detectors on a humanization row are a detector comparison, not a clean/protected-fit contrast. The inspected paper scope and archived static call-chain review do not report that matched contrast; condition-specific code fitting remains partial run evidence.'),
]
audit=[]
for family,name,version,locator,r4,r5,note in specs:
 for item,new in [('R4',r4),('R5',r5)]:
  if new is None:continue
  audit.append({'family':family,'name':name,'item':item,'old':'?','new':new,
   'source_url':receipts[version]['url'],'source_version':version,'source_locator':locator,
   'retrieved_html_sha256':receipts[version]['sha256_html'],'reason':note,
   'scope':'Targeted reporting audit; P/U does not certify unperformed experiments or defended fitting.'})
assert len(audit)==11
csvwrite('family-cell-review.csv',audit);save('family-cell-review.json',audit)

rows=load(S/'record-audit.json'); changes=[]
byfam={a[0]:a for a in specs}
for r in rows:
 if r['family'] not in byfam:continue
 family,name,version,locator,r4,r5,note=byfam[r['family']]
 for item,new in [('R4',r4 if r4 is not None else 'P'),('R5',r5)]:
  if r[item]=='?':
   changes.append({'record_id':r['record_id'],'item':item,'old':'?','new':new,
                   'family':family,'source_locator':locator,'reason':note})
   r[item]=new
 r['rationale']+=' Targeted reread: '+note
save('record-audit.json',rows);csvwrite('record-audit.csv',rows);csvwrite('record-cell-changes.csv',changes)
# Pair membership and verdicts are untouched. Existing paired/transfer '?' are
# different questions from the family R4/R5 reporting states inspected here.
pairs=list(csv.DictReader((S/'pair-inventory.csv').open(encoding='utf-8-sig')))
csvwrite('pair-inventory.csv',pairs)
queries={'inference_utility':['R7','R8'],'inference_cost':['R7','R9'],
 'adapted_inference':['R4','R5','R7'],'inference_utility_cost':['R7','R8','R9'],
 'adapted_inference_utility_cost':['R4','R5','R7','R8','R9']}
joint=[];stress=[];members=[]
for q,fields in queries.items():
 eligible=[r for r in rows if r['scope']=='mitigation' and all(r[k]!='-' for k in fields)]
 bound=[r for r in eligible if all(r[k]=='B' for k in fields)]
 joint.append({'query':q,'eligible':len(eligible),'bound':len(bound),'families':len({r['family'] for r in bound}),
               'configurations':len({r['configuration_group'] for r in bound}),'bound_records':[r['record_id'] for r in bound]})
 for r in rows:
  if r['scope']=='mitigation':members.append({'query':q,'record_id':r['record_id'],'eligible':r in eligible,'bound':r in bound,'statuses':';'.join(k+'='+r[k] for k in fields)})
 for rule in ['B','BP','B?','BP?']:
  stress.append({'query':q,'allowed':rule,'eligible':len(eligible),'selected':sum(all(r[k] in rule for k in fields) for r in eligible)})
save('joint-queries.json',joint);csvwrite('query-membership.csv',members);csvwrite('status-sensitivity.csv',stress)

# Inventory hierarchy: each existing comparison record retains a parameter grid.
# Six question cohorts are an inclusion frame, not an equivalence judgment.
cohort_rules={
 'traffic-envelope':('What does changing the delivered traffic envelope reveal or cost?','Network/API destination, size, timing, count or delivery shaping; includes WRA destination cover, excludes cache probes and content-only identity.'),
 'cache-service':('What does shared-cache protection reveal or cost?','Cache hit/reuse probes, cache policy and its component costs; excludes local memory observation without a service-cache probe.'),
 'local-memory':('What does a local memory/resource intervention reveal or cost?','Memory access/loading/sparsity/obliviousness and associated component costs; excludes network metadata and service-cache timing probes.'),
 'behavioral-humanization':('How does humanization change behavioral inference and execution?','Site/mobile behavioral-trajectory edits or executed GUI humanization; excludes network-destination cover such as WRA.'),
 'generator-fingerprint':('How do generator or route changes affect identity recognition?','Prompt/decoding or route changes with model-identity outcomes; excludes topic/content recovery.'),
 'fixed-instruction':('What does a fixed instruction change under the stated observation?','Fixed instruction/guardrail contrasts; source target and observer still require alignment.'),
 'access-control':('Does the access gate block an agent while retaining task completion?','FP-Agent contextual gate; singleton, no related pair.'),
 'contention-noise':('Does co-running interference change covert-channel capacity?','Behind Bars contextual channel; singleton, no related pair.'),
 'filter-created-view':('Does the filter itself create a membership view?','ML privacy channels contextual filter; singleton, no related pair.'),
}
cm={}
for p in pairs:
 if p['related_subset']=='true':
  for rid in [p['left_unit'],p['right_unit']]:
   assert rid not in cm or cm[rid]==p['cohort'];cm[rid]=p['cohort']
for c,ids in load(P/'evidence/retained-release007/history-release006/decision-audit/coding.json')['cohorts'].items():
 for rid in ids:
  assert rid not in cm or cm[rid]==c;cm[rid]=c
assert len(cm)==39
cohorts=[]
for c,(question,rule) in cohort_rules.items():
 rr=[r['record_id'] for r in rows if cm[r['record_id']]==c]
 cohorts.append({'cohort':c,'question':question,'membership_rule':rule,'records':rr,'record_count':len(rr),'pairs':len(rr)*(len(rr)-1)//2})
save('cohort-rules.json',cohorts)
ledger=load(P/'experiments/reviewer-audit/combined_result_records.json')
lr={r['unit_id']:r for r in ledger['baseline_records']+ledger['added_records']}
split=[]
for r in rows:
 a=lr[r['record_id']]
 split.append({'record_id':r['record_id'],'family':r['family'],'cohort':cm[r['record_id']],
   'source_locator':r['source_locator'],'execution_or_component_scope':a.get('mode',a['scope']),
   'target_or_cost_object':a.get('inference_or_measurement_target',a['scope']),
   'configuration_package':r['configuration_group'],
   'retained_coordinates':'Models, workloads, intensities, repetitions and metrics remain source-indexed within the record; not independent record counts.',
   'split_rule':'Split on primitive, execution mode, receiver/target contract, or separately measured cost object; preserve linked outcome/cost coordinates within a record.'})
csvwrite('record-scope-and-cohort.csv',split)

# RQ3: the 82x6 matrix is a locator, not a defense-transfer count. Track what the
# reported H entry evaluates; no unstated defense condition is inherited.
h=load(P/'provenance/r16-synthesis/holdout-matrix.json')
mit={r['family'] for r in rows if r['scope']=='mitigation'}
objects=[]
for r in h['rows']:
 for axis,status in r['axes'].items():
  if status!='H':continue
  objects.append({'family_id':r['id'],'family':r['citation_key'],'name':r['name'],'axis':axis,
   'historical_status':status,'mitigation_family':r['citation_key'] in mit,
   'evaluated_object':('attack/identification generalization' if axis in ['model','harness_topology'] else 'source-qualified split; defended-condition linkage requires record-level checking'),
   'defended_holdout_binding':'not established by this H entry',
   'defense_calibration_transfer':'not established by this H entry',
   'source_locators':r['source_locators'],'source_url':r['source_url'],
   'qualification':r['interpretation']})
save('holdout-object-ledger.json',objects);csvwrite('holdout-object-ledger.csv',objects)
axes=[]
for axis in h['axes']:
 rr=[r for r in objects if r['axis']==axis]
 axes.append({'axis':axis,'all_H':len(rr),'H_in_mitigation_families':sum(r['mitigation_family'] for r in rr)})
assert [r['all_H'] for r in axes]==[13,3,2,0,1,0]
assert [r['H_in_mitigation_families'] for r in axes]==[4,0,2,0,0,0]
save('holdout-accounting.json',axes)
summary={'revision':'R26','base_commit':'b192bd593f4d6ae6a958122fe6f80ecda048df06',
 'family_cells_reviewed':11,'family_new_statuses':dict(Counter(r['new'] for r in audit)),
 'record_cells_changed':len(changes),'record_question_cells_remaining':sum(r[k]=='?' for r in rows for k in ['R'+str(i) for i in range(1,10)]),
 'records':len(rows),'pairs':len(pairs),'related_pairs':sum(p['related_subset']=='true' for p in pairs),
 'joint':joint,'holdouts':axes,'model_calls':0,'new_experiments':0,
 'input_sha256':{str(f.relative_to(P)):sha(f) for f in [S/'record-audit.json',S/'pair-inventory.csv',P/'provenance/r16-synthesis/holdout-matrix.json',O/'source-receipts.json']},
 'interpretation':'Targeted source reporting reconciliation; no independent human reliability estimate. Existing raw experiments, pair verdicts and supported B joins remain unchanged.'}
save('analysis.json',summary)

# Present current audit; the old artifacts remain immutable.
t=(M/'tables/family-audit-matrix.tex').read_text()
for family,name,version,locator,r4,r5,note in specs:
 lines=t.splitlines()
 for i,line in enumerate(lines):
  if r'\cite{'+family+'}' in line:
   cols=line.split(' & ')
   if r4 is not None:assert cols[4] in ['?',r'\textbf{P}',r4];cols[4]=r'\textbf{P}' if r4=='P' else r4
   assert cols[5] in ['?',r5];cols[5]=r5
   lines[i]=' & '.join(cols)
 t='\n'.join(lines)+'\n'
t=t.replace('?: unverified binding (11 cells)','?: unverified binding')
if 'formerly unverified family cells' not in t:t=t.replace('CachePrune jointly binds R7--R9 at one operating point.',
 'CachePrune jointly binds R7--R9 at one operating point. The 11 formerly unverified family cells have been reread: four are partial and seven unreported in the specified scope (S34). No additional B is inferred.')
texwrite('tables/family-audit-matrix.tex',t)
t=(M/'tables/r19-record-audit.tex').read_text()
for change in changes:
 rid=esc(change['record_id']).replace('-',r'-\allowbreak{}')
 lines=t.splitlines()
 for i,line in enumerate(lines):
  if line.startswith(rid+'~'):
   cols=line.split(' & ');idx=int(change['item'][1:]);assert cols[idx] in ['?',change['new']];cols[idx]=change['new'];lines[i]=' & '.join(cols)
 t='\n'.join(lines)+'\n'
t=t.replace('Source scope and join rationale','Source scope and join rationale')
t=t.replace(r'\label{tab:r19-record-cells}',r'\label{tab:r19-record-cells}')
texwrite('tables/r19-record-audit.tex',t)
print(json.dumps(summary,indent=2))
