"""Current R7 publication checks. Prior version-specific receipts stay historical."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,re,subprocess,sys,zipfile
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
D=P/'experiments/sp2027-r7-robustness';C=P/'experiments/sp2027-r7-crossfit';A=P/'experiments/sp2027-r7-agent-extension'
L=P/'experiments/sp2027-r7-localization'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def history():
 prior=read(O/'prior-package-manifest.json')['files']
 allowed={'README.md','artifact-index.json','provenance/snapshot.json','manuscript/main.tex','manuscript/supplement.tex','manuscript/refs-deployment.bib'}
 sections=['01-introduction','03-methodology','04-scope','10-open-challenges','11-discussion','12-conclusion','26-corpus-map','30-reproducibility-guide','31-result-audit','37-transfer-tests','40-evidence-concordance','42-live-timing-main']
 allowed.update('manuscript/sections/'+n+'.tex' for n in sections)
 allowed.update('manuscript/tables/'+n+'.tex' for n in ['r4-primary','r5-main','family-audit-matrix','six-check-audit'])
 for n in ('main','supplement'):
  allowed.update({'manuscript/'+n+'.pdf','manuscript/'+n+'.bbl','pdf/'+n+'.pdf','provenance/build-logs/'+n+'.log','pdf/build-logs/'+n+'.log'})
 kept=sorted(set(prior)-allowed)
 with ThreadPoolExecutor(max_workers=10) as pool:
  for n,h in zip(kept,pool.map(lambda n:sha(P/n),kept)):assert h==prior[n],('Historical evidence changed',n)
 return len(kept)
def run(script,*args):
 subprocess.run([sys.executable,'-B',str(script),*args],check=True)
def main():
 kept=history();print('HISTORY_PASS',kept,flush=True)
 if '--history-only' in sys.argv:return
 run(P/'verify_revision.py')
 run(P/'experiments/sp2027-r4-full-20261023/verify_release.py')
 run(O/'audit_overlay.py','--check');run(D/'report.py','--check');run(D/'power.py','--check')
 run(O/'common_suite.py','--check')
 run(O/'crossfit_tables.py','--check');run(O/'localization_tables.py','--check');run(O/'legacy_table_check.py')
 f=read(D/'freeze.json')
 for n,h in f['source_sha256'].items():assert sha(D/n)==h,n
 assert sha(D/'PROTOCOL.md')==f['protocol_sha256'] and sha(D/'calibration.json')==f['calibration_sha256']
 for n,h in f['data_sha256'].items():assert sha(D/(n+'.zip'))==h
 v=read(D/'validation.json');assert v['status']=='PASS' and v['train_transformed_sessions']==5382 and v['test_transformed_sessions']==3588
 fit=read(D/'fit_complete.json');archive=read(D/'model_archive_manifest.json')
 assert fit['models']==archive['members'] and sha(D/'models.zip')==archive['archive_sha256']
 with zipfile.ZipFile(D/'models.zip') as z:
  assert set(z.namelist())==set(fit['models'])
  for n,h in fit['models'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h
 refit=read(D/'retraining_validation.json')
 assert refit['status']=='ALL_312_NEW_LEARNERS_EXACTLY_REFIT_AND_RELOADED' and refit['completed_cells']==52
 assert refit['predictions_sha256']==sha(D/'predictions.json') and refit['script_sha256']==sha(O/'retrain_robustness.py')
 res=read(D/'results.json');assert len(res['cells'])==52 and not any(v['criterion'] for v in res['cells'].values())
 common=read(D/'common-suite.json');audit=read(O/'common-suite-audit.json')
 assert len(common['common_attackers'])==7 and common['input_predictions_sha256']==sha(D/'predictions.json')
 for key,v in common['cells'].items():
  for metric in ('ba','auroc'):
   for field in ('point','ci95','invalid_draws'):assert v[metric][field]==audit['cells'][key][metric][field],(key,metric,field)
 cf=read(C/'verification.json');assert cf['passed'] and cf['bundles']==60 and cf['prediction_rows']==4140 and cf['exact_score_checks']==45540
 lv=read(L/'verification.json');assert lv['passed'] and lv['bundles']==40 and lv['prediction_rows']==2760 and lv['exact_score_checks']==30360
 assert lv['customer_overlap']==lv['duplicate_keys']==0 and lv['original_episode_count']==690
 for folder in (C,L):
  run(folder/'dependency_check.py')
  dep=read(folder/'dependency-verification.json')
  assert dep['passed'] and dep['runtime_bound_to_original_episode'] and dep['r6_frozen_chain']
  assert dep['closure_sha256']==sha(folder/'dependency-closure.json')
  assert dep['original_verification_sha256']==sha(folder/'verification.json')
  manifest=read(folder/'artifact_manifest.json')
  for n,v in manifest.items():
   assert (folder/n).stat().st_size==v['bytes'] and sha(folder/n)==v['sha256'],(folder.name,n)
  assert all(p.stat().st_size<100*1024**2 for p in folder.rglob('*') if p.is_file())
 run(O/'portable-verification/robustness_dependency_check.py',str(P))
 dd=read(D/'dependency-verification.json')
 assert dd['status']=='PASS' and dd['shared_dependencies']==36
 assert dd['d_freeze_sha256']==sha(D/'freeze.json') and dd['closure_sha256']==sha(D/'dependency-closure.json')
 section=(M/'sections/37-transfer-tests.tex').read_text(encoding='utf8')
 cr=read(C/'detailed_results.json');lr=read(L/'detailed_results.json')
 def contrast(data,arm,target,name):return next(v for v in data['paired_contrasts'] if (v['prompt'],v['target'],v['contrast'])==(arm,target,name))
 for cond in ('jointconstant','jointbucket1024'):
  pair='/'.join(f"{100*contrast(cr,'baseline',t,'undefended minus '+cond)['ba_decrease']:.1f}" for t in ('cancel','return'))
  assert pair+' points' in section,pair
  for t in ('cancel','return'):assert .30<=contrast(cr,'baseline',t,'undefended minus '+cond)['ba_decrease']<=.35
 for t in ('cancel','return'):
  v=contrast(lr,'baseline',t,'full minus no_writes')
  expected=f"{100*v['ba_decrease']:.1f} [{100*v['ci95'][0]:.1f},{100*v['ci95'][1]:.1f}]"
  assert expected in section,expected
 if '--experiments-only' in sys.argv:
  print('EXISTING_SOL_HISTORY_STRENGTHENED_ATTACKS_LOCALIZATION_TABLES_PASS',flush=True)
  return
 portable=read(O/'portable-verification/verification-receipt.json')
 assert portable['exit_code']==0 and portable['result']['passed'] and portable['result']['exact_score_checks']==45540
 assert portable['inputs_manifest_sha256']==sha(C/'inputs_manifest.json')
 assert portable['source_verification_json_sha256']==portable['relocated_verification_json_sha256']==sha(C/'verification.json')
 moved=read(O/'portable-verification/r7-component-portability-receipt.json')
 assert moved['localization']['passed'] and moved['localization']['exact_score_checks']==30360
 assert moved['localization']['verification_sha256_clone']==moved['localization']['verification_sha256_original']==sha(L/'verification.json')
 assert moved['robustness']['verify_status']=='PASS' and moved['robustness']['total_transformations']==8970
 assert moved['robustness']['reproduce']=='EXACT_REPRODUCTION_PASS' and moved['robustness']['model_packs']==52
 assert moved['robustness']['models_zip_sha256']==sha(D/'models.zip')
 av=read(A/'formal_validation.json');assert av['complete'] and av['runs']==150 and av['reward_recomputed_runs']==150
 assert av['plan_sha256']==sha(A/'formal_plan.json')
 plan=read(A/'formal_plan.json');assert plan['model']=='gpt-6-luna' and plan['effort']=='low' and plan['runs']==150 and not plan['pilot_included']
 for n,h in plan['files'].items():assert sha(A/n)==h,n
 af=read(A/'APPENDED_ANALYSIS_FREEZE.json')
 assert af['formal_plan_sha256']==sha(A/'formal_plan.json')
 assert af['collection_status_at_freeze']['completed_runs']==44
 assert af['training_trajectories']==58 and af['test_trajectories']==92
 for n,h in af['files'].items():assert sha(A/n)==h,n
 for n,h in af['inherited_helpers'].items():assert sha(P/'experiments'/n)==h,n
 compact=read(A/'compact_manifest.json')
 assert compact['formal_runs']==150 and compact['pilot_runs_excluded']==10
 assert sum(v['runs'] for v in compact['per_prompt'].values())==150
 assert sum(v['reward_sum'] for v in compact['per_prompt'].values())==av['native_reward_sum']
 luna_text=(M/'sections/45-luna-extension.tex').read_text(encoding='utf8')
 for arm in ('baseline','rules'):
  u=compact['per_prompt'][arm]
  assert f"{u['reward_sum']}/{u['runs']}" in luna_text
  for metric in ('infrastructure_attempt_errors','timeout_attempt_errors','automatic_retries'):assert u[metric]==0
 for view in ('writes-only','reads-only'):
  rows=[next(v for v in compact['D2_dispatch_suite'] if (v['prompt'],v['view'],v['target'])==('baseline',view,t)) for t in ('cancel','return')]
  pair='/'.join(f"{v['suite_ba']*100:.1f}" for v in rows)
  assert pair in section and pair in luna_text,pair
 assert sum(v['criterion']=='meets_evaluated_suite_criterion' for v in compact['network_suite'])==2
 for n,h in compact['artifacts'].items():assert sha(A/n)==h,n
 raw=read(A/'raw_archive.json');assert sha(A/raw['path'])==raw['sha256']
 for prefix in ('formal','public'):
  legacy=read(A/(prefix+'_validation.json'));corrected=read(A/(prefix+'_validation_corrected.json'))
  aligned=read(A/('decision_alignment.json' if prefix=='formal' else 'public_decision_alignment.json'))
  assert legacy['complete'] and legacy['runs']==legacy['reward_recomputed_runs']==150
  assert aligned['complete'] and aligned['episodes']==150
  assert aligned['tool_dispatch_attempts']==legacy['real_tool_calls']
  assert aligned['real_tool_calls']+aligned['unknown_tool_attempts']==aligned['tool_dispatch_attempts']
  for field in ('real_tool_calls','tool_dispatch_attempts','unknown_tool_attempts','model_calls'):
   assert corrected[field]==aligned[field]
   assert corrected[field]==sum(v[field] for v in compact['per_prompt'].values()),field
  assert corrected['legacy_receipt_sha256']==sha(A/(prefix+'_validation.json'))
  assert corrected['decision_alignment_sha256']==sha(A/corrected['decision_alignment'])
  if prefix=='public':assert legacy['archive_sha256']==aligned['archive_sha256']==raw['sha256']
 net=read(A/'public_network_validation.json')
 assert net['complete'] and net['recomputed_results']==32 and net['archive_sha256']==raw['sha256']
 assert set(net['matched_fields'])=={'suite_ba','suite_auroc','suite_ba_ci95','suite_auroc_ci95'}
 d2=read(A/'public_d2_validation.json')
 assert d2['complete'] and d2['episodes_reconstructed']==150 and d2['suite_cells_matched']==12 and d2['per_model_prediction_sets_matched']==36
 assert d2['public_zip_sha256']==raw['sha256'] and d2['analysis_code_sha256']==sha(A/'evaluate_d2.py')
 assert len(compact['D2_dispatch_suite'])==12 and len(compact['network_suite'])==16
 run(O/'portable-verification/luna_dependency_check.py',str(P))
 ld=read(O/'portable-verification/luna-dependency-receipt.json')
 assert ld['status']=='PASS' and ld['load_tau_code_and_data_files']==24 and not ld['public_zip_is_self_contained']
 assert ld['formal_plan_sha256']==sha(A/'formal_plan.json')
 assert d2['dependency_receipt_sha256']==sha(O/'portable-verification/luna-dependency-receipt.json')
 run(O/'luna_tables.py','--check')
 old=read(P/'experiments/sp2027-r4-full-20261023/validation.json');assert old['status']=='VERIFIED' and old['episodes']==690
 coverage=read(O/'checklist-coverage.json')
 expected={f'T{i}.{j}' for i,n in enumerate([4,5,4,4,3,3,3,3,3,2,2,2,2],1) for j in range(1,n+1)}
 assert {x['id'] for x in coverage['items']}==expected and len(coverage['items'])==40
 checklist=(R/'docs/R7-逐项修改验收清单.md').read_text(encoding='utf8')
 assert set(re.findall(r'^\| (T\d+\.\d+) \|',checklist,re.M))==expected
 for x in coverage['items']:
  assert 'PENDING' not in x['status'],x
  for path in x['evidence']:assert (P/path).exists(),path
 assert set(coverage['unfulfilled_resources'])=={'second environment','fixed open-weight model','different-vendor model','new independent positive customers','live cover with LLM replanning','two external blind human coders'}
 source=(M/'main.tex').read_text()
 assert source.index(r'\bibliography{')<source.index(r'\appendices')
 assert r'\documentclass[conference,compsoc]{IEEEtran}' in source
 # Check only the live source closure, not historical appendices or archived drafts.
 sys.path.insert(0,str(P));from verify_package import closure
 body='\n'.join((M/p).read_text(encoding='utf8') for p in closure(M,'main.tex') if p.endswith('.tex'))
 assert 'pre-registered tests' not in body and 'independent human inter-rater reliability' not in body
 for phrase in ('non-independent','standard prompt','S20','timing-dependent','same-provider','11 cells'):
  assert phrase.lower() in body.lower(),phrase
 for table in ('transfer-streaming','r7-e6-main','r7-e12-main','r7-rq-findings','r7-cohorts','r7-deployment','r7-controls'):
  assert 'tables/'+table+'.tex' in closure(M,'main.tex'),table
 pages={};pdfhash={}
 for name in ('main','supplement'):
  path=P/'pdf'/(name+'.pdf');assert path.read_bytes()==(M/path.name).read_bytes()==(R/path.name).read_bytes()
  doc=PdfReader(path);texts=[p.extract_text() for p in doc.pages];alltext='\n'.join(texts)
  for p in doc.pages:assert float(p.mediabox.width)==612 and float(p.mediabox.height)==792
  for private in ('quueieu28737','administrator','c:/users/','c:\\users\\'):
   assert private not in (str(doc.metadata)+alltext).lower(),(name,private)
  refs=next(i+1 for i,t in enumerate(texts) if re.search(r'(?m)^References\s*$',t))
  if name=='main':
   app=next(i+1 for i,t in enumerate(texts) if 'Appendix A.' in t)
   assert refs<=13 and app>refs and len(texts)<=18,(refs,app,len(texts))
   assert 'Conclusion' in ''.join(texts[:13]) and 'Luna' in ''.join(texts[:13])
   for needle in ('Tamaraw','E14','E12','R9'):
    assert needle in ''.join(texts[:13]),needle
   pages.update(body=refs,references_start=refs,appendix_start=app)
  else:assert all(x in alltext for x in ('S20.','S21.','S22.'))
  pages[name]=len(texts);pdfhash[name]=sha(path)
  for folder in ('provenance/build-logs','pdf/build-logs'):
   log=(P/folder/(name+'.log')).read_text(errors='replace')
   for bad in ('Overfull','undefined references','undefined on input line','multiply defined','Float too large'):
    assert bad not in log,(name,bad)
 visual=read(O/'visual_qa.json');assert visual['pdf_sha256']==pdfhash and visual['status']=='ALL_RENDERED_PAGES_INSPECTED'
 result={'status':'R7_HISTORY_EXPERIMENTS_SOURCES_TABLES_PDFS_AND_40_ITEMS_PASS','base_commit':'ad7ec5f445f7d5f5ab010eee36b98e6e8ab6a7f9',
  'preserved_prior_files':kept,'original_sol_runs':690,'additional_formal_luna_runs':150,'e14_cells':52,
  'new_learners_exactly_refit':312,'crossfit_exact_scores':45540,'oracle_localization_exact_scores':30360,'current_unverified_audit_cells':11,
  'pdf_pages':pages,'pdf_sha256':pdfhash,'checklist_items':40,'external_requirements_unfulfilled':coverage['unfulfilled_resources']}
 if '--save' in sys.argv:(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
