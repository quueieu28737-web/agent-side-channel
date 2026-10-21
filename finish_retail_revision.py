from pathlib import Path
import json,sys,random
from collections import Counter
P=Path(__file__).resolve().parent/'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001'
M=P/'manuscript';A=P/'experiments/reviewer-audit'
sys.path.insert(0,str(A));import retail_replay as impl
u=json.loads((A/'retail_utility.json').read_text());o=json.loads((A/'retail_observers.json').read_text());d=json.loads((A/'retail_diagnostics.json').read_text())
rows=json.loads((A/'retail_units.json').read_text())
def write(f,s):(M/f).write_text(s.strip()+'\n',encoding='utf-8')
def p(x):return f'{100*x:.2f}'
def ci(m):return f"{p(m['accuracy'])} [{p(m['acc_ci95'][0])}, {p(m['acc_ci95'][1])}]"
labels={'baseline':'No cover','discard':'Discard','shadow':'Shadow','read_only':'Read only','live_idempotent_address':'Address self-write','live_idempotent_item_swap':'Item self-write','live_instruction_aware':'Instruction aware','live_decoy_account':'Other-account cancel','live_mutation':'Blind cancel'}
s=r'''\begin{table}[t]\centering\footnotesize
\caption{Retail state and observer results. State columns use 97 eligible tasks (291 units per position); observer columns use 49 held-out tasks (147 units). Percentages are task means across three seeds. B/A denotes before/after.}\label{tab:tau-cover-bridge}
\setlength{\tabcolsep}{2.2pt}
\begin{tabularx}{\columnwidth}{@{}Yrrrr@{}}\toprule
\multicolumn{5}{@{}l}{\textbf{A. Distinct state scopes (reference execution as comparator)}}\\
Policy / position & DB eq. & Account eq. & Object eq. & Mutated\\\midrule
'''
for r in u:
    if r['policy'] in ['baseline','discard','shadow','read_only','live_idempotent_address']:
        if r['position']=='after':continue
        pos='B/A'
    else:pos='B' if r['position']=='before' else 'A'
    s+=labels[r['policy']]+' '+pos+' & '+' & '.join(p(r[k]) for k in ['eligible_native_reward','eligible_user_orders_equal','eligible_gold_touched_equal','eligible_cover_mutated_rate'])+r'\\'+'\n'
s+=r'''\midrule
\multicolumn{5}{@{}l}{\textbf{B. Legacy learned observer versus allowed-view rules}}\\
Policy / position & $D_0$ acc. & $D_2$ acc. & $D_2$ BA & Rule acc.\\\midrule
Majority (all conditions) & 77.55 & 77.55 & 50.00 & ---\\
'''
for r in o:
    if r['policy'] not in ['live_instruction_aware','live_decoy_account','live_mutation']:continue
    ms=r['methods'];s+=labels[r['policy']]+' '+('B' if r['position']=='before' else 'A')+' & '+' & '.join([p(ms['D0']['accuracy']),p(ms['D2_legacy_linear']['accuracy']),p(ms['D2_legacy_linear']['balanced_accuracy']),p(ms['known_position_filter']['accuracy'])])+r'\\'+'\n'
s+=r'''\bottomrule\end{tabularx}
\par\smallskip\raggedright
DB eq.: equality of orders/users against reference (products are read-only), the native reward's database criterion, not an output-response/authorization check. Account eq.: all orders owned by the active user plus that user's record. Object eq.: objects changed by the reference program, not all accessed objects. Mutated: cover itself changes state. Other-account calls yield 0\% DB equality but 100\% active-account equality. BA: balanced accuracy. Rule: remove the known first/last cover call, then inspect cancellation verbs; blind/other-account cancellation also admits the $N_{\rm cancel}\ge2$ rule. Both rules attain 100\% acc./BA in their stated conditions. Other non-cancellation policies retain 100\% verb inference. Full intervals, AUROC and confusion matrices appear in Supplement S9 and the JSON artifact.
\end{table}'''
write('tables/tau-cover-bridge.tex',s)

# Confirm the successful same-item operation has zero price difference in initial data.
ns,tools,base,tasks=impl.load_tau();prices=[]
for tid,t in enumerate(tasks):
    cand=sorted(k for k,v in base['orders'].items() if v['user_id']==t.user_id and v['status']=='pending')
    if not cand:continue
    for seed in impl.SEEDS:
        oid=random.Random(seed+tid*1009).choice(cand);it=base['orders'][oid]['items'][0]
        variant=base['products'][it['product_id']]['variants'].get(it['item_id'])
        if variant and variant['available']:prices.append(variant['price']-it['price'])
(A/'same_item_price_check.json').write_text(json.dumps({'successful_initial_selections':len(prices),'nonzero_price_differences':sum(abs(v)>1e-8 for v in prices),'min':min(prices),'max':max(prices)},indent=2))

write('sections/35-tau-cover-bridge.tex',r'''
\subsection{Retail execution: state scope and a visible-call counterexample}\label{sec:tau-cover-bridge}
We replay the 115 public reference programs in the pinned $\tau$-bench retail simulator. There is no LLM planner or user simulator in this experiment. Ninety-seven tasks have an initially pending order owned by the task user; 18 have none and receive no cover. Three seeds select orders, and cover is inserted before or after the prescribed program. Utility uses 97 task clusters, each with three repeated units per position. Policies include no cover, discard, shadow execution, read only, address self-write, item self-write, instruction-aware selection, other-account cancellation and blind cancellation. Destructive conditions are local negative controls, not proposed deployment policies.

\paragraph{Separate the outcome scopes}
Table~\ref{tab:tau-cover-bridge} reports reference database equality, full active-account equality and equality on objects \emph{changed} by the reference program. The last scope does not include every read/accessed object. The database criterion corresponds to the state part of the native evaluator; the extension script does not evaluate generated response correctness and we do not relabel its state equality as an end-to-end native task reward. All-account equality now checks every order owned by the active user and that user's record, rather than only initially pending orders.
\input{tables/tau-cover-bridge}

Address self-writes preserve the reference state in this simulator. Item self-writes mutate state in 173/291 pre-insertion units (59.45\%): the tool changes the status to \texttt{pending (item modified)} and appends a refund entry even when the item identifier and price are unchanged. The remaining 118/291 calls fail because the requested variant is unavailable, explaining why this mutation rate is below blind cancellation's 291/291 successful calls. This is a state-preservation counterexample from one API, not a prevalence estimate or a discovery about idempotence. Formally, a no-change requirement $f(s,a)=s$ differs from repeated-call idempotence $f(f(s,a),a)=f(s,a)$.

Instruction-aware cover uses only instruction text and the initial order table for selection, with address self-write as fallback. It preserves reference-changed objects in 78.35\%/89.69\% of before/after units, but preserves the full account and database in only 35.05\%/46.39\%. Cancelling an unmentioned order can therefore damage a bystander resource. The heuristic was developed using the available task collection; it has no held-out policy-development evaluation. Its 68/97 availability (70.10\%) and the item-self-write object equality of 204/291 (70.10\%) are separate counts that happen to yield the same percentage.

The other-account condition selects a pending order belonging to another simulated user. It is not a provisioned dedicated decoy account. It preserves the active user's complete account and reference-changed objects in these tasks, while changing the shared database in every eligible unit (0\% database equality). Thus account isolation of an effect cannot be described as whole-database preservation or an authorized production defense.

\paragraph{Observer permissions and simple attacks}
The secret label is whether the reference program \emph{attempts} a cancellation, including a call that may fail after cover execution. The observer sees the ordered dispatched tool names, write counts and response lengths; failed calls remain visible. It sees no arguments, user/order identifiers or database state. We do not infer that a passive TLS observer has these permissions. A backend with plaintext state would instead need a different confidentiality target.

The fixed task split contains 48 training tasks (7 positive, 41 negative) and 49 test tasks (11 positive, 38 negative); seeds stay within tasks. Always predicting no cancellation gives 77.55\% test accuracy and 50\% balanced accuracy. The legacy $D_2$ linear classifier uses cancellation presence, write count and write-response bytes. Its 68.03--73.47\% accuracy under cancellation cover is below the majority baseline, and its balanced accuracy ranges from 45.61\% to 52.79\%. An increase over $D_0$ is therefore insufficient evidence for its claimed privacy interpretation.

For blind and other-account cancellation, exactly one extra cancellation is dispatched in every eligible session. The permitted rule $\widehat y=\mathbf{1}[N_{\rm cancel}\ge2]$ recovers the reference label at 100\% accuracy and balanced accuracy on all 49 test tasks and three seeds, before and after insertion. For any policy with one live cover call at a known first/last position, removing that call and testing for a remaining cancellation also gives 100\%. It needs no identifiers, no response content and no training labels. These are measured finite-sample results and a structural property of the fixed insertion design, not proof of general attack performance. Identifier filtering is unnecessary in this view and is not claimed as an evaluated attack.

\paragraph{Terminal equality does not establish path properties}
Blind pre-insertion cancellation leaves the final database equal to reference in 33/291 units across 12 tasks, even though it preempts the later reference cancellation. The exact per-task counts are in Supplement S9. After insertion, 120/291 cover calls are rejected because reference execution already changed the order's status, and those rejections explain the 41.24\% equality rate. Rejection is not successful benign cover. In the 82 tasks with no reference execution error (246 units), before/after equality is 24/246 (9.76\%) and 94/246 (38.21\%). These results illustrate the limits of endpoint scoring; consent and authorization were not measured.

\soktakeaway{SoK Takeaway 4 (State preservation and inference are separate)}{Same-value tool inputs can change workflow state. Equality on reference-changed objects can miss damage elsewhere in an account; account equality can coexist with global database changes. Even a state-preserving route need not hide a cancellation label from the specified dispatch observer. The tested policies do not establish a privacy--utility frontier.}
''')

s=r'''\subsection{Retail source, permissions and full statistical results}\label{app:tau-cover-details}
The pinned $\tau$-bench commit is \nolinkurl{59a200c6d575d595120f1cb70fea53cef0632f6b}. The instrumented replay preserves the 115 tasks, nine policies, three seeds and two positions (6,210 rows in \path{retail_units.json}); 97 tasks are eligible. The target is the presence of an attempted reference cancellation. Counts include rejected dispatches. The allowed observer receives ordered tool names and response byte lengths, not argument IDs, response contents or backend state. The tool view is separate from the TLS size observer.

The fixed split takes the first 48 sorted eligible task IDs for fitting (7 positive, 41 negative) and the remaining 49 for testing (11 positive, 38 negative). IDs are recorded in \path{retail_diagnostics.json}. Every test task contributes all three seeds. For each task we average accuracy across seeds, then resample 49 tasks 10,000 times for accuracy intervals. Balanced-accuracy intervals independently resample within the 11 positive and 38 negative task strata. These intervals condition on this split, fitted models and saved tasks; policy development was not held out. AUROC uses the uncalibrated ridge linear decision score, including ties. Confusion matrices in \path{retail_observers.json} count 147 task-seed units; they are not 147 independent tasks. Paired $D_2-D_0$ differences are averaged within task before the task bootstrap.

\begin{table*}[t]\centering\footnotesize
\caption{Legacy learned observer on the held-out retail tasks. Intervals are conditional task-bootstrap intervals, not policy-generalization guarantees. The majority baseline is 77.55\% accuracy and 50\% BA.}\label{tab:retail-statistics}
\begin{tabularx}{\textwidth}{@{}Yllll@{}}\toprule
Policy / position & $D_0$ accuracy [95\% CI] & $D_2$ accuracy [95\% CI] & $D_2$ BA [95\% CI] & AUROC\\\midrule
'''
for r in o:
    if r['policy'] not in ['live_instruction_aware','live_decoy_account','live_mutation']:continue
    a=r['methods']['D2_legacy_linear'];s+=labels[r['policy']]+' '+r['position']+' & '+ci(r['methods']['D0'])+' & '+ci(a)+f" & {p(a['balanced_accuracy'])} [{p(a['ba_ci95'][0])}, {p(a['ba_ci95'][1])}] & {a['auroc']:.3f}"+r'\\'+'\n'
s+=r'''\bottomrule\end{tabularx}\end{table*}

The known-position filter scores 100\% accuracy/BA for each policy and position. The cancellation-count rule scores 100\% for blind and other-account cancellation in both positions. Their percentile bootstrap intervals are [100,100] because every observed task is correct; this degeneracy is not a claim about population-level certainty. No identifiers are needed. We do not evaluate an ID-filter attack because IDs are not in the specified view. The legacy model on the other-account after condition recomputes to 71.43\%, correcting the previous prose value 68.03\%; 68.03\% belongs to blind cancellation after insertion.

\paragraph{State metrics and uncertainty}
\path{retail_utility.json} contains task-bootstrap intervals for database equality, full-account equality and equality of reference-changed objects, along with full-census means. The field name \texttt{native\_reward} is retained only for compatibility with the old script; its calculation is orders/users equality, not an invocation of the full reward/response evaluator. Products are shared read-only by the retail tools. The revised account metric checks all orders owned by the active user, plus the user's record. The reference-changed-object set is constructed from baseline differences, not from all accessed objects. Simulator no-cover database equality is a reference-relative 100\%, not proof of user-task success.

\paragraph{Error and denominator reconciliation}
Item self-write before insertion succeeds and changes state in 173/291 units; all remaining 118 errors are unavailable-variant checks. After insertion, 120 errors are non-pending status and 77 are unavailable variants, leaving 94 successful mutations. The raw error strings are retained. Price-difference checks over the 173 initially successful selections find zero differences, but the API still appends a refund and changes the status. The coincidence 204/291 = 68/97 = 70.10\% combines two distinct quantities: preserved reference-changed objects under item self-write and tasks offering an instruction-unmentioned candidate.

For blind cancellation before insertion, database-equal counts by task are: 16:3, 30:3, 31:2, 32:3, 38:3, 54:3, 55:3, 59:2, 66:3, 69:3, 81:2, 99:3. They sum to 33 across 12 tasks. The error-free sensitivity subset is 82 tasks $\times$ 3 seeds = 246 units: 24/246 before and 94/246 after. Simplifying these fractions to 12/123 or 47/123 does not change the underlying sample size. All-unit counts and task IDs are recorded, so repeated seeds are never represented as new independent tasks.
'''
write('sections/36-tau-cover-details.tex',s)
print(json.dumps({'same_item_nonzero_price_differences':sum(abs(v)>1e-8 for v in prices),'retail_rows':len(rows)}))
