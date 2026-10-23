"""Generate a standalone, source-bound supplement from the full verified cohort."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'sp2027-r4-snapshot-20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def emit(p,s):p.write_text(s+'\n',encoding='utf-8',newline='\n')
def pct(x):return f'{100*x:.1f}'
def ci(x,limits):return pct(x)+' ['+pct(limits[0])+', '+pct(limits[1])+']'
def table(spec,heading,rows,caption):
    return '\n'.join([r'\begin{center}\small',r'\begin{tabular}{@{}'+spec+r'@{}}\toprule',heading+r'\\\midrule',*[x+r'\\' for x in rows],r'\bottomrule\end{tabular}',r'\end{center}',r'\noindent\textit{'+caption+'}',r'\par\medskip'])

def main():
    v=read(HERE/'validation.json');assert v['status']=='VERIFIED' and v['episodes']==690
    d=read(HERE/'results.json');b=read(BASE/'results.json')
    r={(x['view'],x['prompt'],x['condition'],x['target']):x for x in d['results']}
    br={(x['view'],x['prompt'],x['condition'],x['target']):x for x in b['results']}
    u={(x['prompt'],x['condition']):x for x in d['utility']}
    bu={(x['prompt'],x['condition']):x for x in b['utility']}
    labels={'raw':'Raw','padding_only':'Padding','shape_only':'Shape','shape_const':'Joint'}
    arms=('baseline','rules');conditions=tuple(labels)
    lines=[r'''\documentclass[10pt,letterpaper]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,booktabs,tabularx,array,amsmath,xcolor}
\usepackage[hyphens]{url}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small Evidence Boundaries of Agent Side-Channel Defenses}\fancyhead[R]{\small Full cohort}
\fancyfoot[C]{\thepage}\setlength{\headheight}{14pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{6pt}
\newcommand{\note}[1]{\par\noindent\colorbox{blue!5}{\parbox{\dimexpr\linewidth-2\fboxsep\relax}{#1}}\par}
\begin{document}
\begin{center}
{\LARGE\bfseries Full-Cohort Supplement: Real-Agent Evaluation}\par\medskip
{\large E9 completion extension, 23 October 2026}\par
\end{center}
\section*{1. Completed evidence and principal findings}
The complete, frozen 690-episode experiment confirms a strong separation between workflow compliance and resistance to network inference. Real model-generated tool trajectories expose cancellation and return intent under raw transport. A defense calibrated only on training trajectories sharply reduces measured attack performance, while the rules prompt improves measured compliance without providing comparable protection.

This supplement adds the completed queue to the previously published 663-episode snapshot. It uses the same GPT-6.1 Sol / low configuration, task/customer split, prompt arms, repetition identifiers, calibration and pre-test analysis. It is an extension of the original experiment. The earlier manuscript, Supplement S14 and snapshot remain historical records with their original sample denominators.
''']
    lines.append(table('lrr','Cohort & Tasks / customers & Episodes',[
        'Training & 69 / 29 & 414','Held-out test & 46 / 24 & 276','Total & 115 / 53 & 690'],
        'Every task has two prompt arms and three repetitions. Training and test customers are disjoint. All training runs preceded defense freezing and test inference.'))
    rows=[]
    for label,arm,cond in [('Baseline','baseline','raw'),('Rules prompt','rules','raw'),('Joint program','baseline','shape_const'),('Rules + joint','rules','shape_const')]:
        c=r['network',arm,cond,'cancel'];t=r['network',arm,cond,'return'];z=u[arm,cond]
        rows.append(f"{label} & {ci(c['suite_ba'],c['suite_ba_ci95'])} & {ci(t['suite_ba'],t['suite_ba_ci95'])} & {pct(z['native_reward']['mean'])} & {z['wire_ratio']:.2f} & {z['call_ratio']:.2f}")
    lines.append(table('lrrrrr',r'Condition & Cancel BA [95\% CI] & Return BA [95\% CI] & Reward & Bytes$\times$ & Calls$\times$',rows,
        r'Table F1. Held-out network results; BA and reward are percentages. BA is the maximum over the fixed attacker suite. Ratios use raw transport within the same prompt.'))
    lines += [r'''\note{\textbf{Measured advantage.} Joint shape cover and constant framing reduce baseline network BA by 47.2 percentage points for cancellation and 44.0 points for return, reaching 50.0\% for both. The corresponding cost is 15.39$\times$ bytes and 3.83$\times$ calls.}

Rules raise measured workflow compliance from 86.2\% to 97.1\%, yet raw network BA remains 97.2\% for cancellation and 93.5\% for return. Thus, a rule-following agent can still produce a highly recognizable tool trace. The evaluation makes this gap measurable and distinguishes prompt behavior from transport-level intervention.

The network evidence comes from TLS~1.2 loopback replay of real LLM trajectories. Program conditions reuse each realized trajectory, so reward equality across those conditions follows by construction. Confidence intervals remain important: no tested condition meets the predeclared finite-suite criterion for both intent targets jointly.
\clearpage
\section*{2. Full ablation results and uncertainty}
''']
    for view in ('network','dispatch'):
        rows=[]
        for arm in arms:
            for cond in conditions:
                c=r[view,arm,cond,'cancel'];t=r[view,arm,cond,'return']
                rows.append(f"{arm} & {labels[cond]} & {ci(c['suite_ba'],c['suite_ba_ci95'])} & {c['suite_auroc']:.3f} & {ci(t['suite_ba'],t['suite_ba_ci95'])} & {t['suite_auroc']:.3f}")
        lines.append(table('llrrrr',r'Prompt & Program & Cancel BA [CI] & AUC & Return BA [CI] & AUC',rows,
            'Table F'+('2' if view=='network' else '3')+'. '+view.capitalize()+r' view on 138 held-out episodes per prompt. BA is in percent. BA and AUROC are separate maxima over the evaluated suite.'))
    pos=r['network','baseline','raw','cancel'];ret=r['network','baseline','raw','return']
    lines += [r'\textbf{Programs.} Raw retains the realized call stream. Padding applies trained constant framing. Shape adds online shadow cover using the trained per-tool count template. Joint combines shape cover and framing. Cover observations are hidden from the planner and real calls are retained.',
        r'\textbf{Attackers.} The frozen suite includes a training-majority baseline, clean-trained gradient boosting, defense-trained logistic regression and gradient boosting, dispatch count rules, and network size-decoding learners/rules. All thresholds, models and decoders use training data only.',
        r'\textbf{Intervals.} We use 2,000 common customer-cluster bootstrap draws, retaining all tasks and repetitions belonging to each sampled customer. Each draw recomputes the suite maximum; single-class draws are excluded. Intervals condition on fitted attackers and do not include training-set or unknown-attacker uncertainty.',
        f"Cancellation has {pos['positive_test_tasks']} positive tasks from {pos['positive_customer_clusters']} customer clusters; return has {ret['positive_test_tasks']} positive tasks from {ret['positive_customer_clusters']} clusters. The respective invalid single-class draw counts are {pos['invalid_single_class_bootstrap_draws']} and {ret['invalid_single_class_bootstrap_draws']}.",
        r'The finite-suite criterion requires the BA interval upper bound below 60\% and point AUROC below 0.65. Baseline shape-only return meets this criterion; cancellation does not, so this is a target-specific result. Baseline joint has 50\% point BA for both targets but upper bounds of 60.6\% and 65.5\%.',
        r'\clearpage\section*{3. Utility, costs and prompt contrasts}']
    rows=[]
    for arm in arms:
        for cond in conditions:
            z=u[arm,cond]
            rows.append(f"{arm} & {labels[cond]} & {ci(z['native_reward']['mean'],z['native_reward']['ci95'])} & {z['call_ratio']:.2f} & {z['wire_ratio']:.2f} & {pct(z['template_overflow_rate'])} & {pct(z['framing_overflow_session_rate'])}")
    lines.append(table('llrrrrr',r'Prompt & Program & Reward [CI] & Calls$\times$ & Bytes$\times$ & Count over. & Cap over.',rows,
        r'Table F4. Reward and session overflow rates are percentages; overhead ratios are ratios of mean costs. All conditions retain unsuccessful tasks and handoffs.'))
    lines += [r'Native reward is 110/138 (79.7\%) for baseline and 105/138 (76.1\%) for rules. Task outcomes include 24 baseline and 23 rules handoffs; these remain in the denominator. Measured rules require one customer-details read before order access and an order read before order writes. Read-before-write compliance is 100\% in both arms.',
        r'Count overflow occurs when real calls exceed the trained template; excess calls pass through. Cap overflow marks messages that exceed trained framing caps and use a larger 1,024-byte bucket. Shape conditions have zero underfill; their cover-call error rates are 5.3\% for baseline and 5.0\% for rules. Shadow calls execute on a cloned initial database without feeding observations back to the agent.',
        r'\subsection*{Paired prompt differences}']
    delta=d['reward_rules_minus_baseline']
    rows=[f"Task reward & {ci(delta['mean'],delta['ci95'])}"]
    for cond in ('raw','shape_const'):
        for target in ('cancel','return'):
            x=next(x for x in d['prompt_differences'] if x['view']=='network' and x['condition']==cond and x['target']==target)
            rows.append(f"{labels[cond]} network, {target} BA & {ci(x['difference'],x['ci95'])}")
    lines.append(table('lr',r'Rules minus baseline & Difference [95\% CI], pp',rows,
        r'Table F5. Contrasts pair task/repetition identifiers and customer-bootstrap draws. They do not imply shared model randomness or identical conversations.'))
    lines += [r'The rules-plus-joint return BA is 60.6\%, compared with 50.0\% for baseline joint. The paired difference interval crosses zero; the experiment does not establish that the rules prompt worsens joint-defense leakage. Likewise, the task-reward contrast does not establish a systematic loss in success.',
        r'\textbf{Training-only calibration.} Both training prompt arms supply the shared count maxima and donor pool. Request caps use the maximum training request plus four bytes, rounded to 256 bytes; response caps use the training 95th percentile plus four bytes, rounded to 1,024 bytes, including donor responses. Frozen caps are 1,024/3,072 bytes. Cover emission uses probability 0.6 for deficits based on past calls, with remaining deficits flushed at the end. Donors exclude the active customer. No test trajectory changes calibration.',
        r'\textbf{Utility scope.} These measurements establish call and byte costs while preserving the original task trace. Online latency, feedback-induced behavior changes and deployed-system utility require a separate interactive evaluation.',
        r'\clearpage\section*{4. Continuity with the published snapshot}']
    comparison=[]
    for label,view,arm,cond,target in [('Baseline raw cancel BA','network','baseline','raw','cancel'),('Baseline raw return BA','network','baseline','raw','return'),('Baseline joint cancel BA','network','baseline','shape_const','cancel'),('Baseline joint return BA','network','baseline','shape_const','return'),('Rules joint return BA','network','rules','shape_const','return')]:
        comparison.append({'metric':label,'snapshot':br[view,arm,cond,target]['suite_ba'],'full':r[view,arm,cond,target]['suite_ba']})
    for arm in arms:
        comparison.append({'metric':arm.capitalize()+' task reward','snapshot':bu[arm,'raw']['native_reward']['mean'],'full':u[arm,'raw']['native_reward']['mean']})
    lines.append(table('lrr',r'Metric (\%) & Snapshot primary & Full cohort',[f"{x['metric']} & {pct(x['snapshot'])} & {pct(x['full'])}" for x in comparison],
        'Table F6. Snapshot primary testing: 41 tasks, 22 customers, 246 episodes. Full testing: 46 tasks, 24 customers, 276 episodes. These are overlapping cohorts, not independent replications.'))
    lines += [r'''The original snapshot contains 663 completed episodes: 414 training, 246 primary test and three separately reported task-105 episodes. Completion adds 27 new episodes; together with those three existing episodes, the full primary test grows by 30. Tasks 105, 106, 107, 108 and 114 are now represented by all six prompt/repetition cells. The 663 prior episode records remain byte-identical.

The full cohort removes the interim completion filter and retains the central pattern: strong raw-trace inference, substantial reduction under joint transport intervention, and limited protection from workflow rules alone. Reward changes reflect the additional tasks and are reported with the new denominator. The snapshot values are not silently replaced.

\subsection*{Execution and reproducibility}
GPT-6.1 Sol / low supplies a structured-action planner and a separate user-simulator context. The planner sees public retail policy, schemas, dialogue and actual sandbox observations. Reference actions and reward targets are used only for scoring. Each decision uses an ephemeral context without host tools. Repetition identifiers are cache namespaces, not provider seeds; the protocol caps agent steps at 30. All 115 tasks were available in prior project development, although formal evaluation uses a customer-disjoint split.

The complete cohort contains 11,586 model decisions, 2,760 TLS sessions and 176 prediction sets across 32 target/view/prompt/program cells. The original frozen verifier passed after calibration refitting, state replay, transport accounting, metric/interval recomputation and request-provenance checks. The extension verifier additionally binds actions and dialogue to actual model outputs, checks all required response strings, and verifies unchanged base bytes and new-record membership.

The incremental release supplies only the 27 new episodes and their model records, plus full predictions, results and capture records. It references the three existing model-record archives by hash. \texttt{reproduce.py --reanalyze} reconstructs the cohort in a temporary directory, reruns the fixed attacker analysis, checks exact equality of saved results and predictions, and executes the original frozen verifier. \texttt{verify\_extension.py} checks decision alignment and incremental provenance. Neither command invokes a model.

\subsection*{What the evidence supports}
This experiment contributes a completed, reproducible comparison linking actual agent behavior, training-only defense calibration and observable leakage. It identifies both a large measured reduction and its operational cost, and demonstrates why prompt compliance alone is insufficient to infer transport protection. It covers one public retail environment and one mutable model alias; the same alias supplies the user simulator. Provider-traffic measurement, external independent replication, broader model/environment transfer and online feedback effects remain outside the experiment. These limits delimit the demonstrated result rather than changing its measured effect.

\end{document}''']
    emit(HERE/'manuscript/main.tex','\n\n'.join(lines))
    emit(HERE/'snapshot_comparison.json',json.dumps({'snapshot_primary_test_episodes':246,'full_test_episodes':276,'comparisons':comparison},indent=2))
    print('FULL_COHORT_TABLES_AND_TEXT_GENERATED')

if __name__=='__main__':main()
