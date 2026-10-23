"""Generate manuscript tables only after the complete formal grid is verified."""
from common import *

def pct(x):return f'{100*x:.1f}'
def ci(x,interval):return pct(x)+r' ['+pct(interval[0])+', '+pct(interval[1])+']'
def texwrite(path,text):path.write_text(text+'\n',encoding='utf-8',newline='\n')

def main():
    data=read(HERE/'results.json');valid=read(HERE/'validation.json')
    assert valid['status']=='VERIFIED' and valid['episodes']==690
    assert valid['protocol_sha256']==sha(HERE/'protocol.json')
    rows={(r['view'],r['prompt'],r['condition'],r['target']):r for r in data['results']}
    util={(r['prompt'],r['condition']):r for r in data['utility']}
    tabledir=EXP.parent/'manuscript/tables'
    primary=[('Baseline','baseline','raw'),('Rules','rules','raw'),('Program','baseline','shape_const'),('Both','rules','shape_const')]
    t=[r'\begin{table}[t]\centering\footnotesize',
       r'\caption{E9: real Sol trajectories, training-only calibration. Maximum network BA (\%) and customer-cluster 95\% intervals; task reward (\%). Byte/call ratios are relative to raw transport within the same prompt. Program = online shadow shape cover plus constant framing.}\label{tab:r4-primary}',
       r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'Condition & Cancel BA [CI] & Return BA [CI] & Reward & Bytes & Calls\\\midrule']
    for label,arm,cond in primary:
        a=rows['network',arm,cond,'cancel'];b=rows['network',arm,cond,'return'];u=util[arm,cond]
        t.append(f"{label} & {ci(a['suite_ba'],a['suite_ba_ci95'])} & {ci(b['suite_ba'],b['suite_ba_ci95'])} & {pct(u['native_reward']['mean'])} & {u['wire_ratio']:.1f}$\\times$ & {u['call_ratio']:.1f}$\\times$"+r'\\')
    t += [r'\bottomrule\end{tabular}',r'\end{table}']
    texwrite(tabledir/'r4-primary.tex','\n'.join(t))
    supp=[r'\section{Real Sol Agent and Training-Only Calibration (E9)}\label{sec:r4}',
        r'E9 is a new internal evaluation on the previously used public retail benchmark. The local configuration was frozen before formal collection; it is not an independently registered study. GPT-6.1 Sol supplies both the planner and a separate user-simulator context through Codex app-server, with low reasoning effort. Each inference uses a fresh ephemeral context with no host environment. The model returns one structured action; the harness executes it on the pinned sandbox and supplies the actual result. The agent receives policy, public tool schemas and interaction history, never reference programs or reward targets. The provider model alias, CLI version, prompts, requests, events, structured outputs, usage and cache fingerprints are retained. Temperature, provider random seed and immutable model weights are unavailable.',
        r'The split contains 69 training tasks from 29 customers and 46 test tasks from 24 disjoint customers. Each prompt runs three independent cache namespaces per task: 690 formal episodes, of which 276 are held out. Repetition identifiers are not provider seeds. Four early Luna pilot episodes, the interrupted CLI batch, and four Luna RPC training episodes plus partial calls are excluded and separately disclosed. Persistent HTTP 429 throttling led to a user-authorized switch before any test collection; all 690 formal Sol episodes start fresh. A single connectivity probe selected the replacement without benchmark inputs. Previous developer exposure to all 115 public tasks remains a limitation.',
        r'The rules prompt requests one successful customer-details read before order access and reads before order writes, while retaining the retail policy and avoiding unrelated calls. This changes planner behavior; it cannot enforce record lengths. Both prompt arms have raw, padding-only, online shape-only and joint shape/constant-framing conditions. Only training trajectories from both arms define the shared per-tool count maxima and donor pools. Request caps round the largest training request plus four bytes to 256-byte multiples; response caps round the training 95th percentile plus four bytes to 1024-byte multiples. Training donor responses are included. Parameters are frozen before test inference. Excess counts pass through, oversized messages expand to the next 1024-byte bucket, and unavailable donors produce recorded underfill. No test-driven recalibration is allowed.',
        r'Shadow calls execute on a cloned initial database and are hidden from the planner. Real calls are never removed or altered. Each prompt trajectory is reused across program conditions; reward equality across these conditions is inherited by construction. It does not measure utility under online delays or changed feedback. The network view is measured TLS~1.2 loopback replay of these real model trajectories, not provider traffic or deployment timing.',
        r'The fixed suite includes a training-majority baseline, clean-trained gradient boosting, defense-trained logistic regression and gradient boosting, a dispatch count rule, and network size-decoding learners/rules. Training-only data fit scalers, models, rule thresholds and decoder tables. Cancellation and return label the reference task intent; actual planner success is measured separately. Semantic failures, maximum-step exits and invalid-action outcomes remain in the grid. All displayed intervals use 2,000 common customer-cluster bootstrap draws with every customer\textquotesingle s tasks and repeats together. Point estimates weight tasks equally. Suite maxima are recomputed within each draw. Intervals condition on fitted attackers and do not account for retraining, feature search or unknown attacks. Single-class draws are discarded and counted. Prompt differences pair tasks, not identical user conversations or model random draws.']
    for view in ('dispatch','network'):
        supp += [r'\begin{table}[ht]\centering\small',r'\caption{E9 '+view+r' view. Maximum BA (\%) with 95\% interval and maximum AUROC across the fixed suite.}',
            r'\begin{tabular}{@{}llrrrr@{}}\toprule',r'Prompt & Program condition & Cancel BA [CI] & Cancel AUC & Return BA [CI] & Return AUC\\\midrule']
        for arm in PROMPTS:
            for cond in ('raw','padding_only','shape_only','shape_const'):
                a=rows[view,arm,cond,'cancel'];b=rows[view,arm,cond,'return']
                supp.append(f"{arm} & {cond.replace('_',' ')} & {ci(a['suite_ba'],a['suite_ba_ci95'])} & {a['suite_auroc']:.3f} & {ci(b['suite_ba'],b['suite_ba_ci95'])} & {b['suite_auroc']:.3f}"+r'\\')
        supp += [r'\bottomrule\end{tabular}\end{table}']
    supp += [r'\clearpage',r'\begin{table}[ht]\centering\small',
        r'\caption{E9 utility and overhead on held-out episodes. Reward is the native state-and-required-output criterion. Overflow is the session fraction (\%). Ratios use the same prompt\textquotesingle s raw condition.}',
        r'\begin{tabular}{@{}llrrrrrr@{}}\toprule',
        r'Prompt & Condition & Reward [CI] & Calls ratio & Bytes ratio & Count overflow & Cap overflow & Underfill\\\midrule']
    for arm in PROMPTS:
        for cond in ('raw','padding_only','shape_only','shape_const'):
            u=util[arm,cond]
            supp.append(f"{arm} & {cond.replace('_',' ')} & {ci(u['native_reward']['mean'],u['native_reward']['ci95'])} & {u['call_ratio']:.2f} & {u['wire_ratio']:.2f} & {pct(u['template_overflow_rate'])} & {pct(u['framing_overflow_session_rate'])} & {pct(u['template_underfill_rate'])}"+r'\\')
    supp += [r'\bottomrule\end{tabular}\end{table}']
    a=rows['network','baseline','raw','cancel'];b=rows['network','baseline','raw','return']
    supp.append(f"Cancellation has {a['positive_test_tasks']} positive tasks across {a['positive_customer_clusters']} customers; return has {b['positive_test_tasks']} positive tasks across {b['positive_customer_clusters']} customers. Of 2,000 bootstrap draws, {a['invalid_single_class_bootstrap_draws']} cancellation and {b['invalid_single_class_bootstrap_draws']} return draws contain only one class and are discarded. These sample sizes restrict power and generalization.")
    delta=data['reward_rules_minus_baseline']
    supp.append('The task-paired rules-minus-baseline reward difference is '+ci(delta['mean'],delta['ci95'])+r' percentage points. Mechanical rule-compliance proxies are reported separately below; they do not constitute an authorization or complete natural-language compliance audit.')
    supp += [r'\begin{table}[ht]\centering\small',r'\caption{Two mechanical workflow-rule proxies (\%). Both proxies are evaluated on both prompt arms.}',
        r'\begin{tabular}{@{}lrrr@{}}\toprule',r'Prompt & One successful customer read first & Order read before write & Both measured proxies\\\midrule']
    for arm in PROMPTS:
        d=util[arm,'raw']['rule_compliance']
        supp.append(arm+' & '+' & '.join(ci(d[k]['mean'],d[k]['ci95']) for k in ('user_details_once_before_order','read_before_order_write','all_measured_rules'))+r'\\')
    supp += [r'\bottomrule\end{tabular}\end{table}',
        'The formal grid used '+str(valid['model_calls'])+' model decisions; total reported input and output tokens were '+str(valid['model_usage']['input_tokens'])+' and '+str(valid['model_usage']['output_tokens'])+'. Input counts include cached tokens. Pilot, aborted-batch and connectivity-check costs are separate. The structured action log supports offline state and statistical replay; it cannot guarantee identical fresh generations from a mutable provider alias.',
        r'All individual attacker predictions, bootstrap definitions, prompt contrasts, task statuses, cover errors, calibration provenance and immutable input hashes are supplied in \path{experiments/sp2027-r4/}. No external replication or independent human coding is claimed.']
    texwrite(tabledir/'r4-supp.tex','\n\n'.join(supp))
    print('R4_TABLES_GENERATED')

if __name__=='__main__':main()
