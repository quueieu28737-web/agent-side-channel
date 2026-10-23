"""Deterministic manuscript tables from the immutable, verified full cohort.

Run without arguments to write the two table sources; --check compares bytes.
No model calls, fitting, or changes to experimental data are performed.
"""
from pathlib import Path
import json, sys
P=Path(__file__).resolve().parents[2]
F=P/'experiments/sp2027-r4-full-20261023'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pct(x):return f'{100*x:.1f}'
def ci(x,limits):return pct(x)+' ['+pct(limits[0])+', '+pct(limits[1])+']'
def table(spec,heading,rows,caption):
    return '\n'.join([r'\begin{table}[ht]\centering\small',r'\caption{'+caption+'}',r'\begin{tabular}{@{}'+spec+r'@{}}\toprule',heading+r'\\\midrule',*[x+r'\\' for x in rows],r'\bottomrule\end{tabular}\end{table}'])
def sources():
    v=read(F/'validation.json');assert v['status']=='VERIFIED' and v['episodes']==690
    d=read(F/'results.json')
    r={(x['view'],x['prompt'],x['condition'],x['target']):x for x in d['results']}
    u={(x['prompt'],x['condition']):x for x in d['utility']}
    labels={'raw':'Raw','padding_only':'Padding only','shape_only':'Shape only','shape_const':'Joint'}
    rows=[]
    for label,arm,cond in [('Baseline','baseline','raw'),('Rules prompt','rules','raw'),('Padding only','baseline','padding_only'),('Shape only','baseline','shape_only'),('Joint program','baseline','shape_const'),('Rules + joint','rules','shape_const')]:
        c=r['network',arm,cond,'cancel'];t=r['network',arm,cond,'return'];z=u[arm,cond]
        rows.append(f"{label} & {ci(c['suite_ba'],c['suite_ba_ci95'])} & {ci(t['suite_ba'],t['suite_ba_ci95'])} & {pct(z['native_reward']['mean'])} & {z['wire_ratio']:.2f} & {z['call_ratio']:.2f}")
    primary='\n'.join([r'\begin{table*}[t]\centering\small',r'\caption{E9: complete real-agent evaluation with training-only defense calibration. Testing covers 46 tasks from 24 held-out customers, two prompts and three repeats (276 episodes). Network BA is the maximum over the fixed attack suite, with customer-cluster 95\% intervals.}\label{tab:r4-primary}',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'Condition & Cancel BA [95\% CI] & Return BA [95\% CI] & Reward (\%) & Bytes$\times$ & Calls$\times$\\\midrule',*[x+r'\\' for x in rows],r'\bottomrule\end{tabular}',r'\par\smallskip\raggedright Joint = online shadow cover plus constant framing. Padding and shape ablations use baseline trajectories. Ratios use raw transport within the same prompt. Program conditions reuse each trajectory, preserving reward by construction. Network measurements are TLS~1.2 loopback replay of actual model-generated calls; 414 training runs preceded defense freezing and test collection. Full methods and ablations: Supplement S14.',r'\end{table*}'])
    lines=[r'''\section{Complete Real-Agent Evaluation with Training-Only Calibration (E9)}\label{sec:r4}
\subsection{Cohort and execution}
All 690 episodes in the frozen protocol are complete: 115 tasks, two prompt arms and three repetition identifiers. The fixed split assigns 69 tasks from 29 customers to training (414 episodes) and 46 tasks from 24 disjoint customers to testing (276 episodes). Every test task has all six prompt/repetition cells, and all failures and handoffs remain in the analysis. Training finished before defense calibration was frozen and test inference began. This section updates the earlier 663-episode publication snapshot to the full cohort; the immutable snapshot and the previous manuscript remain available in the archived release. No model configuration, prompt, split or defense parameter changed for this completion.

GPT-6.1 Sol with low reasoning effort supplies the planner and a separate user simulator through Codex app-server. The planner receives the retail policy, public tool schemas, interaction history and actual sandbox observations, and emits one structured action at each step. Reference actions and reward targets are used only for scoring. Each decision has a fresh ephemeral context without host tools or a host environment. The harness executes decisions in the pinned public retail simulator, with a 30-step limit. Repetition identifiers are cache namespaces; provider random seeds, temperature and an immutable weight snapshot are unavailable.

\subsection{Prompts and defense calibration}
The baseline prompt is the retail policy. The rules prompt adds one customer-details read after identification and before order access, an order read before each order write, and avoidance of unnecessary repeated reads. It preserves authorization and task requirements and prohibits unrelated operations for hiding intent. Both arms are evaluated under raw transport, padding only, online shape cover only, and joint shape cover with constant framing.

Only training trajectories from both prompts determine shared per-tool count maxima, donor pools and size caps. Donor calls exclude the active customer. Request caps are the largest training request plus four bytes rounded to a 256-byte multiple; response caps use the training 95th percentile plus four bytes rounded to a 1024-byte multiple, including training donor responses. Frozen caps are 1,024 and 3,072 bytes. The online dispatcher uses only past real-call counts, inserts a shadow call with probability 0.6 when a deficit exists and flushes remaining deficits at episode end. Overflow calls pass through; oversize messages expand to a 1024-byte bucket. Test data never recalibrate these parameters.

Shadow calls execute on a cloned initial database, with observations hidden from the planner. Real calls remain unchanged. Each trajectory is reused across program conditions, preserving reward by construction. The experiment measures call and byte costs; online delay and feedback-induced behavior require an interactive evaluation. A byte-transparent relay captures TLS~1.2 loopback replay of actual model-generated requests and sandbox responses.

\subsection{Attackers and uncertainty}
The frozen suite includes a training-majority baseline, clean-trained gradient boosting, defense-trained logistic regression and gradient boosting, a dispatch count rule, and network size-decoding learners and rules. All fitted parameters, thresholds and decoder tables use training data only. Targets are cancellation and return intent from the reference task; native task reward is scored separately using final database equality and required response strings. Points weight tasks equally. Intervals use 2,000 common customer-cluster bootstrap draws, retaining each customer's tasks and repetitions together and recomputing the suite maximum in each draw. Intervals condition on fitted attackers. Prompt contrasts pair task/repetition identifiers, without assuming identical conversations or shared model randomness.
''']
    for view in ('dispatch','network'):
        rows=[]
        for arm in ('baseline','rules'):
            for cond in labels:
                c=r[view,arm,cond,'cancel'];t=r[view,arm,cond,'return']
                rows.append(f"{arm} & {labels[cond]} & {ci(c['suite_ba'],c['suite_ba_ci95'])} & {c['suite_auroc']:.3f} & {ci(t['suite_ba'],t['suite_ba_ci95'])} & {t['suite_auroc']:.3f}")
        lines.append(table('llrrrr',r'Prompt & Condition & Cancel BA [CI] & AUC & Return BA [CI] & AUC',rows,'E9 '+view+r' view: maximum BA (\%) with 95\% interval and maximum AUROC across the fixed suite, on 138 test episodes per prompt. BA and AUROC are separate suite maxima.'))
    lines.append(r'\subsection{Utility, overhead and prompt contrasts}')
    rows=[]
    for arm in ('baseline','rules'):
        for cond in labels:
            z=u[arm,cond]
            rows.append(f"{arm} & {labels[cond]} & {ci(z['native_reward']['mean'],z['native_reward']['ci95'])} & {z['call_ratio']:.2f} & {z['wire_ratio']:.2f} & {pct(z['template_overflow_rate'])} & {pct(z['framing_overflow_session_rate'])} & {pct(z['template_underfill_rate'])}")
    lines.append(table('llrrrrrr',r'Prompt & Condition & Reward [CI] & Calls$\times$ & Bytes$\times$ & Count overflow & Cap overflow & Underfill',rows,r'Held-out utility and overhead. Reward and session overflow rates are percentages; ratios use raw transport within the same prompt.'))
    pos=r['network','baseline','raw','cancel'];ret=r['network','baseline','raw','return']
    lines.append(f"Cancellation has {pos['positive_test_tasks']} positive tasks from {pos['positive_customer_clusters']} customers; return has {ret['positive_test_tasks']} positive tasks from {ret['positive_customer_clusters']} customers. Single-class draws excluded from 2,000 replicates: {pos['invalid_single_class_bootstrap_draws']} for cancellation and {ret['invalid_single_class_bootstrap_draws']} for return.")
    lines.append(r'Baseline native reward is 110/138 (79.7\%); rules reward is 105/138 (76.1\%). All 24 baseline and 23 rules handoffs remain in the denominator. Joint-program cover-call error rates are 5.3\% and 5.0\%, respectively; all shape conditions have zero underfill. Overflow rates expose the resource demands of retaining real calls under the frozen training template.')
    rows=[]
    for arm in ('baseline','rules'):
        q=u[arm,'raw']['rule_compliance']
        rows.append(arm+' & '+' & '.join(ci(q[k]['mean'],q[k]['ci95']) for k in ('user_details_once_before_order','read_before_order_write','all_measured_rules')))
    lines.append(table('lrrr','Prompt & One successful customer read first & Order read before write & Both',rows,r'Measured workflow compliance (\% with customer-cluster interval). These checks cover the two specified rules.'))
    q=d['reward_rules_minus_baseline'];rows=[f"Task reward & {ci(q['mean'],q['ci95'])}"]
    for cond in ('raw','shape_const'):
        for target in ('cancel','return'):
            x=next(x for x in d['prompt_differences'] if x['view']=='network' and x['condition']==cond and x['target']==target)
            rows.append(f"{labels[cond]} network, {target} BA & {ci(x['difference'],x['ci95'])}")
    lines.append(table('lr',r'Rules minus baseline & Difference [95\% CI], pp',rows,r'Paired prompt contrasts using common customer-bootstrap draws.'))
    lines.append(r'''\subsection{Interpretation and reproducibility}
The completed cohort shows strong raw-trace intent inference and a large reduction under joint transport intervention. Rules improve measured workflow compliance while leaving network BA above 93\%. Baseline joint shaping reaches 50\% BA for both targets, reducing the raw scores by 47.2 and 44.0 points. The finite-suite criterion requires the BA interval upper bound below 60\% and point AUROC below 0.65. Baseline shape-only return meets it for that target; no condition meets it for both targets. Baseline joint upper bounds are 60.6\%/65.5\%. Rules-plus-joint return BA is 60.6\%; its paired contrast includes zero, as does the reward contrast.

The evidence covers one public retail environment and one mutable model alias, which also supplies user simulation. All 115 tasks were available during prior project development. The formal customer holdout therefore provides internal evaluation; external independent replication, broader model/environment transfer, provider-traffic measurement and interactive feedback effects remain follow-up questions.

The full cohort contains 11,586 model decisions, 2,760 TLS sessions and 176 attack-prediction sets. The frozen verifier passed after training-only recalibration, sandbox state replay, cover reconstruction, TLS accounting, metric/interval recomputation and request-provenance checks. Additional checks bind all agent actions and dialogue to actual model outputs and re-score required response strings. Offline attacker refitting reproduces the saved results and predictions exactly.

\path{experiments/sp2027-r4-full-20261023/} supplies full results, predictions and captures, plus the 27 new episodes and model records needed to extend the immutable 663-run snapshot. The three separately reported snapshot test episodes join the 27 new ones to expand the primary test from 246 to 276. \texttt{reproduce.py --reanalyze} reconstructs the full cohort from the base archives and delta, reruns analysis and executes the original frozen verifier without invoking a model. \texttt{verify\_extension.py} checks decision alignment and provenance. The earlier snapshot, historical R2/R3 studies and pilot archives retain their original denominators and bytes.
''')
    return {'tables/r4-primary.tex':primary+'\n','tables/r4-supp.tex':'\n\n'.join(lines).rstrip()+'\n'}
def main():
    for name,content in sources().items():
        p=P/'manuscript'/name
        if '--check' in sys.argv:assert p.read_bytes()==content.encode('utf-8'),name
        else:p.write_text(content,encoding='utf-8',newline='\n')
    print('FULL_COHORT_MANUSCRIPT_TABLES_MATCH' if '--check' in sys.argv else 'FULL_COHORT_MANUSCRIPT_TABLES_WRITTEN')
if __name__=='__main__':main()
