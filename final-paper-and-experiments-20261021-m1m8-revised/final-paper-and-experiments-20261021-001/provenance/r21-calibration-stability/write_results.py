"""Generate all R21 reporting cells from verified saved statistics."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';D=P/'experiments/sp2027-r21-calibration-stability'
data=json.loads((D/'summary.json').read_text());assert data['replicates']==100
NAMES=['sp2027-r11-minimax','sp2027-r12-glm'];names=dict(zip(NAMES,['MiniMax','GLM']))
def interval(x,scale=100):return '['+', '.join(f'{scale*v:.1f}' for v in x)+']'
def st(target,source,regime,label):return next(x for x in data['stability'] if (x['target'],x['source'],x['regime'],x['label'])==(target,source,regime,label))
def ct(target,regime,label):return next(x for x in data['contrasts'] if (x['target'],x['regime'],x['label'])==(target,regime,label))
def write(rel,text):(M/rel).write_text(text.rstrip()+'\n',encoding='utf8',newline='\n')

main=r'''\begin{table*}[t]\centering\footnotesize
\caption{Calibration source, localized padding and training sensitivity. Top: original 46 test tasks / 24 customers per endpoint; $\Delta$ is the seven-attack max-BA contrast against target-local joint shaping (points). Bottom: 100 paired training-customer resamples, evaluated on the same fixed tests.}\label{tab:calibration-transfer}
\begin{tabularx}{\textwidth}{@{}lYrrrrrr@{}}\toprule
Target & Calibration / intervention & Cancel BA & Return BA & $\Delta$ cancel & $\Delta$ return & Bytes$\times$ & Calls$\times$\\\midrule
MiniMax & MiniMax joint & 60.4 & 67.5 & -- & -- & 20.06 & 3.36\\
MiniMax & GLM joint & 50.8 & 63.0 & $-9.6$ & $-4.5$ & 17.48 & 3.11\\
MiniMax & Write padding & 50.0 & 61.3 & $-10.4$ & $-6.2$ & 1.45 & 1.00\\
GLM & GLM joint & 50.0 & 67.3 & -- & -- & 15.95 & 4.24\\
GLM & MiniMax joint & 70.8 & 50.0 & $+20.8$ & $-17.3$ & 18.65 & 4.66\\
GLM & Write padding & 60.0 & 61.6 & $+10.0$ & $-5.7$ & 1.51 & 1.00\\\bottomrule
\end{tabularx}
\smallskip
\begin{tabularx}{\textwidth}{@{}llYYY@{}}\toprule
Target & Label & Local recalibration BA: 95\% spread & Imported $-$ local $\Delta$: median [95\% spread] & Same $\Delta$ with attacker resampling: median [95\% spread]\\\midrule
'''
for n in NAMES:
    for lab in ['cancel','return']:
        s=st(n,n,'calibration_only',lab);c=ct(n,'calibration_only',lab)['fixed_test'];j=ct(n,'calibration_and_attacker',lab)['fixed_test']
        main+=f"{names[n]} & {lab} & {interval(s['percentiles95'])} & {100*c['median']:+.1f} {interval(c['percentiles95'])} & {100*j['median']:+.1f} {interval(j['percentiles95'])} \\\\\n"
main+=r'''\bottomrule\end{tabularx}
\par\smallskip\raggedright Original eight customer-paired contrasts: 99,999 whole-suite swaps each, Holm-adjusted $p=1.000$ throughout. Historical nominal intervals remain in the supplement. Resampling spreads measure training sensitivity, not confidence in a population effect. All seven attacks (including decoding and call counts) are refitted per condition. Costs are summed local TLS test bytes/calls relative to raw target totals; they exclude live planner utility and WAN delay.
\end{table*}'''
write('tables/r14-calibration-transfer.tex',main)

section=r'''\section{Calibration Source and Training-Customer Sensitivity}\label{sec:calibration-stability}
\paragraph{Question and design}
The opposite GLM point changes ($+20.8$ cancellation and $-17.3$ return BA points) describe a target-dependent operating point. They do not isolate a causal model-source effect: changing source calibration also changes a finite training sample's templates, caps and donors. We therefore add a local-recalibration baseline and an attacker-only baseline. This post hoc protocol fixed 100 replicate seeds and the complete seven-attack endpoint suite before the new results. The source inputs, plan and implementation are hashed. No model calls, new customers or new task outcomes are added.

Each replicate draws 29 training customers with replacement and retains all their tasks, using identical customer draws for the two source endpoints. All 24 original test customers remain disjoint. Duplicate customer selections weight episode-derived calibration lengths; the original donor deduplication and fixed cover random seeds are retained. Donor pool ordering follows the resampling order. The original calibration helper's allowed-task list remains distinct from the actual sampled tasks, which are archived explicitly. The resulting training sample can contain a different number of episode occurrences from the original 69 tasks.

Both calibrations are applied to all 115 saved trajectories from each endpoint, producing 460 fresh local TLS 1.2 captures per replicate and 46,000 captures overall. Attacks fit only target training trajectories. Each fit includes majority, clean-trained gradient boosting, defended-data logistic regression and gradient boosting, decoded-tool gradient boosting, decoded target-call count and total exchange count. The decoder and count thresholds are refitted. These are length/direction experiments, with no reconstructed timing or new live-planner measurements.

\paragraph{Three sensitivity regimes}
\emph{Calibration only} rebuilds the defense and refits attacks on the full original target training population. \emph{Calibration plus attacker} also resamples training customers for attack fitting, independently of the calibration draw but paired across conditions. \emph{Attacker only} refits attacks on the original frozen local-calibration captures. Single-class training fits retain the draw and use constant predictions. Fixed-test percentile ranges measure pipeline sensitivity; they are not population confidence intervals. Original results are preserved, and the new implementation reproduces both original calibrators and all 84 original seven-attacker prediction arrays exactly.

\paragraph{Conditional permutation tests and multiplicity}
The original table has eight target-level contrasts: two endpoints, two interventions relative to local joint shaping, and two labels. For each contrast we perform 99,999 seeded customer-level swaps of the entire seven-attacker condition prediction vector; all tasks of a customer move together. We reselect each suite maximum and use the absolute difference as a two-sided statistic with the plus-one Monte Carlo correction. Holm adjustment covers all eight contrasts. The null is conditional exchangeability of prediction vectors within customers, not a randomized causal model-source intervention. A small clustered example is checked against complete swap enumeration.

\begin{table}[ht]\centering\small
\caption{Original contrasts under customer-paired permutation tests. $\Delta$ is intervention minus local joint max-BA in points.}\label{tab:r21-permutation}
\begin{tabular}{lllrrr}\toprule
Target & Intervention & Label & $\Delta$ & Raw $p$ & Holm $p$\\\midrule
'''
for x in data['conditional_tests']:
    cond='Imported joint' if x['condition']=='transferred_joint' else 'Write padding'
    section+=f"{names[x['target']]} & {cond} & {x['label']} & {100*x['delta']:+.1f} & {x['permutation_p']:.5f} & {x['holm_p']:.3f} \\\\\n"
section+=r'''\bottomrule\end{tabular}\end{table}
The earlier return percentile interval excluded zero, whereas the paired permutation test gives $p=0.174$ before adjustment. These are different inferential constructions for a nonsmooth maximum over fitted attacks in a small clustered sample. We retain the historical intervals for traceability and withdraw the earlier ``resolved return reduction'' interpretation. None of the eight contrasts is resolved by the corrected tests; this does not establish equivalence between the defenses.

\begin{table}[ht]\centering\small
\caption{Local-pipeline stability on the fixed 46-task test population. Entries are median BA [2.5th, 97.5th percentiles] over 100 training-customer resamples.}\label{tab:r21-local}
\begin{tabular}{llrrr}\toprule
Endpoint & Label & Calibration only & Calibration + attacker & Attacker only\\\midrule
'''
for n in NAMES:
    for lab in ['cancel','return']:
        vals=[st(n,n,reg,lab) for reg in ['calibration_only','calibration_and_attacker','attacker_only']]
        section+=f"{names[n]} & {lab} & "+' & '.join(f"{100*x['median']:.1f} {interval(x['percentiles95'])}" for x in vals)+r' \\'+'\n'
section+=r'''\bottomrule\end{tabular}\end{table}

\begin{table}[ht]\centering\small
\caption{Imported-minus-local max-BA contrasts after paired source-calibration resampling. Fixed-test cells are median [95\% sensitivity spread], in points. Joint train/test cells are exploratory percentile intervals with attacker retraining.}\label{tab:r21-deltas}
\begin{tabular}{llrrr}\toprule
Endpoint & Label & Calibration only & Calibration + attacker & Joint train/test\\\midrule
'''
for n in NAMES:
    for lab in ['cancel','return']:
        c=ct(n,'calibration_only',lab);j=ct(n,'calibration_and_attacker',lab)
        section+=f"{names[n]} & {lab} & {100*c['fixed_test']['median']:+.1f} {interval(c['fixed_test']['percentiles95'])} & {100*j['fixed_test']['median']:+.1f} {interval(j['fixed_test']['percentiles95'])} & {interval(j['joint_train_test']['percentiles95'])} \\\\\n"
section+=r'''\bottomrule\end{tabular}\end{table}
For joint sampling intervals, each of the 100 training replicates supplies 20 common 24-customer test bootstrap draws. All tasks from a selected customer stay together and both suite maxima are reselected. Single-class test draws are counted and omitted without replacement. The 2,000 nested draws are not 2,000 independent training fits. These exploratory empirical-population intervals include calibration and attacker-refit variability but are neither multiplicity-adjusted confirmatory intervals nor evidence for unobserved customer populations.
'''
invalid=[ct(n,'calibration_and_attacker',lab)['joint_train_test']['invalid'] for n in NAMES for lab in ['cancel','return']]
section+='Invalid joint test draws (MiniMax cancel/return, GLM cancel/return): '+', '.join(map(str,invalid))+'.\n'
section+=r'''
\begin{table}[ht]\centering\small
\caption{Resampled-calibration cost: median [95\% spread] of summed test cost divided by raw target totals.}\label{tab:r21-cost}
\begin{tabular}{llrr}\toprule
Target & Calibration source & Bytes$\times$ & Calls$\times$\\\midrule
'''
for x in data['costs']:
    section+=f"{names[x['target']]} & {names[x['source']]} & "+' & '.join(f"{x[k]['median']:.2f} {interval(x[k]['percentiles95'],1)}" for k in ['bytes_ratio','calls_ratio'])+r' \\'+'\n'
section+=r'''\bottomrule\end{tabular}\end{table}

\paragraph{What this establishes}
Local GLM return BA has median 52.5\% and 95\% calibration-sensitivity range 50.0--67.9\%: a 17.9-point width comparable to the original 17.3-point source contrast. Under paired source resampling, the imported-minus-local return contrast has median 0.0 and range $[-16.9,18.4]$ points; with attacker resampling its median is $+0.3$ and range $[-11.2,18.9]$. The joint train/test interval is $[-19.9,26.3]$. Hence the original directional attribution is not stable to local training variability. These ranges describe empirical sensitivity, not equivalence or a universal absence of source effects.
The deployment comparison must be indexed by target, source calibration, training sample and attacker fitting. An observed nonmonotone difference is a reason to measure that operating point; it is not sufficient evidence of a model-source transfer penalty. The additional experiment prices local recalibration variability and identifies which claims require a new customer population. The operational decision is to compare imported calibration with repeated local calibration under matched attacker fitting before carrying a numerical defense claim forward. All original attack, reward and cost measurements retain their stated scopes.
'''
write('sections/60-calibration-stability.tex',section)
print('R21_TABLES_AND_SUPPLEMENT_WRITTEN')
