"""Formatting-only compact manifest and paper tables, from saved analysis JSON."""
from common import *
from collections import Counter

def main():
 s=read(HERE/'formal_summary.json');plan=read(HERE/'formal_plan.json');net=read(HERE/'network_results.json');d2=read(HERE/'D2_suite.json');diag=read(HERE/'constant_output_diagnostic.json')
 utility={(r['prompt'],r['condition']):r for r in net['utility']};rows=[read(p) for p in (HERE/'formal').glob('*/task-*/episode.json')]
 ns,tools,base,tasks=load();per={}
 for arm in PROMPTS:
  es=[r for r in rows if r['prompt']==arm];errors=[read(p) for p in (HERE/'formal'/arm).rglob('infrastructure_error.json')]
  per[arm]=dict(s[arm+'_all'],real_tool_calls=sum(c['name'] in tools for r in es for c in r['calls']),tool_dispatch_attempts=sum(len(r['calls']) for r in es),unknown_tool_attempts=sum(c['name'] not in tools for r in es for c in r['calls']),tool_error_calls=sum(c['err'] for r in es for c in r['calls']),infrastructure_attempt_errors=len(errors),timeout_attempt_errors=sum('timeout' in r['error'].lower() for r in errors),automatic_retries=0,protocol_error_episodes=sum(r['status']=='protocol_error' for r in es),reward_failure_episodes=sum(not r['native_reward'] for r in es))
 from evaluate_d2 import ev
 view_counts={}
 for arm in PROMPTS:
  for part,ids in [('all',plan['train']+plan['test']),('train',plan['train']),('test',plan['test'])]:
   cs=[c for r in rows if r['prompt']==arm and r['task'] in ids for c in r['calls']]
   for view in ['all','writes-only','reads-only']:
    keep=lambda c:view=='all' or (view=='writes-only' and c['name'] in ev.WRITES) or (view=='reads-only' and c['name'].startswith(('get_','find_','list_')))
    retained=[c for c in cs if keep(c)];excluded=[c for c in cs if not keep(c)]
    view_counts[arm+'_'+part+'_'+view]={'prompt':arm,'partition':part,'view':view,'total_call_attempts':len(cs),'retained_calls':len(retained),'excluded_calls':len(excluded),'retained_names':dict(Counter(c['name'] for c in retained)),'excluded_names':dict(Counter(c['name'] for c in excluded))}
 write(HERE/'D2_view_call_counts.json',{'definition':'reads-only keeps get_/find_/list_ only, not the full no_writes complement; do not equate with Sol E12 writes-removed','counts':view_counts})
 targets={}
 for name,bit in [('cancel',1),('return',2)]:
  targets[name]={}
  for part in ['train','test']:
   ts=[r for r in plan['tasks'] if r['partition']==part]
   targets[name][part]={'positive_tasks':sum(bool(r['label']&bit) for r in ts),'positive_customers':len(set(r['customer'] for r in ts if r['label']&bit)),'tasks':len(ts),'customers':len(set(r['customer'] for r in ts))}
 network=[]
 for r in net['results']:
  if r['view']!='network':continue
  u=utility[r['prompt'],r['condition']]
  network.append({k:r[k] for k in ['target','prompt','condition','suite_ba','suite_ba_ci95','suite_auroc','suite_auroc_ci95','criterion','valid_ba_draws','valid_auroc_draws']}|{k:u[k] for k in ['call_ratio','wire_ratio','mean_calls','mean_wire_bytes','cover_error_rate','template_overflow_rate','template_underfill_rate','framing_overflow_session_rate']})
 files=['public_d2_validation.json','verify_public_d2.py','PACKAGING_AMENDMENT.json','PACKAGING_FAILURE.md','package_raw_v2.py','authentication_status.json','formal_plan.json','APPENDED_ANALYSIS_FREEZE.json','formal_collection.json','formal_summary.json','formal_validation.json','formal_validation_corrected.json','decision_alignment.json','public_decision_alignment.json','public_validation.json','public_validation_corrected.json','public_network_validation.json','D2_view_call_counts.json','D2_suite.json','D2_results.json','D2_predictions.json','network_results.json','network_predictions.json','network_calibration.json','raw_archive.json','raw_evidence_inventory.json','PUBLIC_REDACTION.json','constant_output_diagnostic.json','dependency_versions_full.json','requirements-public.txt']
 depdir=HERE.parents[1]/'provenance'/'r7-review'/'portable-verification'
 dependency={n:{'path':str((depdir/n).relative_to(HERE.parents[1])).replace(chr(92),'/'),'sha256':sha(depdir/n)} for n in ['luna-dependency-closure.json','luna-dependency-receipt.json','luna_dependency_check.py']}
 manifest={'benchmark_dependency_authority':dependency,'model':'gpt-6-luna','returned_alias':'gpt-6-luna','authentication_status':read(HERE/'authentication_status.json'),'reasoning_effort':'low','selection':'convenience subset: first 29 inherited train excluding pilot 0..4 plus all 46 inherited test; no new customers','counter_semantics':{'real_tool_calls':'Legacy field: known-name dispatch attempts, including env.step errors; not successful executions','tool_dispatch_attempts':'All recorded non-respond dispatch attempts, including unknown/errors','network_call_ratio':'Test aggregate dispatch records ratio, including unknown/errors/cover, not successful executions','public_reproduction':'Public ZIP model evidence plus pinned checkout/vendor/tasks/tools/helpers and dependencies; ZIP is not self-contained'},'formal_runs':len(rows),'pilot_runs_excluded':10,'per_prompt':per,'target_counts':targets,'D2_view_call_counts':view_counts,'D2_dispatch_suite':d2,'network_suite':network,'gboost_constant_diagnostic':diag['summary'],'publication_redaction':'Only Windows HOME prefixes/spelling/aliases replaced in publication copies; original scientific files unchanged; see PACKAGING_AMENDMENT and PUBLIC_REDACTION','raw_archive':read(HERE/'raw_archive.json'),'artifacts':{n:sha(HERE/n) for n in files},'timing':'Appended algorithm/config freeze at 44/150 before test outputs; calibration parameters fit after all 150 collection using training only'}
 write(HERE/'compact_manifest.json',manifest)
 fmt=lambda x:f'{x:.3f}';ci=lambda x:f'[{x[0]:.3f}, {x[1]:.3f}]'
 lines=['# Luna extension compact tables','','Model requested/returned: gpt-6-luna; effort low. 150 runs=75 existing tasks x2 prompts, one repetition; convenience subset, 34 existing customers. Ten pilot runs excluded.','','| Prompt | Reward | Wallclock p50/p95 s | Known-name dispatch/model calls | Tool errors | Infra/timeout/retry |','|---|---:|---:|---:|---:|---:|']
 for arm,v in per.items():lines.append(f"| {arm} | {v['reward_sum']}/{v['runs']} | {v['median_episode_seconds']:.2f}/{v['p95_episode_seconds']:.2f} | {v['real_tool_calls']}/{v['model_calls']} | {v['tool_error_calls']} | {v['infrastructure_attempt_errors']}/{v['timeout_attempt_errors']}/0 |")
 lines+=['','Known-name dispatch attempts include env.step errors; they are not successful executions. Total dispatch/unknown counts are separate in compact_manifest.json. Network dispatch ratios include unknown/errors/cover. Public ZIP recomputation requires the fixed checkout/vendor benchmark and pinned dependencies; ZIP alone is not self-contained.','','D2 dispatch suite: majority/logreg/gboost; per prompt 29 train/46 test, 10/24 customers. Test positive customer clusters 5 cancel/7 return. Max reselected each customer bootstrap draw; fixed fit uncertainty excluded.','','| Target | Prompt | View | BA [95% CI] | AUROC | Valid draws |','|---|---|---|---|---:|---:|']
 for r in d2:lines.append(f"| {r['target']} | {r['prompt']} | {r['view']} | {fmt(r['suite_ba'])} {ci(r['suite_ba_ci95'])} | {fmt(r['suite_auroc'])} | {r['valid_ba_draws']}/2000 |")
 lines+=['','Network suite: full inherited fixed R4 family on local TLS replay. Defense calibration pools 58 train trajectories; each attacker fits 29 per prompt. No live replan/provider-transport claim.','','| Target | Prompt | Condition | BA [95% CI] | AUROC | Dispatch/wire ratio | Criterion |','|---|---|---|---|---:|---:|---|']
 for r in network:lines.append(f"| {r['target']} | {r['prompt']} | {r['condition']} | {fmt(r['suite_ba'])} {ci(r['suite_ba_ci95'])} | {fmt(r['suite_auroc'])} | {r['call_ratio']:.2f}/{r['wire_ratio']:.2f} | {r['criterion']} |")
 lines+=['','Luna reads-only keeps get_/find_/list_ only. It differs from Sol E12 no_writes complement; think/calculate/handoff/unknown tools can be outside both Luna read/write views. All retained/excluded tool names and counts are saved in D2_view_call_counts.json.','','Gradient boosting default min_samples_leaf 20; 29 training rows cannot form two leaves. Actual per-entry constant-score fractions: '+json.dumps({k:v for k,v in diag['summary'].items() if 'gboost' in k})+'.','', 'Algorithm/config frozen before test outputs; fitted calibration parameters computed after complete collection on training only. No cross-provider/new-customer/independent-human validation claim.']
 (HERE/'COMPACT_TABLES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('COMPACT_MANIFEST_READY')
if __name__=='__main__':main()










