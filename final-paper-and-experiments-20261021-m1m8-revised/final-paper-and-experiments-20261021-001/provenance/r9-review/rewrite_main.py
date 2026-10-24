"""R9 editorial restructuring. Frozen experimental archives stay unchanged."""
from pathlib import Path
O=Path(__file__).resolve().parent;M=O.parents[1]/'manuscript'
def put(rel,s): (M/rel).write_text(s.strip()+'\n',encoding='utf8',newline='\n')
def edit(rel,a,b):
 p=M/rel;s=p.read_text(encoding='utf8');assert a in s,(rel,a[:100]);p.write_text(s.replace(a,b),encoding='utf8',newline='\n')
put('sections/37-transfer-tests.tex',r"""
\section{Four Experimental Demonstrations}\label{sec:controlled-placement}\label{sec:tau-cover-bridge}
Four experiments turn the synthesis into testable comparison obligations: \textbf{(1) emitter placement}, \textbf{(2) execution state and link composition}, \textbf{(3) real-agent operation signatures}, and \textbf{(4) timing and matched traffic controls}. Each holds a boundary fixed while changing the mechanism relevant to that obligation. Table~\ref{tab:r7-cohorts} identifies the three real-agent estimands; Appendix~\ref{app:experiments} maps the modules to archived study identifiers and extensions.

\paragraph{Shared measurement conventions}
A byte-transparent relay captures post-handshake TLS application records on loopback; TLS~1.3 session tickets are disabled. Standard-prompt results use the arm called \texttt{baseline} in the artifact; \emph{undefended} denotes transport without a program defense. Balanced accuracy (BA) averages the two class recalls. We report the maximum over each specified attack suite and recompute that maximum in each of 2,000 common bootstrap draws, grouping tasks for reference-program tests and customers for real-agent tests. The original protocol additionally screens for an upper 95\% BA bound below 0.60 and maximum AUROC below 0.65. We retain this engineering threshold, reporting its interpretation once in \S\ref{sec:validity}.
\input{tables/r9-cohorts}

\subsection{Exp 1: bind protection and cost to the emitter}\label{sec:exp-emitter}
Buffered tests use brief/expanded saved responses for 24 topics (12 training, 12 test). Padding only the upstream link leaves verbosity 100\% separable at a plaintext-aware terminal emitter; padding both reduces BA to 50\%, reproducing NetEcho's mechanism~\cite{netecho2025}. A training-fitted buffered cap achieves 50\% at 2.18$\times$ wire bytes under TLS~1.2 (2.19$\times$ under TLS~1.3).

Streaming the same 48 texts as per-token server-sent events changes the cost contract~\cite{weiss2024prompt,whisperleak2025}. Per-event padding retains token count and 100\% verbosity inference. Eight-token batching cuts bytes to 0.21$\times$ and clean-trained BA to 50\%, yet defended-data refitting restores 100\%. Constant shape reaches 50\% at 2.42$\times$ bytes and 208 versus 105 token intervals; two overflowing test outputs remain identifiable (Table~\ref{tab:transfer-streaming}).
\input{tables/transfer-streaming}
\textbf{Finding.} The same saved content yields different protection and delay under buffering and streaming. A buffered cap's byte ratio cannot price a streaming deployment, whose first-output delay and emission schedule are different outcomes.

\subsection{Exp 2: compose state preservation with link protection}\label{sec:exp-state}
\paragraph{Execution boundary}
In 115 public retail reference programs, same-item modification changes status and appends a refund despite unchanged item and price (173/291 pre-insertion units). Idempotence, $f(f(s,a),a)=f(s,a)$, therefore differs from state preservation, $f(s,a)=s$. Cancelling another user's order changes the shared database. The shadow executor isolates cover effects on a separate state and suppresses its responses; a live-execution control exposes the resulting side effects.

The dispatch observer sees ordered tool names and response lengths. Policies add cancellation, pad its count, interleave donor programs or equalize all tool counts; donors/templates use the known 115-program population. Task-grouped five-fold attacks fit clean/defended gradient boosting and logistic regression on counts, bigrams and lengths, with a count-rule baseline and three seeds (18/32 positive cancellation/return tasks).
\input{tables/r7-e6-main}
One inserted cancellation drives clean-trained BA to chance, while refitting restores 100\%. Count equalization removes that rule's signal, but correlated tools retain 76.9\% BA. Donor programs, inspired by WRA's discarded retrieval cover~\cite{jeong2026wra}, leave 83.5--91.9\%. Shape equalization reaches 50.0/54.5\% at 6.7 extra calls per real call (Table~\ref{tab:r7-e6}). Shadow checks match the original live state in every case; live cancellation changes it in every case.

\paragraph{Final network view}
Four cover policies and three framing choices produce 4,140 TLS~1.2 sessions. The network observer receives direction-tagged record lengths and order. A training-fold profiler maps request sizes to tool types before applying dispatch attacks: request-only identification reaches 89.9/91.4\% (582 calls; majority 29.4\%). Per-call buckets leave return BA at 73.9\%; joint shape cover and constant framing reduce cancellation/return to 54.4/50.0\%, at 26.3$\times$ bytes and 7.7$\times$ calls.

\textbf{Finding.} Call-level cover and per-call framing address complementary observables. Full constant-rate transport can instead hide packet counts from a passive link observer without executing dummy tools~\cite{rfc9347}; Exp~4 measures that alternative. At a dispatch view after decapsulation, cover requires hidden markers and routing to the trusted isolated executor (\S\ref{sec:deployment}). The intervention must match the receiver and the protected state.

\subsection{Exp 3: real-agent signatures and calibrated shaping}\label{sec:real-agent}\label{sec:r5}
\paragraph{Task and collection}
Cancellation and return label the reference program's requested operations, \texttt{cancel\_pending\_order} and \texttt{return\_delivered\_order\_items}. This operational target tests whether encrypted metadata reveals which service action a task requests. GPT-6.1 Sol/low plans from public retail policies, schemas and actual sandbox observations; a separate context simulates the user. Two prompts and three repeats on 115 tasks yield 690 runs from 53 customers. The rules prompt adds a customer-details read before order access and a read before each write.

\paragraph{Frozen calibration and behavioral control}
All 414 training runs (69 tasks) precede freezing shared cover templates, donors and framing caps. The 276 test runs cover 46 tasks from 24 disjoint customers. Prefix-only scheduling inserts training-derived cover, flushing unmet counts at episode end. Four program conditions per prompt give 2,760 local TLS replays with lengths/order attacks; every failure and handoff remains included. Real-call pass-through plus isolated cover preserves the logical response/state projection (Appendix~\ref{app:equivalence}); reusing trajectories pairs the network interventions on identical model decisions.

Rules raise read-order adherence from 86.2\% to 97.1\%, while undefended category inference remains above 93\%. Native rewards are 110/138 and 105/138 (paired difference $-3.6$ points, 95\% interval $[-9.5,1.4]$). Thus compliance and metadata privacy separate in the same task population.
\input{tables/r9-frozen-reference}
Joint cover and framing reach 50.0/50.0\% point BA, compared with 97.2/94.0\% undefended; their upper bounds are 60.6/65.5\%. The paired decreases are 47.2/44.0 points (Table~\ref{tab:r4-primary}). The rules-arm joint return point is 60.6\%, identifying prompt/cohort sensitivity.

\paragraph{Customer-grouped exploratory comparison}
Five-fold cross-fitting refits templates, donors, caps and all attackers on other customers, pooling the full known cohort (14/18 positive customers). The analytic TLS model matches all 2,760 saved sessions and 120 additional captures. An 11-model union includes a 1D-CNN and k-FP-style forest-leaf learner. Joint constant shaping reduces BA by 31.2/30.0 points (paired 95\% intervals [15.3,41.0]/[14.8,39.2]); buckets reduce it by 34.6/32.8 points, at lower byte cost (Table~\ref{tab:r5}).
\input{tables/r9-crossfit}

\paragraph{Locate the observable operation signature}
An oracle selects write exchanges using true tool types, then exposes only ciphertext lengths/order. Writes comprise 19.6\% of real calls yet retain 91.7/84.9\% BA; removing them leaves 62.8/59.9\% (Table~\ref{tab:r7-e12}). The target names an operation, so the result locates its metadata signature. It directs protection toward specific exchanges, while residual read inference shows why hiding one named call is insufficient.
\input{tables/r9-localization}
\textbf{Finding.} Better read-order compliance leaves operation inference intact; calibrated joint shaping reduces that fitted-suite inference; and the localization identifies which exchanges carry it. Semantic-attribute generalization is a separate estimand, tested by the small extension summarized in Appendix~\ref{app:experiments}.

\input{sections/42-live-timing-main}

\paragraph{Synthesis}
The demonstrations operationalize the audit: match the emitter before borrowing a byte cost (Exp~1), verify executed state before borrowing a cover strategy (Exp~2), bind targets and calibration to a shared cohort (Exp~3), and price timing protection against matched transport alternatives (Exp~4). They show how source-bound comparisons change a concrete deployment decision.
""")
put('sections/42-live-timing-main.tex',r"""
\subsection{Exp 4: timing, latency and matched transport controls}\label{sec:live-timing}\label{sec:r7-main}
All 690 saved action trajectories execute through a live local tool server under six conditions, producing 4,140 new TLS sessions. Each real response gates the next action; real and shadow calls have separate states. The original 414/276 customer-disjoint split is retained, with attacks fitted and frozen before test capture. Lengths, directions and arrival times measure the tool RPC chain.

A complete tunnel sends 4,096-byte cells in both directions at 2 or 5\,ms target intervals; dummy cells execute no tools. A training-sized 133-slot horizon continues after the last response. Serial and two-in-flight shadow schedules use the frozen prefix-only count policy with constant per-call framing. The attack union includes size/order, timing, combined features and learned flush removal. Seven shared learners, including a 1D-CNN and forest-leaf neighbors, also permit a matched comparison with offline website-fingerprinting (WF) adaptations.
\input{tables/r9-controls}

\paragraph{Timing reveals distinguishable cover}
For standard-prompt serial shadow, adding timing/flush attacks increases cancellation BA from 50.0\% to 61.4\% (paired increase 11.4 points, 95\% interval [3.7,19.6]); return changes from 50.7\% to 53.4\%. Flush-phase detection reaches 90.4/92.3\% for serial/parallel schedules over 15,278 records from 276 test episodes. A separate cover-versus-real request classifier reaches 82.5/96.1\% on 7,639 requests.

We then compose the detector with intent inference: a training-fitted detector strips the predicted suffix before classification. Table~\ref{tab:r8-flush} shows the recovered category signal, with a strongest return point of 60.7\%. The full attack union retains both stripped and unstripped traces. This separates the ability to recognize padding phases from the ability to recover a task's operation.
\input{tables/r9-flush}

\paragraph{Match cost to the protected boundary}
Measured real-chain p95 latency is 26.2/20.8\,ms for serial/two-in-flight shadow, versus 56.4/112.3\,ms for 2/5\,ms tunnels. Sessions preserve real responses and final live state; fixed tunnel sizes/counts still expose host-scheduled direction/order. Table~\ref{tab:r7-controls} keeps measured RPC times separate from offline schedule transformations.

Under the common seven attacks, random-donor Walkie-Talkie (WT) reaches 50.0/56.7\% BA at 2.04$\times$ bytes, versus serial shadow's 50.0/52.9\% at 15.11$\times$. WT also matches or improves both BA points, bytes and calls over parallel shadow; under rules, its 51.4/56.3\% at 2.23$\times$ improves those four point metrics over both shadow schedules. These measured point trade-offs motivate choosing protection at the narrowest required boundary.

The WF adapters use the same saved traffic and training customers. WT samples donor traces without symmetric site pairing; WTF-PAD samples training inter-arrival histograms; Tamaraw and FRONT supply fixed-rate and front-loaded controls. Input-derived fragments preserve sizes, directions and order, enabling a controlled metadata comparison. Their simulated spans and measured RPC latency remain separate cost objects.

\textbf{Finding.} A length-only verdict misses schedule leakage, and expensive shadow execution has no measured network-efficiency advantage over all transport alternatives. For a passive ingress-link observer, lightweight shaping is a relevant candidate; for a restricted dispatch observer, execution isolation addresses an additional state boundary. This is the audit's placement-and-cost distinction demonstrated on one workload.
""")
put('tables/r9-audit-rules.tex',r"""
\begin{table}[t]\centering\footnotesize
\caption{Operational rules for the nine reuse bindings. Apply each item to a specified result record and deployment claim.}\label{tab:audit-rules}
\begin{tabularx}{\columnwidth}{@{}lY@{}}\toprule
Item & Evidence required for a Bound (B) judgment\\\midrule
R1 Target & Hidden property, inference goal and authorized/protected interest are explicit.\\
R2 Receiver & Observer permission, released representation and auxiliary inputs identify the evaluated view.\\
R3 Intervention & Placement and execution mode bind the transform to stored data, wire emission or executed actions.\\
R4 Protected fit & Attacker fitting/calibration uses the protected condition; training and protected testing are identified.\\
R5 Matched adaptation & Clean- and protected-condition fits are evaluated on the same defended test population.\\
R6 Workload & Tasks, system/generator configuration and holdout specify the supported transfer axis.\\
R7 Inference & Metric, denominator and evaluation condition bind the attack outcome to the scoped mechanism.\\
R8 Utility & Task/component performance is measured at the same protected operating point, with its state boundary explicit.\\
R9 Cost & Resource units, baseline and measurement object price that operating point.\\\bottomrule
\end{tabularx}
\par\smallskip\raggedright B: bound; P: partial binding; U: unreported in inspected scope; A: source unavailable; ?: binding unverified; --: inapplicable. First determine applicability, then assign evidence status. Family B means at least one scoped record satisfies the item, not that every result does.
\end{table}
""")
edit('main.tex',r'\newcommand{\NRR}{\textsc{nr-r}}',r'\newcommand{\NRR}{\textsf{U}}')
edit('main.tex',r'\newcommand{\NRA}{\textsc{nr-a}}',r'\newcommand{\NRA}{\textsf{A}}')
edit('main.tex',r'\newcommand{\NRV}{\textsc{nr-v}}',r'\newcommand{\NRV}{\textsf{?}}')
edit('main.tex',r'\newcommand{\NA}{\textsc{na}}',r'\newcommand{\NA}{--}')
edit('main.tex',r'\input{sections/30-reproducibility-guide}',r'\input{sections/30-reproducibility-guide}'+'\n'+r'\input{sections/49-r9-record-index}'+'\n'+r'\input{sections/50-r9-experiment-index}'+'\n'+r'\input{sections/51-r9-extensions}')
p=M/'sections/27-intervention-contracts.tex';s=p.read_text()
s=s.replace('S18 maps every family and record.','Appendix~\\ref{app:records} lists all 39 records with source locators; Table~\\ref{tab:core-family-map} covers all 58 families.').replace('; Supplement S8','')
s=s.replace(" (the supplied 50-pair subsample, not all 102 pairs, has 94.0\\% agreement across its 150 judgments, $\\kappa=0.916$)","")
a=s.index('Table~\\ref{tab:family-audit} reports all 180');b=s.index('\\input{tables/family-audit-matrix}',a)
s=s[:a]+r"""Table~\ref{tab:audit-rules} defines each item before its application to the 180 cells in Table~\ref{tab:family-audit}. Applicability follows the result's reuse claim: a fixed analytical attack can make adaptation inapplicable, while a component benchmark can support component utility. U and ? retain distinct source states. The 11 unresolved adaptation cells comprise five R4 and six R5 bindings, explicitly distinguished from an attack failure.
\input{tables/r9-audit-rules}
"""+s[b:]
s=s.replace('Full cell dispositions and reasons are in Supplement S18.','The record index in Appendix~\\ref{app:records} identifies the underlying operating points.')
p.write_text(s,encoding='utf8',newline='\n')
edit('tables/family-audit-matrix.tex',r'R1 target/polarity; R2 receiver; R3 placement/execution; R4 defended-condition fit; R5 matched adaptation; R6 workload/generator shifts; R7 inference; R8 utility; R9 cost.',r'Table~\ref{tab:audit-rules} defines R1--R9 and the shared status alphabet.')
edit('tables/family-audit-matrix.tex','Source follow-up resolves three former ? cells: cloud-traffic R3 to B; Shape and Substance R4/R5 to U (S8).','Source follow-up resolves cloud-traffic R3 to B and Shape and Substance R4/R5 to U.')
copies={'r8-cohorts':'r9-cohorts','r8-frozen-reference':'r9-frozen-reference','r8-crossfit':'r9-crossfit','r7-e12-main':'r9-localization','r8-controls':'r9-controls','r8-flush':'r9-flush'}
for old,new in copies.items():
 s=(M/'tables'/f'{old}.tex').read_text()
 s=s.replace('E9/E13','Frozen split / RPC').replace('E13/14','Exp 4').replace('E13/E14','Exp 4').replace('E9','Exp 3 frozen').replace('E10','Exp 3 cross-fit').replace('E12','Exp 3').replace('E13','Exp 4')
 s=s.replace('Joint-design absolute-criterion outcomes remain inconclusive.','').replace('All full-union two-target gates remain unconfirmed.','')
 s=s.replace('Full methods, intervals and prompt contrasts: Supplement S14.','Reward is measured on original trajectories and inherited by program transforms; see the utility scope in \\S\\ref{sec:validity}.')
 s=s.replace('Every bootstrap draw reselects the complete maximum; S21 reports both prompts, AUROC and paired reductions.','Every bootstrap draw reselects the complete maximum. Intervals condition on fitted predictions.')
 s=s.replace('Ratios use prompt-specific undefended captures; S20/S23 give both prompts, interval and finish-time details. No row measures live defended-planner utility.','Ratios use prompt-specific undefended captures. The utility scope is defined in \\S\\ref{sec:validity}.')
 s=s.replace('The 690 runs are repeated execution coverage, not 690 independent customers.','Repeats measure execution variation within these customer groups.')
 put(f'tables/{new}.tex',s)
print('MAIN_FOUR_MODULES_AND_RULES_WRITTEN')
