from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent/'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001'
M=P/'manuscript';A=P/'experiments/reviewer-audit'
def write(f,s):(M/f).write_text(s.strip()+'\n',encoding='utf-8')
g=json.loads((A/'tls_gradient.json').read_text());e=json.loads((A/'tls_adaptive.json').read_text())
def pct(x):return f'{100*x:.1f}'
s=r'''\begin{table}[!t]\centering\footnotesize
\caption{Corrected TLS application-record results. Costs use each workload's own unprotected texts (all 48 outputs); accuracy uses 24 test outputs in 12 topics. Intervals resample topics.}
\label{tab:controlled-placement}
\setlength{\tabcolsep}{2.2pt}
\begin{tabularx}{\columnwidth}{@{}Yrrr@{}}\toprule
\multicolumn{4}{@{}l}{\textbf{A. Two-link placement (T1; retained experiment)}}\\
Protection & Upstream acc. & Terminal acc. & Terminal bytes\\\midrule
None & 100.0 & 100.0 & 720.96\\
Upstream only & 50.0 & 100.0 & 720.96\\
Both, loose cap & 50.0 & 50.0 & 16,848\\\midrule
\multicolumn{4}{@{}l}{\textbf{B. Matched workload costs and defended-fit accuracy}}\\
Workload / framing & Mean bytes & Ratio & Acc. (\%)\\\midrule
'''
for regime in ['T1','T2','T3','T4']:
    ps=['unpadded','bucket_256','bucket_512','bucket_1024']
    if regime=='T1':ps+=['train_cap','fixed_16848']
    if regime=='T4':ps=['unpadded']
    names={'unpadded':'unprotected','bucket_256':'256B bucket','bucket_512':'512B bucket','bucket_1024':'1024B bucket','train_cap':'training-fitted cap','fixed_16848':'loose cap'}
    for pol in ps:
        r=next(x for x in g if x['regime']==regime and x['policy']==pol)
        s+=f"{regime}: {names[pol]} & {r['mean_wire_bytes']:,.2f} & {r['matched_ratio']:.2f} & {pct(r['accuracy_ci95'][0])}"+r'\\'+'\n'
s+=r'''\midrule
\multicolumn{4}{@{}l}{\textbf{C. Adaptation on identical defended T1 tests}}\\
Defense & $D_0$ (\%) & $D_2$ (\%) & Gain [95\% CI], pp\\\midrule
'''
names={'offset_512':'+512B offset','bucket_1024':'1024B bucket','stoch_u512':r'$U(0,512)$B','stoch_u1024':r'$U(0,1024)$B','fixed_16848':'Loose cap','train_cap':'Training-fitted cap'}
for r in e:
    gain=r['gain'];s+=f"{names[r['policy']]} & {pct(r['D0'][0])} & {pct(r['D2k12'][0])} & {pct(gain[0])} [{pct(gain[1])}, {pct(gain[2])}]"+r'\\'+'\n'
s+=r'''\bottomrule\end{tabularx}
\par\smallskip\raggedright\footnotesize
Panel C uses 12 training pairs. Four-pair accuracy is the same except under $U(0,1024)$B, where it is 90.2\%. Random padding averages 50 draws within each topic; these are not 50 independent corpora. T2/T3 are sentence-prefix constructions. T4 relabels both original response lengths and has a 58.3\% test majority baseline. The cap equalizes only the specified record-length projection when no message overflows.
\end{table}'''
write('tables/controlled-placement.tex',s)

cs=json.loads((A/'scenario_confusions.json').read_text())['matrices']
s=r'''\begin{table}[t]\centering\footnotesize
\caption{Author-constructed scenario exercise: complete confusion matrices. Each triple gives predictions (Compatible, Incompatible, Unresolved) for the indicated true category. The last two columns distinguish detecting mismatches from retaining compatible reuse.}\label{tab:m1-validity}
\setlength{\tabcolsep}{2pt}
\begin{tabularx}{\columnwidth}{@{}Yccccc@{}}\toprule
Procedure & True C & True I & True U & I recall & C recall\\\midrule
'''
for key,label in [('headline_baseline_pred','Always C'),('always_incompatible','Always I'),('always_unresolved','Always U'),('expert1_3check_pred','Coder column 1'),('expert2_3check_pred','Coder column 2')]:
    a=cs[key];s+=label+' & '+' & '.join(','.join(map(str,row)) for row in a)+f' & {100*a[1][1]/12:.1f} & {100*a[0][0]/7:.1f}'+r'\\'+'\n'
s+=r'''\bottomrule\end{tabularx}
\par\smallskip\raggedright This illustrates the recorded labeling exercise; scenarios and labels were not independently held out. C recall is specificity when Incompatible is the positive class and evaluation is restricted to the C/I subset. Unresolved is retained as a third outcome.
\end{table}'''
write('tables/scenario-confusions.tex',s)

# Complete compressed family inventory with actual citations, rather than only nocite.
rows=list(csv.DictReader((P/'evidence/retained-release007/search-update/final-family-index.csv').open(encoding='utf-8-sig')))
assert len(rows)==82
s=r'''\paragraph{Complete indexed-family citation inventory}
The following citation groups enumerate all 82 indexed families. Categories are core eligibility and origin, not mutually exclusive threat objectives. The machine-readable index binds each key to its source version and locators.
'''
for label,subset in [('Core', [r for r in rows if r['classification']=='core']),('Adjacent',[r for r in rows if r['classification']!='core'])]:
    keys=[r['citation_key'] for r in subset]
    s+=label+f' ({len(keys)} families): '+r'\cite{'+','.join(keys)+r'}.'+'\n\n'
write('tables/corpus-citations.tex',s)

write('sections/29-scope-comparison-boundary.tex',r'''
\section{Retained Indexing Experiment and Scenario Illustration}\label{app:scope-workflow-boundary}
The retained model-assisted experiment compares flat checklist R, structured checklist T and raw \scope{} traversal V. There are 512 roots per arm and three query judgments per root (1,536 judgments). The endpoint is the mean of each root's three binary joint outcomes, requiring a correct deployment decision and exact configuration counts. R has 624 joint successes (40.63\%); V has 494 (32.16\%). T has 693 observed successes and three missing queries belonging to one root, giving the retained 45.12--45.31\% missing-outcome range. V is worse on this joint endpoint; this is retained negative evidence.

Decision-correct but count-incorrect judgments number 537 (R), 476 (T) and 695 (V), out of 1,536 query opportunities. Observed queries have no schema/evidence-ID failures. Binary-decision successes are 1,161 (R), 1,169 (T, plus three missing) and 1,189 (V). The 1.11--1.30 percentage-point V--T binary difference is a secondary post-outcome decomposition, not proof of a better workflow. Counts are query judgments, not independent roots; percentages average three judgments per root. We do not infer causality from the error decomposition.

The separate 24-scenario exercise uses author-constructed source-reuse cases and author labels. Seven are Compatible, twelve Incompatible and five Unresolved. Its two supplied coder columns match 23/24 and 22/24 labels and agree on 21/24. The original headline rule is always Compatible (7/24); always Incompatible gives 12/24 and always Unresolved 5/24. No accuracy advantage over an informative, equal-information comparator is claimed. All three-category confusion matrices are in \path{experiments/reviewer-audit/scenario_confusions.json}. Independent construction, blinding and out-of-corpus validation remain unperformed.
''')

write('sections/33-controlled-details.tex',r'''
\section{Controlled Replay Details and Revised Accounting}\label{app:controlled-details}
The current experimental source is \path{experiments/reviewer-audit/recompute.py}, with the instrumented retail implementation in \path{retail_replay.py}. Historical inputs and previous summaries are retained unchanged; revised JSON files take precedence for the current manuscript. No fresh model generations were requested.

\paragraph{TLS corpus and length accounting}
The 48 saved outputs comprise 24 brief/expanded pairs. Training and testing each contain 12 topics and 24 outputs. T1 uses the original verbosity labels. T2 retains brief responses and takes the first two period-delimited sentences of expanded responses. T3 uses the first two and first three sentences of each expanded response. T4 retains both original outputs per topic and labels their domain. There is one generation per prompt, not repeated model sampling. T4 has 14 positive and 10 negative test outputs (seven versus five topics), so 50\% is not its empirical majority-class baseline.

For every regime and framing policy, \path{tls_records.json} saves topic, split, label, plaintext bytes, application-record count, payload bytes, wire bytes and recovered plaintext hash. \path{tls_gradient.json} reports absolute means and matched denominators. All 48 texts are used for cost means; only 24 held-out outputs are used for accuracy. A record contains five TLS header bytes plus 24 encryption-overhead bytes under the pinned TLS~1.2 suite. Handshake traffic, TCP/IP and timing are outside this cost scope. Bucket 1024 uses four 256-byte writes per quantum, hence 1,140 rather than 1,082 wire bytes per quantum. Buckets 256/512 use 128-byte writes.

The training-fitted cap rounds the maximum framed training length, 1,194 bytes, up to 1,280 bytes. It emits ten records of 128 bytes (1,570 wire bytes). Overflow adds 128-byte frames, never truncates, and leaks an overflow-dependent length; none of the saved test responses overflows. The loose 16-record, 1,024-byte-per-record control is 16,848 wire bytes and is not a lower bound on protection cost.

Cohen's absolute standardized mean difference, recomputed across the 48 constructed plaintext lengths using pooled sample variance, is 12.264 (T1), 5.723 (T2), 3.418 (T3) and 0.033 (T4). Previous values embedded in regime labels were not produced by that calculation and are withdrawn. These descriptive values are not entropy, independent tests or a model of required framing cost.

\paragraph{Adaptive fitting and bootstrap hierarchy}
The clean threshold is fitted to training TLS payload bytes. The defended thresholds use the first four or all twelve training topic pairs. The 1024B defended threshold is 1,680 TLS payload bytes. Stochastic padding has 50 draws; the first is measured on sockets and 49 are calculated using socket-checked record accounting. The independent resampling unit is one of 12 test topics. For each topic, correctness or paired gain is averaged across its two outputs and all draws before 10,000 percentile-bootstrap resamples (seed 20261021). We do not refit the model in that bootstrap or infer uncertainty across fresh model generations. Stored per-topic/per-draw correctness permits exact reconstruction. Both constant caps give a constant specified length sequence without overflow; this says nothing about unobserved timing or metadata.

\paragraph{Retained synthetic tool control}
The original 24 saved inventory/calendar programs are a separate synthetic demonstration. Discard, shadow and read-only routes preserve the prescribed states by construction; 9/24 live-write runs meet both the narrow goal and protected-bystander condition. This is not evidence for autonomous-agent planning or safe deployment of destructive cover.

\input{sections/36-tau-cover-details}
''')
print('TLS, scenario, corpus and supplement tables generated')
