"""Independent R8 table source/denominator review; no source-table writes."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

O=Path(__file__).resolve().parent;P=O.parents[1];E=P/'experiments';M=P/'manuscript'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(O/'make_tables.py'),'--check'],check=True)
r4=read(E/'sp2027-r4-full-20261023/results.json')
r6=read(E/'sp2027-r6-timing/results.json')
r7=read(E/'sp2027-r7-robustness/results.json')
common=read(E/'sp2027-r7-robustness/common-suite.json')
cross=read(E/'sp2027-r7-crossfit/detailed_results.json')
audit=read(O/'defense-self-audit.json')
cohorts=(M/'tables/r8-cohorts.tex').read_text()
u9=next(r for r in r4['utility'] if r['prompt']=='baseline' and r['condition']=='shape_const')
u10=next(r for r in cross['results'] if r['prompt']=='baseline' and r['condition']=='jointconstant' and r['target']=='cancel')
u13=r6['resources']['baseline|shadow_serial']
source_rows={
 'E9':dict(bytes_ratio=u9['wire_ratio'],calls_ratio=u9['call_ratio'],episodes_both_prompts=276,
    customers=24,positive_customers=[5,7],source='sp2027-r4-full-20261023/results.json / utility baseline shape_const; results baseline raw network',
    raw_ba=[next(r['suite_ba'] for r in r4['results'] if r['prompt']=='baseline' and r['condition']=='raw' and r['view']=='network' and r['target']==t) for t in ['cancel','return']]),
 'E10':dict(bytes_ratio=u10['bytes_ratio'],calls_ratio=u10['calls_ratio'],episodes_both_prompts=690,
    customers=53,positive_customers=[14,18],source='sp2027-r7-crossfit/detailed_results.json / baseline jointconstant and undefended cells',
    raw_ba=[next(r['suite_ba'] for r in cross['results'] if r['prompt']=='baseline' and r['condition']=='undefended' and r['target']==t) for t in ['cancel','return']]),
 'E13/14':dict(bytes_ratio=u13['wire_ratio'],calls_ratio=u13['call_ratio'],episodes_both_prompts=276,
    customers=24,positive_customers=[5,7],source='sp2027-r6-timing/results.json / resources baseline shadow_serial; E14 union raw cells',
    raw_ba=[r7['cells'][f'baseline|raw|{t}']['ba']['point'] for t in ['cancel','return']]),
}
for name,r in source_rows.items():
    line=next(s for s in cohorts.splitlines() if s.startswith(name+' &'))
    parts=[s.strip().split('\\')[0] for s in line.split('&')]
    assert parts[2]=='/'.join(f'{100*v:.1f}' for v in r['raw_ba']), (name,parts)
    assert parts[3]==f"{r['bytes_ratio']:.2f}", (name,parts)
assert '5.04' in cohorts and '3.83' in cohorts
assert f"{u10['calls_ratio']:.2f}"=='5.04' and f"{u9['call_ratio']:.2f}"==f"{u13['call_ratio']:.2f}"=='3.83'
assert all(s in cohorts for s in ['276 test episodes, 24 customers, 5/7 positive customers','690 episodes, 53 customers, 14/18 positive customers'])

keys=['raw','padding','shadow_serial','shadow_parallel2','tunnel_2ms','tunnel_5ms','bucket1024','tamaraw','tamaraw_fast','front','wtfpad','walkie_talkie','front_shift']
control_rows=[l for l in (M/'tables/r8-controls.tex').read_text().splitlines() if l.startswith(('M &','S &'))]
assert len(control_rows)==13
for cond,line in zip(keys,control_rows):
    parts=[x.strip().removesuffix('\\\\') for x in line.split('&')]
    cc=[common['cells'][f'baseline|{cond}|{t}'] for t in ['cancel','return']]
    uu=[r7['cells'][f'baseline|{cond}|{t}'] for t in ['cancel','return']]
    assert parts[2]=='/'.join(f"{100*v['ba']['point']:.1f}" for v in cc)
    assert parts[3]=='/'.join(f"{100*v['ba']['point']:.1f}" for v in uu)
    assert parts[4]=='/'.join(f"{100*v['ba']['ci95'][1]:.1f}" for v in uu)
    cost=r7['resources']['baseline|'+cond]
    assert parts[5]==f"{cost['wire_ratio']:.2f}" and parts[6]==f"{cost['call_ratio']:.2f}"
    assert parts[7]==(f"{cost['last_real_p95_ms']:.1f}" if parts[0]=='M' else '--')
    assert all(v['suite_size']==7 for v in cc)
    assert all(17<=v['suite_size']<=22 for v in uu) if parts[0]=='M' else all(v['suite_size']==7 for v in uu)

flush_rows=[l for l in (M/'tables/r8-flush.tex').read_text().splitlines() if l.startswith(('Standard &','Rules &'))]
assert len(flush_rows)==4
for (arm,cond),line in zip([(a,c) for a in ['baseline','rules'] for c in ['shadow_serial','shadow_parallel2']],flush_rows):
    parts=[x.strip().removesuffix('\\\\') for x in line.split('&')]
    for index,target in enumerate(['cancel','return']):
        key=f'{arm}|{cond}|flush_stripped_joint|{target}'
        v=r6['cells'][key]['ba']
        assert v==audit['saved_flush_then_intent'][key]['ba']
        expected=f"{100*v['point']:.1f} [{100*v['ci95'][0]:.1f}, {100*v['ci95'][1]:.1f}]"
        assert parts[2+index]==expected

# Compare generated supplementary text without overwriting any manuscript file.
generated={}
def capture(path,data,**kwargs):
    assert path.resolve()==(M/'sections/47-r8-empirical-audit.tex').resolve()
    generated['text']=data
    return len(data)
with patch.object(Path,'write_text',capture),redirect_stdout(io.StringIO()):
    runpy.run_path(str(O/'build_empirical_audit.py'),run_name='__main__')
assert generated['text']==(M/'sections/47-r8-empirical-audit.tex').read_text(encoding='utf-8')

inputs=['experiments/sp2027-r4-full-20261023/results.json','experiments/sp2027-r6-timing/results.json',
 'experiments/sp2027-r7-robustness/results.json','experiments/sp2027-r7-robustness/common-suite.json',
 'experiments/sp2027-r7-crossfit/detailed_results.json','experiments/sp2027-r8-cluster-sensitivity/results.json',
 'provenance/r8-review/defense-self-audit.json','provenance/r8-review/make_tables.py','provenance/r8-review/build_empirical_audit.py',
 'manuscript/tables/r8-cohorts.tex','manuscript/tables/r8-controls.tex','manuscript/tables/r8-flush.tex','manuscript/sections/47-r8-empirical-audit.tex']
report=dict(status='PASS',cohort_sources=source_rows,control_rows_checked=13,flush_rows_checked=4,
 supplement_generator_exact_match=True,make_tables_check='PASS',
 findings=[
 'No numerical column swaps or incorrect rounding found in requested tables.',
 'Cohort raw BA and byte ratio are distinct estimands, not a same-condition raw-cost pair: the caption correctly says byte ratios price joint constant shaping.',
 'E9 15.39 and E13 15.11 are not contradictory: different RPC serialization/envelope and each own undefended denominator.',
 'E10 19.76/5.04 uses fold-specific analytic calibration on 345 trajectories per prompt, not measured E13 timing or E9 pretest template.',
 'Cohort sample counts cover both prompts, but BA/byte/call values are standard prompt; positive customers are unique shared customers, not doubled with prompt.',
 'r8-controls upper BA is the full-union upper 95% bound; common-seven and full-union columns are correctly distinct.',
 'S simulated rows correctly omit RPC latency; M p95 is last real response, excluding planner/WAN and excluding tail drain.',
 'Flush table uses the 138-episode-per-prompt intent task after estimated removal, not 15278 record-level detector BA.',
 '47 matches its generator exactly; cluster table uses 345 trajectories/53 customers, not 345 independent customers.'],
 limitations='This numerical review does not rerun the science verifier or model fitting. It validates saved-result mappings, units and generated text.',
 sha256={n:sha(P/n) for n in inputs},review_code_sha256=sha(Path(__file__)))
(O/'numerical-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
lines=['# R8 numerical review','','PASS: make_tables --check; 13 control rows, 4 flush rows, exact supplementary generator match.','']
for n,r in source_rows.items():
    lines.append(f"- {n}: bytes {r['bytes_ratio']:.12f}; calls {r['calls_ratio']:.12f}; raw BA {r['raw_ba']}; source {r['source']}.")
lines+=['']+['- '+s for s in report['findings']]+['',report['limitations']]
(O/'numerical-review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','cohort_sources','control_rows_checked','flush_rows_checked','supplement_generator_exact_match']},indent=2))
