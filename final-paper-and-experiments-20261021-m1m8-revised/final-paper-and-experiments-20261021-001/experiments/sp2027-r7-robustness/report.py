"""Derive every current E14 table and cost plot from saved results."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;M=HERE.parents[1]/'manuscript'
R=json.loads((HERE/'results.json').read_text());P=json.loads((HERE/'power.json').read_text())
C=json.loads((HERE/'common-suite.json').read_text())
names={'raw':'Undefended','padding':'Per-call constant','shadow_serial':'Serial shadow','shadow_parallel2':'Two-in-flight shadow',
 'tunnel_2ms':'Full tunnel, 2 ms','tunnel_5ms':'Full tunnel, 5 ms','bucket1024':'Record buckets','tamaraw':'Tamaraw 40/12 ms',
 'tamaraw_fast':'Tamaraw 4/1.2 ms','front':'FRONT','wtfpad':'WTF-PAD adaptation','walkie_talkie':'WT random-donor','front_shift':'FRONT, short calibration'}
measured=list(names)[:6];conditions=list(names)
def pair(c,arm='baseline'):
 return '/'.join(f"{R['cells'][f'{arm}|{c}|{t}']['ba']['point']*100:.1f}" for t in ('cancel','return'))
def put(p,s):
 s=s.strip()+'\n'
 if '--check' in sys.argv:assert p.read_text(encoding='utf-8')==s,p
 else:p.write_text(s,encoding='utf-8',newline='\n')
head=r'''\begin{table*}[t]\centering\footnotesize
\caption{E13 captures with the E14 expanded defense-aware suite, and offline WF adaptations. Standard prompt: 138 test trajectories, 24 customers. BA and upper 95\% bounds are cancel/return percentages. Every condition has an upper bound above 60\%, leaving the two-target absolute criterion unconfirmed. Last-real/finish p95 is measured from RPC start for M rows; for S rows it is simulated from the first input record, not online planner latency.}\label{tab:r7-controls}
\begin{tabular}{@{}llrrrrrr@{}}\toprule
View & Condition & BA & Upper BA & Bytes$\times$ & Calls$\times$ & Last-real p95 (ms) & Finish p95 (ms)\\\midrule'''
lines=[head]
for i,c in enumerate(conditions):
 v=R['resources']['baseline|'+c]
 if i==6:lines.append(r'\midrule')
 upper='/'.join(f"{R['cells'][f'baseline|{c}|{t}']['ba']['ci95'][1]*100:.1f}" for t in ('cancel','return'))
 lines.append(f"{'M' if c in measured else 'S'} & {names[c]} & {pair(c)} & {upper} & {v['wire_ratio']:.2f} & {v['call_ratio']:.2f} & {v['last_real_p95_ms']:.1f} & {v['traffic_p95_ms']:.1f}"+r'\\')
lines+=[r'''\bottomrule\end{tabular}
\par\smallskip\raggedright M rows retain 17--22 attacks (seven R7 models plus all original E13 attacks); S rows use the common seven. These strongest-available maxima are not a matched-suite dominance comparison. S20 provides the common-seven sensitivity and cost plot. Bytes include TLS headers; ratios use each prompt's undefended captures. WF dummies execute no tools; random-donor WT has no symmetric site-pair guarantee.
\end{table*}''']
put(M/'tables/r7-controls.tex','\n'.join(lines))
lines=[r'''\begin{longtable}{@{}llrrrr@{}}
\caption{E14: all prompt/defense cells, maximum over the expanded attack suite. Customer bootstrap 95\% BA intervals; AUC is suite-maximum AUROC. All 52 cells fail the absolute criterion.}\label{tab:r7-all}\\
\toprule Prompt / condition & Target & BA [95\% CI] & AUC & Attacks & CNN trunc.\\\midrule\endfirsthead
\toprule Prompt / condition & Target & BA [95\% CI] & AUC & Attacks & CNN trunc.\\\midrule\endhead''']
for arm in ('baseline','rules'):
 for c in conditions:
  for t in ('cancel','return'):
   v=R['cells'][f'{arm}|{c}|{t}'];b=v['ba'];ci=b['ci95']
   lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} / {names[c]} & {t} & {b['point']*100:.1f} [{ci[0]*100:.1f}, {ci[1]*100:.1f}] & {v['auroc']['point']:.3f} & {v['suite_size']} & {v['cnn_test_truncated']}"+r'\\')
lines.append(r'\bottomrule\end{longtable}')
put(M/'tables/r7-all.tex','\n'.join(lines))
lines=[r'''\begin{longtable}{@{}llrrrr@{}}
\caption{Matched-suite sensitivity: the same seven R7 models in every E14 condition. BA and AUROC maxima are independently reselected in every customer-bootstrap draw. This subset is used for the cost plot, not to replace the stronger available attack union or its absolute assessment.}\label{tab:r7-common}\\
\toprule Prompt / condition & Target & BA [95\% CI] & AUROC & Valid draws & Subset gate\\\midrule\endfirsthead
\toprule Prompt / condition & Target & BA [95\% CI] & AUROC & Valid draws & Subset gate\\\midrule\endhead''']
for arm in ('baseline','rules'):
 for c in conditions:
  for t in ('cancel','return'):
   v=C['cells'][f'{arm}|{c}|{t}'];b=v['ba'];ci=b['ci95']
   lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} / {names[c]} & {t} & {b['point']*100:.1f} [{ci[0]*100:.1f}, {ci[1]*100:.1f}] & {v['auroc']['point']:.3f} & {2000-b['invalid_draws']} & {'Pass' if v['criterion'] else 'Unmet'}"+r'\\')
lines.append(r'\bottomrule\end{longtable}')
put(M/'tables/r7-common.tex','\n'.join(lines))
lines=[r'''\begin{table}[ht]\centering\small
\caption{Planning sensitivity: smallest searched positive-cluster count with at least 80\% probability of an upper BA bound below .60. Independent Bernoulli customer correctness and a normal 97.5\% upper endpoint; this omits the AUROC gate and is not the power of the observed heterogeneous bootstrap.}\label{tab:r7-power}
\begin{tabular}{@{}rrrr@{}}\toprule
Negatives per positive & Population BA & Independent attacks & Positive clusters\\\midrule''']
for v in P['minimum_80pct']:
 n=v['n_positive'];lines.append(f"{v['ratio']} & {v['true_ba']:.2f} & {v['attackers']} & {n if n is not None else '$>400$ in grid'}"+r'\\')
lines.append(r'\bottomrule\end{tabular}\end{table}')
put(M/'tables/r7-power.tex','\n'.join(lines))
if '--check' not in sys.argv:
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.ticker import FixedLocator, ScalarFormatter, NullFormatter
 plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'font.family':'DejaVu Sans'})
 fig,ax=plt.subplots(2,2,figsize=(9,6.5),layout='constrained')
 ys=[max(C['cells'][f'baseline|{c}|{t}']['ba']['point'] for t in ('cancel','return'))*100 for c in conditions]
 full=[max(R['cells'][f'baseline|{c}|{t}']['ba']['point'] for t in ('cancel','return'))*100 for c in conditions]
 xs=[R['resources']['baseline|'+c]['wire_ratio'] for c in conditions]
 frontier=[i for i in range(len(xs)) if not any(xs[j]<=xs[i] and ys[j]<=ys[i] and (xs[j]<xs[i] or ys[j]<ys[i]) for j in range(len(xs)))]
 offsets={1:(4,5),2:(4,5),3:(4,5),4:(6,1),5:(-14,5),6:(-14,-10),7:(-14,7),8:(-11,-12),9:(-16,5),10:(6,-10),11:(-14,-10),12:(-14,5),13:(7,-10)}
 for i,c in enumerate(conditions):
  v=R['resources']['baseline|'+c];color='#175c82' if c in measured else '#aa5d26';marker='o' if c in measured else '^'
  panel=ax[0,0];x=v['wire_ratio']
  if full[i]>ys[i]+1e-10:
   panel.plot([x,x],[ys[i],full[i]],color='#8c8c8c',lw=.8,ls='--')
   panel.scatter(x,full[i],edgecolor='#777777',facecolor='none',marker='s',s=24)
   panel.annotate(str(i+1)+'+',(x,full[i]),xytext=(5,4),textcoords='offset points',fontsize=7,color='#666666')
  panel.scatter(x,ys[i],color=color,marker=marker,s=34);panel.annotate(str(i+1),(x,ys[i]),xytext=offsets[i+1],textcoords='offset points',fontsize=8)
  ax[0,1].barh(i+1,v['call_ratio'],color=color,height=.65)
  ax[0,1].text(v['call_ratio']+.06,i+1,f"{v['call_ratio']:.2f}",va='center',fontsize=7)
  panel=ax[1,0] if c in measured else ax[1,1]
  latency_offsets={7:(-14,6),10:(6,-10),11:(6,4),12:(6,5),13:(-14,-10),8:(-13,5)}
  panel.scatter(v['last_real_p95_ms'],ys[i],color=color,marker=marker,s=34);panel.annotate(str(i+1),(v['last_real_p95_ms'],ys[i]),xytext=latency_offsets.get(i+1,(4,5 if i%2 else -9)),textcoords='offset points',fontsize=8)
 order=sorted(frontier,key=lambda i:xs[i]);ax[0,0].plot([xs[i] for i in order],[ys[i] for i in order],color='gray',ls=':',lw=1)
 ax[0,0].set(xscale='log',xlabel='TLS wire bytes / undefended',title='A. Common-suite byte / leakage points')
 ax[0,1].set(xlabel='Tool calls / undefended',title='B. Tool-call cost',ylabel='Condition ID',xlim=(0,4.5),yticks=list(range(1,14)),ylim=(13.7,.3))
 ax[0,1].grid(axis='x',alpha=.2)
 ax[1,0].set(xscale='log',xlabel='Measured last-real-response p95 (ms)',title='C. Live E13 tool-response clock')
 ax[1,1].set(xscale='log',xlim=(10,1000),xlabel='Simulated last-real span p95 (ms)',title='D. Offline WF schedule; first record = 0')
 for a in (ax[0,0],ax[1,0],ax[1,1]):a.set_ylabel('Common-suite max BA (%)');a.set_ylim(48,100);a.grid(alpha=.2);a.axhline(50,color='gray',lw=.5)
 for a,ticks in ((ax[0,0],[1,10,100]),(ax[1,0],[20,50,100]),(ax[1,1],[10,100,1000])):
  a.xaxis.set_major_locator(FixedLocator(ticks));a.xaxis.set_major_formatter(ScalarFormatter());a.xaxis.set_minor_formatter(NullFormatter())
 fig.savefig(M/'figures/r7-pareto.pdf',metadata={'Creator':'Reproducible plotting script','CreationDate':None,'ModDate':None})
 fig.savefig(HERE/'pareto.png',dpi=160);plt.close(fig)
 write={'numbered_conditions':{str(i+1):c for i,c in enumerate(conditions)},'byte_frontier_indices':[i+1 for i in order],
        'common_suite_max_ba_percent':ys,'full_union_max_ba_percent':full,'common_attackers':C['common_attackers'],
        'meaning':'Descriptive matched-seven-attack BA/byte frontier only; gray upper squares show larger available unions. Measured and simulated latency are not interchangeable; confidence intervals not used to assert dominance.'}
 (HERE/'plot-data.json').write_text(json.dumps(write,indent=2)+'\n',encoding='utf-8')
plot=json.loads((HERE/'plot-data.json').read_text())
assert plot['common_suite_max_ba_percent']==[100*max(C['cells'][f'baseline|{c}|{t}']['ba']['point'] for t in ('cancel','return')) for c in conditions]
assert plot['full_union_max_ba_percent']==[100*max(R['cells'][f'baseline|{c}|{t}']['ba']['point'] for t in ('cancel','return')) for c in conditions]
assert plot['common_attackers']==C['common_attackers'] and len(C['common_attackers'])==7
assert plot['numbered_conditions']=={str(i+1):c for i,c in enumerate(conditions)}
print('E14_TABLES_AND_PLOT_CHECKED' if '--check' in sys.argv else 'E14_TABLES_AND_PLOT_WRITTEN')
