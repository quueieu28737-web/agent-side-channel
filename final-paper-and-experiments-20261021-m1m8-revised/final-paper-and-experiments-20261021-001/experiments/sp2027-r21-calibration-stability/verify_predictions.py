"""Recompute all new point metrics using sklearn, separately from the runner."""
import run as r
from sklearn.metrics import balanced_accuracy_score
files=sorted((r.D/'replicates').glob('*.json'));assert len(files)==100
arrays=rows=0
for f in files:
    rep=r.nr.read(f)
    for row in rep['results']:
        for label,m in row['metrics'].items():
            metrics=[balanced_accuracy_score(m['y'],p) for p in m['predictions'].values()]
            assert len(metrics)==7 and abs(max(metrics)-m['suite_ba'])<1e-12
            arrays+=len(metrics);rows+=1
r.nr.write(r.D/'prediction_verification.json',{'passed':True,'suite_rows_recomputed':rows,'attacker_prediction_arrays_checked':arrays,'oracle':'sklearn.metrics.balanced_accuracy_score','replicates':len(files)})
print('ALL_NEW_PREDICTION_ARRAYS_VERIFIED',arrays)
