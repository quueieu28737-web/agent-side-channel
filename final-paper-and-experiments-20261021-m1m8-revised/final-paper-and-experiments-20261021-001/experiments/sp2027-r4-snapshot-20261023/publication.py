"""Generate publication tables from the verified, fixed completion snapshot."""
from common import *
from collections import Counter

def pct(v):return f'{100*v:.1f}'
def interval(v,ci):return pct(v)+' ['+pct(ci[0])+', '+pct(ci[1])+']'
def emit(p,s):p.write_text(s+'\n',encoding='utf-8',newline='\n')

def main():
    draft='--draft' in sys.argv
    if draft:
        subset=read(HERE/'analysis_split.json')
        primary=[read(p) for p in (HERE/'runs').glob('*/*/episode.json') if int(p.parent.name.split('-')[1]) in subset['train']+subset['test']]
        assert len(primary)==660
        v={'model_calls':sum(e['model_calls'] for e in primary)}
    else:
        v=read(HERE/'validation.json');assert v['status']=='VERIFIED' and v['primary_analysis_episodes']==660
    data=read(HERE/'results.json');r={(x['view'],x['prompt'],x['condition'],x['target']):x for x in data['results']}
    u={(x['prompt'],x['condition']):x for x in data['utility']}
    out=EXP.parent/'manuscript/tables'
    lines=[r'\begin{table*}[t]\centering\footnotesize',
      r'\caption{E9: real-agent evaluation with training-only defense calibration. Primary snapshot: 41 held-out tasks, 22 customers, two prompts, three repeats (246 episodes). Network values are maximum balanced accuracy (\%) over the fixed attack suite with customer-cluster 95\% intervals. Program = online shadow cover plus constant framing.}\label{tab:r4-primary}',
      r'\begin{tabularx}{\textwidth}{@{}Yrrrrr@{}}\toprule',
      r'Condition & Cancellation BA [CI] & Return BA [CI] & Task reward (\%) & Bytes$\times$ & Calls$\times$\\\midrule']
    for label,arm,cond in [('Baseline','baseline','raw'),('Rules prompt','rules','raw'),('Program defense','baseline','shape_const'),('Rules + program','rules','shape_const')]:
        c=r['network',arm,cond,'cancel'];t=r['network',arm,cond,'return'];z=u[arm,cond]
        lines.append(f"{label} & {interval(c['suite_ba'],c['suite_ba_ci95'])} & {interval(t['suite_ba'],t['suite_ba_ci95'])} & {pct(z['native_reward']['mean'])} & {z['wire_ratio']:.2f} & {z['call_ratio']:.2f}"+r'\\')
    lines += [r'\bottomrule\end{tabularx}',r'\par\smallskip\raggedright Ratios use raw transport within the same prompt. Program conditions replay the same trajectory, so reward is unchanged by construction. The measurement is TLS~1.2 loopback replay of real model-generated tool calls. The 663-run completion snapshot includes 414 training runs and three further test runs outside the complete-task primary analysis; the planned cohort is 690. Full methods and ablations: Supplement S14.',r'\end{table*}']
    emit(out/'r4-primary.tex','\n'.join(lines))
    s=[r'\section{Real-Agent Evaluation with Training-Only Calibration (E9)}\label{sec:r4}',
    r'\subsection{Cohort and execution}',
    r'We froze a 115-task protocol with two prompt arms and three repetition identifiers (690 planned episodes). The fixed split assigns 69 tasks from 29 customers to training and 46 tasks from 24 disjoint customers to testing. All 414 training episodes completed before defense calibration was frozen and test inference began. At the publication cutoff, 2026-10-23 10:01:03 UTC, 663 episodes were complete: 414 training and 249 test episodes. Primary comparisons include every test task with all six prompt/repetition cells complete: 41 tasks from 22 customers, 246 episodes. Task 105 contributes three additional completed episodes, retained in the release and reported below. The remaining 27 runs were incomplete. This operational completion cutoff was adopted before the present attack analysis; it did not filter on reward, status or leakage. It is an interim sample, and completion order can affect its task composition.',
    r'GPT-6.1 Sol with low reasoning effort supplies the planner and a separate user simulator through Codex app-server. The planner receives the retail policy, public tool schemas, interaction history and actual sandbox observations, and emits one structured action at each step. Reference actions and reward targets are used only for scoring. Each model decision has a fresh ephemeral context without host tools or a host environment. The harness executes decisions in the pinned public retail simulator. Repetition identifiers are cache namespaces, not provider random seeds. The alias is mutable; temperature and an immutable weight snapshot are unavailable. This is a structured-action LLM agent evaluation, not a native function-calling API benchmark.',
    r'\subsection{Prompts and defense calibration}',
    r'The baseline prompt is the retail policy. The rules prompt adds one customer-details read after identification and before order access, an order read before each order write, and avoidance of unnecessary repeated reads. It preserves authorization and task requirements and prohibits unrelated operations for hiding intent. We compare both prompt arms under raw transport, padding only, online shape cover only, and joint shape cover with constant framing.',
    r'Only training trajectories from both prompts determine the shared per-tool count maxima, donor pools and size caps. Donor calls exclude the active customer. Request caps are the largest training request plus four bytes rounded to a 256-byte multiple; response caps use the training 95th percentile plus four bytes rounded to a 1024-byte multiple, including training donor responses. The frozen caps are 1,024 and 3,072 bytes. The online dispatcher can use only past real-call counts; it inserts a shadow call with probability 0.6 when a deficit exists and flushes remaining deficits at episode end. Overflow calls pass through; oversize messages expand to a 1024-byte bucket. Underfill and overflow are reported. Test data never recalibrate these parameters.',
    r'Shadow calls execute on a cloned initial database, with observations hidden from the planner. Real calls remain unchanged. Each realized trajectory is reused across the four program conditions, so reward equality across those conditions is structural. The experiment measures call and byte costs, not online delay or feedback-induced utility changes. A byte-transparent relay captures TLS~1.2 loopback replay of actual model-generated requests and sandbox responses; provider traffic and its timing are outside this measurement.',
    r'\subsection{Attackers and uncertainty}',
    r'The fixed suite contains a training-majority baseline, clean-trained gradient boosting, defense-trained logistic regression and gradient boosting, a dispatch count rule, and network size-decoding learners and rules. All fitted parameters, thresholds and decoder tables use training data only. Targets are cancellation and return intent from the reference task, while planner task reward is scored separately from final database equality and required response strings. Failed tasks and handoffs remain in the cohort. Points weight tasks equally; each primary task has three repeats per prompt. Intervals use 2,000 common customer-cluster bootstrap draws, retaining all of each customer\textquotesingle s tasks and repetitions together and recomputing the suite maximum in each draw. They condition on fitted attackers; training, feature-search and unknown-attacker uncertainty are outside their scope. Prompt contrasts pair tasks and repeat identifiers, not identical conversations or model randomness.']
    for view in ('dispatch','network'):
        s += [r'\begin{table}[ht]\centering\small',r'\caption{E9 '+view+r' view: maximum BA (\%) with 95\% interval and maximum AUROC across the fixed suite.}',r'\begin{tabular}{@{}llrrrr@{}}\toprule',r'Prompt & Condition & Cancel BA [CI] & AUC & Return BA [CI] & AUC\\\midrule']
        for arm in PROMPTS:
            for cond in ('raw','padding_only','shape_only','shape_const'):
                c=r[view,arm,cond,'cancel'];t=r[view,arm,cond,'return']
                s.append(f"{arm} & {cond.replace('_',' ')} & {interval(c['suite_ba'],c['suite_ba_ci95'])} & {c['suite_auroc']:.3f} & {interval(t['suite_ba'],t['suite_ba_ci95'])} & {t['suite_auroc']:.3f}"+r'\\')
        s += [r'\bottomrule\end{tabular}\end{table}']
    s += [r'\clearpage',r'\subsection{Utility, overhead and completion accounting}',r'\begin{table}[ht]\centering\small',r'\caption{Held-out utility and overhead. Reward and overflow rates are percentages. Ratios use the same prompt\textquotesingle s raw transport.}',r'\begin{tabular}{@{}llrrrrrr@{}}\toprule',r'Prompt & Condition & Reward [CI] & Calls$\times$ & Bytes$\times$ & Count overflow & Cap overflow & Underfill\\\midrule']
    for arm in PROMPTS:
        for cond in ('raw','padding_only','shape_only','shape_const'):
            z=u[arm,cond]
            s.append(f"{arm} & {cond.replace('_',' ')} & {interval(z['native_reward']['mean'],z['native_reward']['ci95'])} & {z['call_ratio']:.2f} & {z['wire_ratio']:.2f} & {pct(z['template_overflow_rate'])} & {pct(z['framing_overflow_session_rate'])} & {pct(z['template_underfill_rate'])}"+r'\\')
    s += [r'\bottomrule\end{tabular}\end{table}']
    c=r['network','baseline','raw','cancel'];t=r['network','baseline','raw','return'];delta=data['reward_rules_minus_baseline']
    s += [f"Cancellation has {c['positive_test_tasks']} positive tasks from {c['positive_customer_clusters']} customers; return has {t['positive_test_tasks']} positive tasks from {t['positive_customer_clusters']} customers. Single-class draws discarded from 2,000 bootstrap replicates: {c['invalid_single_class_bootstrap_draws']} for cancellation and {t['invalid_single_class_bootstrap_draws']} for return. The paired rules-minus-baseline reward difference is {interval(delta['mean'],delta['ci95'])} percentage points.",
       r'\begin{table}[ht]\centering\small',r'\caption{Mechanical workflow compliance (\% with customer-cluster interval). These two checks do not audit all authorization or natural-language requirements.}',r'\begin{tabular}{@{}lrrr@{}}\toprule',r'Prompt & One successful customer read first & Order read before write & Both\\\midrule']
    for arm in PROMPTS:
        z=u[arm,'raw']['rule_compliance'];s.append(arm+' & '+' & '.join(interval(z[k]['mean'],z[k]['ci95']) for k in ('user_details_once_before_order','read_before_order_write','all_measured_rules'))+r'\\')
    s += [r'\bottomrule\end{tabular}\end{table}']
    eps=[read(p) for p in (HERE/'runs').glob('*/*/episode.json')];orig=read(HERE/'split.json');additional=[]
    for arm in PROMPTS:
        test=[e for e in eps if e['prompt']==arm and e['task'] in orig['test']]
        extra=[e for e in test if e['task'] not in read(HERE/'analysis_split.json')['test']]
        additional.append({'prompt':arm,'all_completed_test_episodes':len(test),'all_completed_test_successes':sum(e['native_reward'] for e in test),'all_completed_test_status':dict(Counter(e['status'] for e in test)), 'additional':[{k:e[k] for k in ('task','repeat','native_reward','status')} for e in extra]})
    write(HERE/'completion_summary.json',additional)
    s.append('All completed test episodes, including task 105: '+ '; '.join(f"{a['prompt']} {a['all_completed_test_successes']}/{a['all_completed_test_episodes']} native successes" for a in additional)+'. These unbalanced completion totals are descriptive and do not replace the complete-task prompt comparison. The release preserves each additional episode, its status and model records.')
    s += [r'\subsection{Interpretation and reproducibility}',
       r'E9 supplies real model-generated trajectories and a fully training-calibrated defense evaluation, extending the reference-program tests. Its scope is one public benchmark and one provider model alias, with the same model family supplying the user simulator. All 115 tasks had been available during earlier paper development; the customer holdout is an internal evaluation, not an external benchmark. The incomplete late-task cohort and small positive-customer counts limit extrapolation. An independent human replication remains future work.',
       'The primary analysis contains '+str(v['model_calls'])+' model decisions and 2,640 TLS sessions. Records for all 663 completed episodes are retained. The release verifies inference fingerprints, original runtime and pretest analysis hashes, training-only recalibration, sandbox state and required-output scoring, cover reconstruction, TLS accounting, saved predictions, sklearn point metrics and clustered intervals. This is executable verification, not independent external replication.',
       r'\path{experiments/sp2027-r4-snapshot-20261023/} contains the cutoff amendment, complete episode membership, original pretest sources, derived analysis, calibration, compressed model records, predictions and validation receipt. Earlier Luna pilots and interrupted attempts are separately archived and excluded. Operational logs and recovery details are retained in the artifact README rather than used as scientific outcomes.']
    emit(out/'r4-supp.tex','\n\n'.join(s).replace(r'\textquotesingle s',"'s"))
    print('DRAFT_TABLES_FOR_LAYOUT_ONLY' if draft else 'PUBLICATION_TABLES_GENERATED')

if __name__=='__main__':main()
