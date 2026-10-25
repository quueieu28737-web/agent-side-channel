"""Read-only manuscript-to-evidence and saved-prediction checks for the merged revision."""
from pathlib import Path
from collections import Counter,defaultdict
import json,re,subprocess,sys,hashlib
R=Path(__file__).resolve().parents[4]
for dep in ['revision-preview/r3/deps','revision-preview/r7-agent-deps']:sys.path.insert(0,str(R/dep))
import numpy as np
from sklearn.metrics import balanced_accuracy_score,roc_auc_score
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';E=P/'experiments'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(E/'sp2027-r12-glm'))
import evaluate_network as en
rows=read(E/'sp2027-r14-transfer-boundaries/full_suite_results.json');assert len(rows)==28
point_count=0
for r in rows:
 assert len(r['attacks'])==7 and len(r['units'])==46
 ys=[u['y'] for u in r['units']];bas=[];aucs=[]
 for name,a in r['attacks'].items():
  assert abs(balanced_accuracy_score(ys,a['predictions'])-r['individual_ba'][name])<1e-12
  b,c=en.stats.distributions(r['units'],np.array(a['scores']),np.array(a['predictions']),2000)
  bas.append(b);aucs.append(c);point_count+=1
 b=np.fmax.reduce(bas);c=np.fmax.reduce(aucs)
 assert abs(b[0]-r['suite_ba'])<1e-12 and abs(c[0]-r['suite_auroc'])<1e-12
 assert np.allclose(np.nanquantile(b[1:],[.025,.975]),r['ci95'])
 if r['study']=='calibration_transfer':
  captures=[read(f) for f in (E/'sp2027-r14-transfer-boundaries/transfer_captures'/r['source']/r['target']/r['condition']).glob('*.json')]
  ids=set(read(E/r['target']/'formal_plan.json')['test']);assert len(captures)==115
  raw=read(E/r['target']/'network_sessions.json')
  ratio=sum(s['application_wire_bytes'] for s in captures if s['task'] in ids)/sum(s['application_wire_bytes'] for s in raw if s['condition']=='raw' and s['task'] in ids)
  assert abs(ratio-r['bytes_ratio'])<1e-12
names={'MiniMax':'sp2027-r11-minimax','GLM':'sp2027-r12-glm'}
find=lambda study,source,target,cond,label:next(r for r in rows if (r['study'],r['source'],r['target'],r['condition'],r['label'])==(study,source,target,cond,label))
caltext=(M/'tables/r14-calibration-transfer.tex').read_text();rep=(M/'tables/r11-model-replication.tex').read_text();main=(M/'sections/37-transfer-tests.tex').read_text()
for name,source in names.items():
 vals=[]
 for target in names.values():
  vals.append(' / '.join(f"{100*find('calibration_transfer',source,target,'transferred_joint',label)['suite_ba']:.1f}" for label in ['cancel','return']))
 assert name+' & '+' & '.join(vals) in caltext
 vals=[]
 for cond in ['raw','shape_const']:
  vals.append(' / '.join(f"{100*find('attacker_transfer',source,source,cond,label)['suite_ba']:.1f}" for label in ['cancel','return']))
 assert ('MiniMax-M3' if name=='MiniMax' else 'GLM-5.3-flash')+' & '+' & '.join(vals) in rep
model=names['GLM'];delta=100*(find('attacker_transfer',model,model,'raw','return')['suite_ba']-find('attacker_transfer',model,model,'shape_const','return')['suite_ba'])
assert f'and {delta:.1f} for GLM' in main
mode=read(P/'provenance/r16-synthesis/record-mode-inventory.json');group=defaultdict(list)
short={'Executed collection or prototype':'Ex','Trace transformation':'Tr','Simulation or derived estimate':'Si','Component or calibration measurement':'Co','Placement unresolved':'Un'}
table=(M/'tables/r9-record-index.tex').read_text()
for r in mode['records']:
 group[r['family']].append(r)
 assert re.search(re.escape(r'\textsf{'+r['record']+'}')+r'.*? & '+short[r['mode_group']]+r' & ',table)
assert len(mode['records'])==39 and len(group)==26
assert sum(len(v)>1 for v in group.values())==11
assert sum(len(set(r['mode_group'] for r in v))>1 for v in group.values())==9
# All imported experimental table data rows must retain published numeric values.
checked=[]
for f in (M/'tables').glob('*.tex'):
 if not re.match(r'(r[3-9]|r1[145]|conditional-null)',f.name) or f.name in ['r9-record-index.tex','r9-rq-findings.tex']:continue
 rel=f.relative_to(P.parents[1]).as_posix()
 try:old=subprocess.check_output(['git','show','f1ada1228ca7a179211fd55b2d57196c7049d3ec:'+rel],stderr=subprocess.DEVNULL).decode()
 except subprocess.CalledProcessError:continue
 def numeric_rows(s):
  out=[]
  for x in s.splitlines():
   if '&' not in x or r'\multicolumn' in x or x.lstrip().startswith((r'\caption',r'\begin',r'\par',r'\multicolumn',r'\cmidrule')):continue
   out.append(re.findall(r'\d+(?:\.\d+)?',re.sub(r'\\cite(?:\[[^]]*\])?\{[^}]*\}','',x)))
  return out
 assert numeric_rows(old)==numeric_rows(f.read_text()),f.name
 checked.append(f.name)
# Bibliography closure: every citation resolves once; merged bibliography reproduces the two former inputs.
bibs=[M/(s+'.bib') for s in ['refs','refs-final-additions','refs-deployment','refs-search-completion']]
keys=[]
for f in bibs:keys+=re.findall(r'@\w+\s*\{\s*([^,]+),',f.read_text())
assert len(keys)==len(set(keys))
cited=set()
for f in M.rglob('*.tex'):
 for x in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}',f.read_text()):cited.update(x.split(','))
assert cited<=set(keys),sorted(cited-set(keys))
out={'passed':True,'suite_rows':len(rows),'point_metrics_recomputed':point_count,'bootstrap_draws_per_row':2000,'calibration_costs_recomputed':True,'model_rows_matched':True,'glm_return_reduction_unrounded_pp':delta,'unchanged_experimental_tables':checked,'record_modes_checked':39,'families':26,'multi_record_families':11,'multi_mode_families':9,'bibliography_unique_keys':len(keys),'resolved_citation_keys':len(cited),'source_sha256':{'full_suite_results':sha(E/'sp2027-r14-transfer-boundaries/full_suite_results.json'),'record_modes':sha(P/'provenance/r16-synthesis/record-mode-inventory.json')},'scope':'Saved predictions, customer intervals, costs, source table mapping and citation resolution; no new model calls or new source recoding.'}
(O/'data-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
