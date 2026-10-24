from run import *
def main():
 predictions=json.loads((HERE/'predictions.json').read_text());full=[dict(r,view='full') for r in json.loads((CROSS/'predictions.json').read_text()) if r['condition']=='undefended'];allrows=predictions+full;results=[];draws={}
 for target in ['cancel','return']:
  for arm in ['baseline','rules']:
   for view in ['full','no_writes','writes_only']:
    rows=[r for r in allrows if (r['target'],r['prompt'],r['view'])==(target,arm,view)];assert len(rows)==345;units=[dict(task=r['customer'],y=r['y']) for r in rows];per={};bs=[];ass=[]
    for name in rows[0]['attacks']:
     ba,auc=L.stats.distributions(units,np.array([r['attacks'][name]['score'] for r in rows]),np.array([r['attacks'][name]['pred'] for r in rows]),2000);bs.append(ba);ass.append(auc);per[name]=dict(ba=float(ba[0]),ba_ci95=np.nanquantile(ba[1:],[.025,.975]).tolist(),auroc=float(auc[0]),auroc_ci95=np.nanquantile(auc[1:],[.025,.975]).tolist())
    ub=np.nanmax(bs,axis=0);ua=np.nanmax(ass,axis=0);draws[target,arm,view]=ub
    results.append(dict(target=target,prompt=arm,view=view,n=len(rows),customers=len({r['customer'] for r in rows}),suite_size=len(per),suite_ba=float(ub[0]),suite_ba_ci95=np.nanquantile(ub[1:],[.025,.975]).tolist(),suite_auroc=float(ua[0]),suite_auroc_ci95=np.nanquantile(ua[1:],[.025,.975]).tolist(),best_attacker=max(per,key=lambda n:per[n]['ba']),criterion=L.stats.criterion(float(ub[0]),np.nanquantile(ub[1:],[.025,.975]),float(ua[0])),attackers=per))
 contrasts=[]
 for target in ['cancel','return']:
  for arm in ['baseline','rules']:
   for view in ['no_writes','writes_only']:
    d=draws[target,arm,'full']-draws[target,arm,view];contrasts.append(dict(target=target,prompt=arm,contrast='full minus '+view,ba_decrease=float(d[0]),ci95=np.nanquantile(d[1:],[.025,.975]).tolist()))
 write(HERE/'detailed_results.json',dict(runtime=dict(python=sys.version.split()[0],numpy=np.__version__,sklearn=__import__('sklearn').__version__,torch=__import__('torch').__version__),scope='Posthoc oracle localization on original 690 Sol episodes; no new captures/LLM calls; zero timing channel; intervals conditional on fitted attacks.',suite_size=11,results=results,paired_contrasts=contrasts,retained_fraction=json.loads((HERE/'retained_fraction.json').read_text()),full_reference='R7 crossfit completed undefended OOF predictions, exact source hashes in protocol.json'))
 np.savez_compressed(HERE/'bootstrap_suite_ba.npz',**{'|'.join(k):v for k,v in draws.items()})
 lines=['# R7 strengthened E12 oracle localization','', 'Posthoc known cohort. Full-view OOF reused from verified R7 crossfit. All 11 attacks; 2,000 common customer-cluster draws, max reselected each draw. Direction and length only; zero timing.','', '|Target|Prompt|Oracle view|BA [95% CI]|Max AUROC [95% CI]|BA winner|Criterion|','|---|---|---|---|---|---|---|']
 for r in results:lines.append(f"|{r['target']}|{r['prompt']}|{r['view']}|{r['suite_ba']:.9f} [{r['suite_ba_ci95'][0]:.9f}, {r['suite_ba_ci95'][1]:.9f}]|{r['suite_auroc']:.9f} [{r['suite_auroc_ci95'][0]:.9f}, {r['suite_auroc_ci95'][1]:.9f}]|{r['best_attacker']}|{r['criterion']}|")
 lines+=['','|Target|Prompt|Paired oracle contrast|BA difference [95% CI]|','|---|---|---|---|']
 for r in contrasts:lines.append(f"|{r['target']}|{r['prompt']}|{r['contrast']}|{r['ba_decrease']:.9f} [{r['ci95'][0]:.9f}, {r['ci95'][1]:.9f}]|")
 (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
if __name__=='__main__':main()


