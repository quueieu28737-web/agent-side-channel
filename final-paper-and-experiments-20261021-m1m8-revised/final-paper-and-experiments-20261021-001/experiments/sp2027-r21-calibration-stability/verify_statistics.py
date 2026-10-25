"""Independent BA oracle and compatibility with archived customer bootstrap."""
import analyze as a
import numpy as np
from sklearn.metrics import balanced_accuracy_score
r=a.r
users=['a','a','b','c','c','d','e','e'];y=[0,0,1,1,0,0,1,0]
pred=[[0,1,1,0,1,0,1,0],[1,0,1,1,0,1,0,0]]
m={'users':users,'y':y,'predictions':{str(i):p for i,p in enumerate(pred)}}
units=[{'task':u,'y':v} for u,v in zip(users,y)]
ref=np.fmax.reduce([r.en.stats.distributions(units,np.array(p),np.array(p),100)[0][1:] for p in pred])
groups=sorted(set(users));draws=np.random.default_rng(r.en.stats.m.SEED).choice(len(groups),(100,len(groups)))
for i,draw in enumerate(draws):
    picks=[groups[j] for j in draw];ids=[k for u in picks for k,v in enumerate(users) if u==v]
    result=a.boot_metric(m,picks)
    if len({y[j] for j in ids})<2:assert np.isnan(result) and np.isnan(ref[i])
    else:
        oracle=max(balanced_accuracy_score([y[j] for j in ids],[p[j] for j in ids]) for p in pred)
        assert abs(result-ref[i])<1e-12 and abs(result-oracle)<1e-12
assert np.isnan(a.boot_metric(m,['a']*5))
assert np.allclose(a.holm([.01,.04,.03,.2]),[.04,.09,.09,.2])
assert np.allclose(a.holm([1,1,.2]),[1,1,.6])
r.nr.write(r.D/'statistics_verification.json',{'passed':True,'customer_bootstrap_matches_archived_implementation_and_sklearn':100,'single_class_test_draw_retained_as_invalid':True,'holm_known_examples':2,'analysis_sha256':r.nr.sha(r.D/'analyze.py')})
print('RESAMPLING_STATISTICS_VERIFIED')
