"""Generate only the new R8 supplementary empirical audit, from saved results."""
import json
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parents[1]
C=json.loads((P/'experiments/sp2027-r8-cluster-sensitivity/results.json').read_text())
A=json.loads((O/'defense-self-audit.json').read_text())
lines=[r'''\section{R8 Construct validity and evidence calibration}\label{sec:r8-empirical-audit}
This appendix applies the paper's evidence requirements to its own experiments. It adds deterministic sensitivity calculations on saved predictions, not new model runs, customers or defense deployments. The separate analysis plan and code hashes were frozen before these new calculations; the original test predictions were already available, so this remains post hoc.

\subsection{Customer composition and fixed-attacker sensitivity}
The complete out-of-fold prediction collection contains 690 original model trajectories, re-used across conditions and targets. Each prompt-specific cell contains 345 trajectories (115 tasks, three repetitions), but only 53 customers. Cancellation has 54 positive trajectories from 18 tasks and 14 customers; return has 96 from 32 tasks and 18 customers. These full-cohort positive-customer counts differ from the original held-out subset's five/seven. Repetitions, prompts and transformed views do not create additional independent customers.

For each of the 11 saved attackers, episode-weight BA pools correctness within each true class. The sensitivity estimand first averages correctness within each customer/class stratum, then equally weights customers within each class and finally the two class rates. The four cancellation and eight return mixed-label customers contribute separately to both class rates; they are neither discarded nor forced to have one customer-level label. Suite maxima are independently reselected under both weightings. Thresholds and predictions remain fixed.

\begin{table*}[ht]\centering\footnotesize
\caption{Fixed-prediction cluster sensitivity for the complete OOF cohort. BA and leave-one-positive-customer-out ranges are percentages. Each row has 345 trajectories and 53 customers. Every deletion removes the customer's negative tasks as well as positive tasks; all 14/18 deletions remain valid for cancel/return. Ranges are deterministic influence ranges, not confidence intervals.}\label{tab:r8-cluster-sensitivity}
\begin{tabular}{@{}lllrrrr@{}}\toprule
Prompt & Condition & Target & Episode BA & Customer-equal BA & LOO episode range & LOO customer-equal range\\\midrule''']
names={'undefended':'Undefended','jointbucket1024':'Joint bucket','jointconstant':'Joint constant'}
for k,v in C['cells'].items():
    arm,cond,target=k.split('|');m=v['metrics'];rr=v['deletion_ranges']
    def rg(n):return f"{100*rr[n]['min']:.2f}--{100*rr[n]['max']:.2f}"
    lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} & {names[cond]} & {target} & {100*m['episode_weight']['suite_max_ba']:.2f} & {100*m['customer_equal_within_class']['suite_max_ba']:.2f} & {rg('episode_weight')} & {rg('customer_equal_within_class')}"+r'\\')
lines+=[r'''\bottomrule\end{tabular}\end{table*}

Weighting changes the estimand and moves different cells in different directions; it is not a universal correction in favor of either defense. Positive-customer deletion exposes concentration in particular customers. Neither calculation removes that customer's influence on models trained in other folds: no attacker is refitted. Thus these results condition on the saved fitted attacks and do not include retraining uncertainty, an independent population, or uncertainty induced by prior development access to the public tasks. We do not pool scores into one customer-level classifier because task labels can differ within a customer. The complete per-attack, per-customer/class and per-deletion values, including remaining denominators, are saved in \texttt{sp2027-r8-cluster-sensitivity/results.json}; an independent direct-weight verifier checks all 12 cells and 192 deletions.

\subsection{Applying R1--R9 to our own evidence}
Table~\ref{tab:r8-own-evidence} distinguishes a bound measurement from an unverified extension. In particular, a structural planner-history invariant, measured fixed-action response/state equality, and live LLM task utility are different outcomes. Inherited native reward does not count as utility measured under the defended operating point.

\begin{table*}[ht]\centering\footnotesize
\caption{Scoped self-audit of E9/E10/E13/E14/E15 under R1--R9. Entries describe evidence boundaries, not overall success grades. The missing live defended-LLM utility binding is retained for our experiments under the same standard applied to the source corpus.}\label{tab:r8-own-evidence}
\begin{tabularx}{\textwidth}{@{}lYY@{}}\toprule
Item & Bound or partially bound observation & Unverified extension\\\midrule
R1: target/polarity & Privacy inference of cancel/return action-labelled task trajectories & Unobserved psychological intent or a general semantic secret\\
R2: receiver & E9/E10/E15 dispatch or TLS length/order; E13 local arrival timing & Production provider logs, routing leaks and unmeasured observers\\
R3: placement/execution & E13 executes tools on fixed saved actions; E14 separates measured and offline rows & Live LLM replanning under cover; executing WF transforms as production defenses\\
R4: defended fitting & Training-only calibration and condition-specific attack fitting; E15 fits only 58 training trajectories & Arbitrary attacker strength or prospective parameter freeze for E15\\
R5: matched adaptation & Defended-data attackers; common-seven condition comparison in E14 & A fully matched clean-versus-adapted causal contrast from every D2/union difference\\
R6: workload shifts & Customer splits/cross-fitting, two prompts and same-provider Luna retail alias & New customers, new environment, independent vendor or blinded confirmation\\
R7: inference & Saved suite maxima, customer intervals, failures and negative outcomes retained & An absolute bound against unknown attackers or success inferred from a low point estimate\\
R8: utility & Original LLM rewards; E13 measured real-response/final-state equality on fixed actions & Live defended LLM task utility; timing-dependent replanning, quotas and failures\\
R9: cost & E13 local tool-chain cost; E14 matched byte/call accounting with separate simulated clocks & End-to-end deployed cost or a common live latency ranking across measured/simulated rows\\
\bottomrule\end{tabularx}\end{table*}

E9/E10 program conditions inherit reward from reused trajectories. E13 additionally checks real responses and final live database states in all 4,140 local sessions, but the next action is specified by the saved trajectory rather than a new LLM decision. E14's offline WF adapters preserve abstract fragment identity/order and do not schedule fragments before input availability; they neither decrypt and compare payloads nor execute tools. Their copied native rewards are not independent utility measurements. E15's actual 150-task rewards and wall clocks describe the original collection service, not planner behavior under cover. Own live defended-LLM utility therefore remains unbound.

\subsection{Matched-seven comparison and the limits of dominance}
All rows in Table~\ref{tab:r8-matched-seven} use the same seven attack families: majority, logistic, gradient boosting, random forest, extra trees, leaf fingerprint and sequence CNN. BA and AUROC suite maxima are separately reselected in each customer-bootstrap draw. The measured conditions retain additional E13 attacks in the full-union assessment elsewhere; this common subset cannot replace that stronger assessment. The exact values, intervals, full-union values and cost denominators are retained in \texttt{provenance/r8-review/defense-self-audit.json}.

\begin{table*}[ht]\centering\footnotesize
\caption{Both prompts under the matched seven-model subset. BA is cancel/return in percent. Bytes and dispatch counts use the corresponding prompt's undefended totals; per-prompt evaluation has 138 trajectories and 24 customers. WT is the random-training-donor RPC adaptation, not the original symmetric-pair guarantee. No row establishes live defended-LLM utility.}\label{tab:r8-matched-seven}
\begin{tabular}{@{}llrrrr@{}}\toprule
Prompt & Condition & Cancel/return BA & Bytes$\times$ & Calls$\times$ & Execution\\\midrule''']
conditions={'walkie_talkie':'WT random donor','shadow_serial':'Serial shadow','shadow_parallel2':'Two-in-flight shadow','tunnel_2ms':'Full tunnel 2 ms','tunnel_5ms':'Full tunnel 5 ms'}
for arm in ['baseline','rules']:
    for cond,name in conditions.items():
        cc,rr=[r for r in A['matched_rows'] if r['prompt']==arm and r['condition']==cond]
        lines.append(f"{'Standard' if arm=='baseline' else 'Rules'} & {name} & {100*cc['common_ba']:.2f}/{100*rr['common_ba']:.2f} & {cc['wire_ratio']:.3f} & {cc['call_ratio']:.3f} & {'Offline' if cond=='walkie_talkie' else 'Local tools'}"+r'\\')
lines+=[r'''\bottomrule\end{tabular}\end{table*}

WT's lower byte and backend-call cost is a real advantage of the evaluated adaptation. For standard prompts it exchanges lower cost for higher return BA than serial shadow (56.67\% versus 52.86\%); neither point dominates the other. For rules, WT has lower point BA on both targets and lower byte/call cost than either shadow scheduler. It also weakly dominates the standard two-in-flight point in these four dimensions. These are descriptive point relations, not statistically certified or deployment dominance: they exclude AUROC and latency, intervals are wide, and the WT schedule is simulated while the shadow tool chain is measured. A claim including AUROC can change the ordering. Tunneled dummies execute no tools; the two fixed local tunnel operating points trade much larger byte cost for no extra backend calls, without establishing an optimal tunnel configuration. The evaluated shadow policy is therefore not presented as Pareto-superior to these controls.

\paragraph{What flush recognition establishes.}
The E13 serial/parallel flush detectors achieve 90.45/92.31\% BA on 15,278 record labels (8,902 after the declared flush start, 6,376 before), pooling 276 trajectories and 24 customers across prompts. This is schedule-phase recognition, not intent recovery. Separate real/cover request detection reaches 82.53/96.08\% BA on 7,639 requests. These observations refute cover-indistinguishability for the measured scheduler/view. Already-saved attacks estimate a single flush boundary using a training-fitted detector, with customer-out-of-fold segmentation for intent training, then attack the remaining prefix. The highest such intent BA is 60.69\% (rules serial return, 95\% interval [50.83,70.95]); the unstripped views remain in the complete suite. Recognizable flush does not imply 90\% intent recovery, and the relatively low stripped-view points do not erase the stronger unstripped attacks or certify defense success.
''']
destination=P/'manuscript/sections/47-r8-empirical-audit.tex'
destination.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(destination.name,'GENERATED_FROM_SAVED_RESULTS')
