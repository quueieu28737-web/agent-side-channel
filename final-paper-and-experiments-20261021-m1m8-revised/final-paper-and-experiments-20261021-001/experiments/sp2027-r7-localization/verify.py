"""Portable exact saved-model predictions, full legacy refit, and oracle filtering audit."""
from pathlib import Path
from dependency_check import check as check_dependency_closure
check_dependency_closure(Path(__file__).resolve().parent)
from run import *
def main():
 protocol=json.loads((HERE/'protocol.json').read_text());fold={str(k):v for k,v in protocol['fold_of_customer'].items()}
 for rel,digest in protocol['source_hashes'].items():
  target=(PACKAGE/rel).resolve();assert target.is_relative_to(PACKAGE.resolve());assert sha(target)==digest,(rel,'hash changed')
 rows,_=L.all_episodes();assert len(rows)==690;original={key(e):e for e in rows};assert len(original)==690;assert {str(k):v for k,v in folds_of(rows).items()}==fold
 predictions=json.loads((HERE/'predictions.json').read_text());lookup={(r['episode'],r['target'],r['view']):r for r in predictions};assert len(predictions)==len(lookup)==2760
 expected={v:{key(e):session(e,VIEWS[v]) for e in rows} for v in ['no_writes','writes_only']};checks=0;modelbytes=[]
 for path in sorted(HERE.glob('f*.zip')):
  with zipfile.ZipFile(path) as z:b=pickle.loads(z.read('bundle.pkl'))
  assert path.stat().st_size<100*1024**2;modelbytes.append(path.stat().st_size);tr,te=b['train'],b['test'];k=b['fold'];view=b['view'];target=b['target'];assert not {s['user'] for s in tr}&{s['user'] for s in te}
  for split,ss in [('train',tr),('test',te)]:
   for s in ss:
    assert (fold[str(s['user'])]==k)==(split=='test');e=expected[view][key(s)];assert e['calls']==s['calls'] and e['records']==s['records'];assert s[b['lab']]==original[key(s)][b['lab']]
  att=L.attack_suite(tr,te,tr,b['lab'],b['verb'],'network',b['verbs'],True);modelnames=[n for n in att if n not in ('majority','network_decode_count_rule')];assert len(modelnames)==len(b['old_models'])
  for name,(mdl,x) in zip(modelnames,b['old_models']):np.testing.assert_array_equal(mdl.predict_proba(x)[:,1],b['attacks'][name][0])
  for name,(sc,pr) in att.items():np.testing.assert_array_equal(sc,b['attacks'][name][0]);np.testing.assert_array_equal(pr,b['attacks'][name][1])
  ate=list(map(adapt,te));assert all(t==0 for s in ate for d,n,t in s['records'])
  for name,mdl,x in [('ext_D2_cnn',b['cnn'],ate),('ext_D2_kfp_style',b['fp'],list(map(feature,ate)))]:np.testing.assert_array_equal(mdl.predict_proba(x)[:,1],b['attacks'][name][0]);np.testing.assert_array_equal(np.asarray(b['attacks'][name][0])>=.5,np.asarray(b['attacks'][name][1],bool))
  for i,s in enumerate(te):
   row=lookup[key(s),target,view];assert row['y']==int(s[b['lab']])
   for name,(sc,pr) in b['attacks'].items():assert row['attacks'][name]==dict(score=float(sc[i]),pred=int(pr[i]));checks+=1
  print('verified',path.name,flush=True)
 assert len(modelbytes)==40;assert checks==30360
 full_expected={key(e):session(e,VIEWS['full']) for e in rows};fullkeys=set()
 for path in sorted(CROSS.glob('f*-undefended-*.zip')):
  with zipfile.ZipFile(path) as z:b=pickle.loads(z.read('bundle.pkl'))
  for s in b['train']+b['test']:
   e=full_expected[key(s)];assert e['calls']==s['calls'] and e['records']==s['records'];fullkeys.add(key(s))
 assert len(fullkeys)==690
 full_lookup={(r['episode'],r['target']):r for r in json.loads((CROSS/'predictions.json').read_text()) if r['condition']=='undefended'}
 for r in predictions:
  f=full_lookup[r['episode'],r['target']];assert (r['customer'],r['fold'],r['y'])==(f['customer'],f['fold'],f['y'])
 retained=json.loads((HERE/'retained_fraction.json').read_text())
 for arm in ['baseline','rules']:
  rr=[r for r in retained if r['prompt']==arm];assert abs(sum(r['calls_fraction'] for r in rr)-1)<1e-12;assert abs(sum(r['wire_fraction'] for r in rr)-1)<1e-12
 assert json.loads((CROSS/'verification.json').read_text())['passed'];assert json.loads((HERE/'run_complete.json').read_text())['protocol_sha256']==sha(HERE/'protocol.json')
 result=dict(passed=True,bundles=40,prediction_rows=2760,exact_score_checks=checks,largest_model_file_bytes=max(modelbytes),duplicate_keys=0,original_episode_count=690,customer_overlap=0,oracle_filter='Exact original E12 call and TLS sequence equality for all train/test session instances',timing='Third timing channel all zeros; no measured or generated timing')
 assert json.loads((HERE/'verification.json').read_text())==result;print(result)
if __name__=='__main__':main()



