"""Recompute all independent dispatch D2 ablations from public ZIP episodes + fixed checkout."""
from common import *
import tempfile,zipfile,shutil,datetime
import evaluate_d2 as d2

def main():
 root=HERE;freeze=read(root/'APPENDED_ANALYSIS_FREEZE.json');assert sha(root/'evaluate_d2.py')==freeze['files']['evaluate_d2.py']
 for rel,h in freeze['inherited_helpers'].items():assert sha(EXP/rel)==h
 meta=read(root/'raw_archive.json');assert sha(root/meta['path'])==meta['sha256'];inventory={x['path']:x for x in read(root/'raw_evidence_inventory.json')};n=0
 with tempfile.TemporaryDirectory(prefix='r7-public-d2-') as td:
  target=Path(td)
  with zipfile.ZipFile(root/meta['path']) as z:
   for name in z.namelist():
    if not (name.startswith('formal/') and name.endswith('/episode.json')):continue
    out=(target/name).resolve();assert out.is_relative_to(target.resolve());data=z.read(name);assert hashlib.sha256(data).hexdigest()==inventory[name]['public_sha256']
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);n+=1
  assert n==150;shutil.copyfile(root/'formal_plan.json',target/'formal_plan.json');d2.HERE=target;d2.main()
  for name in ['D2_suite.json','D2_results.json','D2_predictions.json']:assert read(target/name)==read(root/name),name
  write(root/'public_d2_validation.json',{'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input':'150 episode files from public model-evidence ZIP plus fixed checkout/vendor/helpers/dependencies; original raw directories not consulted; ZIP not self-contained','public_zip_sha256':meta['sha256'],'episodes_reconstructed':n,'suite_cells_matched':len(read(target/'D2_suite.json')),'per_model_prediction_sets_matched':len(read(target/'D2_predictions.json')),'match':'Exact JSON equality for all suite BA/AUROC/both CI/valid draws, all per-model results, scores and predictions','analysis_code_sha256':sha(root/'evaluate_d2.py'),'verifier_code_sha256':sha(root/'verify_public_d2.py'),'dependency_receipt_sha256':sha(root.parents[1]/'provenance'/'r7-review'/'portable-verification'/'luna-dependency-receipt.json'),'additional_LLM_requests':0})
 print('PUBLIC_D2_VALIDATION_OK')
if __name__=='__main__':main()
