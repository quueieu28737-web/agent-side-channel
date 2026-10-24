"""Derive manuscript tables directly from verified E13 outputs."""
from r6common import *

NAMES={'raw':'Raw','padding':'Per-call padding','shadow_serial':'Shadow, serial',
       'shadow_parallel2':'Shadow, two in flight','tunnel_2ms':'Full tunnel, 2 ms','tunnel_5ms':'Full tunnel, 5 ms'}
VN={'size_order':'Size/order','timing_direction':'Timing/direction','joint':'Joint features',
    'flush_stripped_joint':'Estimated flush removed','suite':'Full adaptive suite'}

def pct(x):return f'{100*x:.1f}'
def interval(x):return f"\\mbox{{{pct(x['point'])} [{pct(x['ci95'][0])}, {pct(x['ci95'][1])}]}}"
def pair(res,arm,cond,view):return '/'.join(pct(res['cells']['|'.join((arm,cond,view,t))]['ba']['point']) for t in ('cancel','return'))

def tables():
    res=read(HERE/'results.json');main=[];supp=[]
    main.extend([r'\begin{table*}[t]\centering\footnotesize',
      r'\caption{E13: measured live tool RPCs and timing-aware attacks. Six conditions re-execute all 690 saved agent trajectories (4,140 TLS sessions); this table reports the 138 baseline-prompt test trajectories from 24 customers. BA columns show cancellation/return percentages. S19 reports both prompt arms, customer-cluster intervals and per-view attacks.}\label{tab:r6-main}',
      r'\setlength{\tabcolsep}{4pt}',r'\begin{tabularx}{\textwidth}{@{}Yrrrrrr@{}}\toprule',
      r'Condition & Size/order BA & Full-suite BA & Bytes$\times$ & Calls$\times$ & Real-chain p95 (ms) & Traffic p95 (ms)\\\midrule'])
    for c in CONDITIONS:
        r=res['resources']['baseline|'+c]
        main.append(f"{NAMES[c]} & {pair(res,'baseline',c,'size_order')} & {pair(res,'baseline',c,'suite')} & {r['wire_ratio']:.1f} & {r['call_ratio']:.1f} & {r['last_real_response_ms']['p95']:.1f} & {r['traffic_finish_ms']['p95']:.1f} "+r'\\')
    main.extend([r'\bottomrule\end{tabularx}',
      r'\par\smallskip\raggedright Full suite: size/order, timing/direction and joint classifiers; shadow conditions also include learned flush removal. Real-chain: release to last real response; traffic: through cover completion or tunnel horizon. Clocks exclude LLM generation and WAN latency. Tunnel dummy cells execute no tools; both directions send 133 fixed-size cells. All real responses and final live states are checked against unprotected execution.',r'\end{table*}'])
    for arm in ('baseline','rules'):
        supp.extend([r'\begin{table}[htbp]\centering\footnotesize',
          '\\caption{E13 '+arm+' prompt: intent BA [95\\% customer-cluster interval] and AUROC. The full suite unions all available views.}',
          r'\begin{tabular}{llrrrr}\toprule',r'Condition & View & Cancel BA [CI] & Return BA [CI] & Cancel AUC & Return AUC\\\midrule'])
        for c in CONDITIONS:
            for view in ['size_order','timing_direction','joint']+(['flush_stripped_joint'] if c.startswith('shadow') else [])+['suite']:
                a=res['cells']['|'.join((arm,c,view,'cancel'))];b=res['cells']['|'.join((arm,c,view,'return'))]
                supp.append(f"{NAMES[c]} & {VN[view]} & {interval(a['ba'])} & {interval(b['ba'])} & {a['auroc']['point']:.3f} & {b['auroc']['point']:.3f} "+r'\\')
            supp.append(r'\addlinespace[2pt]')
        supp.extend([r'\bottomrule\end{tabular}',r'\end{table}',r'\clearpage'])
    supp.extend([r'\begin{table}[htbp]\centering\footnotesize',
      r'\caption{E13 live execution costs, both prompt arms. Medians and 95th percentiles describe observed local RPCs; they are not production-service latency estimates.}',
      r'\begin{tabular}{llrrrrrr}\toprule',
      r'Prompt & Condition & Bytes$\times$ & Calls$\times$ & First p50/p95 & Last real p50/p95 & Traffic p50/p95 & RPC p50/p95\\\midrule'])
    for arm in ('baseline','rules'):
        for c in CONDITIONS:
            r=res['resources'][arm+'|'+c]
            vals=[f"{r[name]['p50']:.1f}/{r[name]['p95']:.1f}" for name in ('first_response_ms','last_real_response_ms','traffic_finish_ms','real_call_ms')]
            supp.append(f"{arm} & {NAMES[c]} & {r['wire_ratio']:.2f} & {r['call_ratio']:.2f} & "+' & '.join(vals)+r'\\')
    supp.extend([r'\bottomrule\end{tabular}',r'\par\smallskip All time columns are milliseconds. The saved results additionally report queue/service times, a descriptive 100 ms per-call deadline count, cell lateness, failures, and paired mean last-response differences.',r'\end{table}'])
    supp.extend([r'\begin{table}[htbp]\centering\footnotesize',
      r'\caption{E13 learned timing/shape detectors on held-out customers, pooling both prompt arms. Flush labels identify records after the online flush declaration; cover labels identify encrypted requests. Ground truth is used only for fitting/scoring, never as an attacker feature.}',
      r'\begin{tabular}{llrrr}\toprule',r'Condition & Detector & BA [95\% CI] & AUROC & Records/requests\\\midrule'])
    for c in ('shadow_serial','shadow_parallel2'):
        for kind in ('flush','cover'):
            r=res['detectors'][c+'-'+kind]
            supp.append(f"{NAMES[c]} & {kind} & {interval(r['ba'])} & {r['auroc']:.3f} & {r['records_or_calls']} "+r'\\')
    supp.extend([r'\bottomrule\end{tabular}',r'\end{table}'])
    return {'r6-main.tex':'\n'.join(main)+'\n','r6-supp.tex':'\n'.join(supp)+'\n'}

if __name__=='__main__':
    for n,s in tables().items():
        path=PKG/'manuscript/tables'/n
        if '--check' in sys.argv:assert path.read_text(encoding='utf-8')==s,n
        else:path.write_text(s,encoding='utf-8',newline='\n')
    print('E13_TABLES_MATCH' if '--check' in sys.argv else 'E13_TABLES_WRITTEN')
