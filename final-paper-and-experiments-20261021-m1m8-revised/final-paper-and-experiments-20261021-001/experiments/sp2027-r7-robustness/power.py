"""Prospective design sensitivity, not empirical power of the original bootstrap."""
from r7common import *
from scipy.stats import norm
def compute():
    rng=np.random.default_rng(SEED);out=[];trials=20000
    for ratio in (1,3):
        for n in (5,7,14,18,30,50,75,100,150,200,250,400):
            for p in (.5,.55):
                for k in (1,7):
                    # Bernoulli correctness per independent customer, equal sensitivity/specificity.
                    # Independence across attacks is one extreme; k=1 also represents perfect dependence.
                    pos=rng.binomial(n,p,size=(trials,k))/n;neg=rng.binomial(n*ratio,p,size=(trials,k))/(n*ratio)
                    ba=(pos+neg)/2
                    # Null-free Wald planning approximation at the assumed population rate;
                    # 97.5th percentile parallels the original two-sided interval's upper endpoint.
                    se=np.sqrt(.25*p*(1-p)*(1/n+1/(n*ratio)))
                    upper=ba+norm.ppf(.975)*se
                    out.append({'positive_customers':n,'negative_customers':n*ratio,'true_ba':p,'independent_attackers':k,
                        'pass_probability_BA_only':float(np.mean(upper.max(axis=1)<.60)),'population_se':float(se)})
    return {'assumptions':'Independent Bernoulli customer correctness; equal TPR/TNR; fixed predictions; normal upper bound; no AUROC gate. Not actual cluster-bootstrap power.',
        'trials':trials,'seed':SEED,'rows':out,'minimum_80pct':[
            {'ratio':ratio,'true_ba':p,'attackers':k,'n_positive':next((r['positive_customers'] for r in out if r['negative_customers']==ratio*r['positive_customers'] and r['true_ba']==p and r['independent_attackers']==k and r['pass_probability_BA_only']>=.8),None)}
            for ratio in (1,3) for p in (.5,.55) for k in (1,7)]}
if __name__=='__main__':
    result=compute()
    if '--check' in sys.argv:assert result==read(HERE/'power.json')
    else:write(HERE/'power.json',result)
    print(json.dumps(result['minimum_80pct']))
