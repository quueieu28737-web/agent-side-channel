from common import *
ns,tools,base,tasks=load();es=[read(p) for p in (HERE/'formal').glob('*/task-*/episode.json')]
for arm in PROMPTS:
 rows=[e for e in es if e['prompt']==arm];print(json.dumps({'prompt':arm,'known_name_dispatch':sum(c['name'] in tools for e in rows for c in e['calls']),'dispatch_attempts':sum(len(e['calls']) for e in rows),'unknown':sum(c['name'] not in tools for e in rows for c in e['calls']),'tool_errors':sum(c['err'] for e in rows for c in e['calls']),'protocol_error_episodes':sum(e['status']=='protocol_error' for e in rows)}))
for r in read(HERE/'D2_suite.json'):
 print(json.dumps({k:r[k] for k in ['prompt','target','view','suite_ba','suite_ba_ci95','suite_auroc','valid_ba_draws']}))
net=read(HERE/'network_results.json');u={(x['prompt'],x['condition']):x for x in net['utility']}
for r in net['results']:
 if r['view']=='network' and r['condition']=='shape_const':print(json.dumps({k:r[k] for k in ['prompt','target','suite_ba','suite_ba_ci95','suite_auroc','criterion','valid_ba_draws']}|{k:u[r['prompt'],r['condition']][k] for k in ['call_ratio','wire_ratio']}))
if (HERE/'constant_output_diagnostic.json').exists():print(json.dumps(read(HERE/'constant_output_diagnostic.json')['summary']))
