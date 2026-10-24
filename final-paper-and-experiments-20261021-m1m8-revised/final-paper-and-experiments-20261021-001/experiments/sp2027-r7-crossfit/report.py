"""Detailed CIs for every attack and union; uses immutable saved OOF predictions."""
from run import *
import platform
import sklearn,torch

def main():
 rows=json.loads((HERE/'predictions.json').read_text());base=json.loads((HERE/'results.json').read_text());out=[];draws={}
 for r in base['results']:
  target,arm,cond=r['target'],r['prompt'],r['condition'];rr=[p for p in rows if (p['target'],p['prompt'],p['condition'])==(target,arm,cond)]
  units=[dict(task=p['customer'],y=p['y']) for p in rr];per={};bas=[];aucs=[];two=[]
  for name in rr[0]['attacks']:
   ba,auc=L.stats.distributions(units,np.array([p['attacks'][name]['score'] for p in rr]),np.array([p['attacks'][name]['pred'] for p in rr]),2000)
   per[name]=dict(ba=float(ba[0]),ba_ci95=np.nanquantile(ba[1:],[.025,.975]).tolist(),auroc=float(auc[0]),auroc_ci95=np.nanquantile(auc[1:],[.025,.975]).tolist());bas.append(ba);aucs.append(auc);two.append(np.maximum(auc,1-auc))
  ub=np.nanmax(bas,axis=0);ua=np.nanmax(aucs,axis=0);ut=np.nanmax(two,axis=0);draws[target,arm,cond]=ub
  assert ub[0]==r['ext_ba'];np.testing.assert_array_equal(np.nanquantile(ub[1:],[.025,.975]),r['ext_ba_ci95'])
  out.append(dict(target=target,prompt=arm,condition=cond,n=len(rr),customers=len({p['customer'] for p in rr}),positive_customers=len({p['customer'] for p in rr if p['y']}),positive_episodes=sum(p['y'] for p in rr),best_attacker=max(per,key=lambda n:per[n]['ba']),suite_ba=float(ub[0]),suite_ba_ci95=np.nanquantile(ub[1:],[.025,.975]).tolist(),suite_auroc=float(ua[0]),suite_auroc_ci95=np.nanquantile(ua[1:],[.025,.975]).tolist(),sign_agnostic_auroc=float(ut[0]),sign_agnostic_auroc_ci95=np.nanquantile(ut[1:],[.025,.975]).tolist(),criterion=r['criterion_ext'],bytes_ratio=r['bytes_ratio'],calls_ratio=r['calls_ratio'],attackers=per))
 paired=[]
 for target in L.ev.TARGETS:
  for arm in ['baseline','rules']:
   for cond in ['jointconstant','jointbucket1024']:
    d=draws[target,arm,'undefended']-draws[target,arm,cond];paired.append(dict(target=target,prompt=arm,contrast='undefended minus '+cond,ba_decrease=float(d[0]),ci95=np.nanquantile(d[1:],[.025,.975]).tolist()))
   d=draws[target,arm,'jointconstant']-draws[target,arm,'jointbucket1024'];paired.append(dict(target=target,prompt=arm,contrast='jointconstant minus jointbucket1024',ba_difference=float(d[0]),ci95=np.nanquantile(d[1:],[.025,.975]).tolist()))
 runtime=dict(python=platform.python_version(),platform=platform.platform(),numpy=np.__version__,sklearn=sklearn.__version__,torch=torch.__version__,torch_threads=torch.get_num_threads())
 write(HERE/'detailed_results.json',dict(runtime=runtime,suite_size=len(out[0]['attackers']),legacy_suite_size=9,new_attackers=['ext_D2_cnn','ext_D2_kfp_style'],thresholds=dict(ba=.60,auroc=.65,rule='BA lower CI > .60: above_threshold; BA upper CI < .60 and max AUROC < .65: meets_evaluated_suite_criterion; otherwise inconclusive'),results=out,paired_contrasts=paired,scope='posthoc known cohort; intervals conditional on fitted attacks; direction/length only, third timing channel zero'))
 np.savez_compressed(HERE/'bootstrap_suite_ba.npz',**{'|'.join(k):v for k,v in draws.items()})
 lines=['# R7 crossfit complete extended union','', 'Posthoc known 690-episode Sol cohort; customer 5-fold OOF; direction and length only; zero timing channel. 2,000 customer-cluster bootstrap draws, suite maximum reselected per draw.','', '|Target|Prompt|Condition|BA [95% CI]|Max AUROC [95% CI]|BA winner|Wire ×|Calls ×|Criterion|','|---|---|---|---|---|---|---|---|---|']
 for r in out:lines.append(f"|{r['target']}|{r['prompt']}|{r['condition']}|{r['suite_ba']:.9f} [{r['suite_ba_ci95'][0]:.9f}, {r['suite_ba_ci95'][1]:.9f}]|{r['suite_auroc']:.9f} [{r['suite_auroc_ci95'][0]:.9f}, {r['suite_auroc_ci95'][1]:.9f}]|{r['best_attacker']}|{r['bytes_ratio']:.9f}|{r['calls_ratio']:.9f}|{r['criterion']}|")
 lines+=['','|Target|Prompt|Paired contrast|BA difference [95% CI]|','|---|---|---|---|']
 for r in paired:
  v=r.get('ba_decrease',r.get('ba_difference'));lines.append(f"|{r['target']}|{r['prompt']}|{r['contrast']}|{v:.9f} [{r['ci95'][0]:.9f}, {r['ci95'][1]:.9f}]|")
 (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps(runtime))
if __name__=='__main__':main()

