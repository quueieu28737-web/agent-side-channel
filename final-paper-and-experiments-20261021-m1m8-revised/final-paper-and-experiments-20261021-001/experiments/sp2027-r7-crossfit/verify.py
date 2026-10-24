"""Exact persisted model prediction and customer split audit; trusted local pickle only."""
from pathlib import Path
from dependency_check import check as check_dependency_closure
check_dependency_closure(Path(__file__).resolve().parent)
from run import *
from pathlib import PureWindowsPath

def relocated(path):
 mapping=json.loads((HERE/'portable-path-map.json').read_text(encoding='utf-8-sig'))
 original=PureWindowsPath(path);prefix=PureWindowsPath(mapping['original_package_root'])
 relative=original.relative_to(prefix)
 assert relative.parts and relative.parts[0]==mapping['allowed_first_component']
 assert not any(p in ('.','..') for p in relative.parts)
 root=HERE.parents[1].resolve();target=root.joinpath(*relative.parts).resolve()
 assert target.is_relative_to(root) and target.is_file(),('outside package or missing',path)
 return target
def main():
 protocol=json.loads((HERE/'protocol.json').read_text());fold=protocol['fold_of_customer']
 # JSON object keys may stringify numeric customer ids; use canonical representation.
 fold={str(k):v for k,v in fold.items()}
 for path,digest in protocol['source_hashes'].items():assert sha(relocated(path))==digest,(path,'source changed')
 for path,digest in json.loads((HERE/'inputs_manifest.json').read_text())['sha256'].items():assert sha(relocated(path))==digest,(path,'input changed')
 assert json.loads((HERE/'results.json').read_text())['protocol_sha256']==sha(HERE/'protocol.json')
 rows,_=L.all_episodes();assert {str(k):v for k,v in folds_of(rows).items()}==fold
 predictions=json.loads((HERE/'predictions.json').read_text());lookup={(r['episode'],r['target'],r['condition']):r for r in predictions}
 checks=0
 for p in sorted(HERE.glob('f*.zip')):
  with zipfile.ZipFile(p) as z:b=pickle.loads(z.read('bundle.pkl'))
  tr,te=b['train'],b['test'];k=b['fold'];target=p.stem.split('-')[-1];cond=p.stem.split('-')[1]
  for i,s in enumerate(te):
   row=lookup[key(s),target,cond]
   for name,(sc,pr) in b['attacks'].items():assert row['attacks'][name]==dict(score=float(sc[i]),pred=int(pr[i]))
  assert not {s['user'] for s in tr}&{s['user'] for s in te}
  assert all(fold[str(s['user'])]!=k for s in tr);assert all(fold[str(s['user'])]==k for s in te)
  att=L.attack_suite(tr,te,b['raw'],b['lab'],b['verb'],'network',b['verbs'],True)
  modelnames=[n for n in att if n not in ('majority','network_decode_count_rule')]
  assert len(modelnames)==len(b['old_models'])
  for n,(mdl,x) in zip(modelnames,b['old_models']):np.testing.assert_array_equal(mdl.predict_proba(x)[:,1],b['attacks'][n][0])
  for n,(sc,pr) in att.items():
   np.testing.assert_array_equal(sc,b['attacks'][n][0]);np.testing.assert_array_equal(pr,b['attacks'][n][1]);checks+=len(sc)
  ate=list(map(adapt,te))
  for n,mdl,x in [('ext_D2_cnn',b['cnn'],ate),('ext_D2_kfp_style',b['fp'],list(map(feature,ate)))]:
   sc=mdl.predict_proba(x)[:,1];np.testing.assert_array_equal(sc,b['attacks'][n][0]);np.testing.assert_array_equal(sc>=.5,np.array(b['attacks'][n][1],bool));checks+=len(sc)
  assert all(t==0 for r in ate for d,n,t in r['records'])
  print('verified',p.name,flush=True)
 assert len(predictions)==4140
 for c in json.loads((HERE/'calibrations.json').read_text()):
  assert not set(c['train_customers'])&set(c['test_customers'])
  assert all(d['user'] in c['train_customers'] for ds in c['calibration']['donors'].values() for d in ds)
 assert len({(r['episode'],r['target'],r['condition']) for r in predictions})==4140
 for r in predictions:assert r['fold']==fold[str(r['customer'])]
 result={'passed':True,'bundles':len(list(HERE.glob('f*.zip'))),'prediction_rows':len(predictions),'exact_score_checks':checks,'split':'same R5 customer 5 folds; zero train/test customer overlap','timing':'all third columns zero; direction and length only'}
 assert json.loads((HERE/'verification.json').read_text())==result;print(result)
if __name__=='__main__':main()




