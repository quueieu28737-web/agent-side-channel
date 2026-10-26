"""Focus the SoK on decisions licensed by source-bound evidence."""
from pathlib import Path
import json,re
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
def read(n):return (M/n).read_text(encoding='utf8')
def write(n,s):(M/n).write_text(s,encoding='utf8',newline='\n')
def replace(n,a,b):
 s=read(n);assert a in s,(n,a[:80]);write(n,s.replace(a,b))

write('sections/28-fingerprint-dependencies.tex',r'''\section{Which Evidence Supports Defense Transfer?}\label{sec:evaluation}\label{sec:threats}
\subsection{Separate the evaluated object before counting holdouts}
RQ3 distinguishes three questions: does an \emph{attack} recognize new inputs or systems; is a \emph{defense condition} evaluated; and does a \emph{fixed attacker or defense calibration} carry from a specified source to a target? Table~\ref{tab:r26-transfer-objects} makes the distinction operational. Repeating a defense on several models can establish condition-specific outcomes without establishing a held-out model or transferring a fitted calibration.
\input{tables/r26-transfer-objects}

The 82-family matrix in Appendix~\ref{app:holdouts} is a discovery index for these questions. Its six axes are task/input/user, model, harness/topology, hardware, network/load and time. H marks reported separation, V condition variation/recalibration, X a scoped restriction, and ? unresolved extraction. The 13 task/input H entries include only four mitigation families; all three model H entries concern attack/identification generalization in families outside the 20-family mitigation audit. The two topology H entries occur in mitigation families, but their held-out objects are workflow recognizers. These counts therefore cannot be read as 13 task-transfer or three model-transfer validations of defenses. S34 identifies each H entry and its evidence object; S28 preserves the full matrix and source scopes.

\subsection{A changed generator and a tested defense are different bindings}
LLM-Fin, ArchSnoop and LeakyLMs evaluate recognition of unseen model variants or architectures \cite{nazari2024llmfin,weng2026archsnoop,majidi2026leakylms}. This supplies attack-side model generalization. In the traffic benchmark, graph-to-star and star-to-graph classification explicitly move the fitted attacker across topologies; the prompt/temperature countermeasures are separate evaluations \cite[V-B--C]{pouryousef2026traffic}. Dangol's leave-composition-out test likewise examines recognition of a novel workflow shape, separately from its protected-capture frontier \cite[9.8--9.12]{dangol2026workflow}. Neither topology entry licenses a transported defense calibration.

There is nevertheless useful \emph{defense-side variation} evidence. Time Will Tell applies the same fixed-length instruction to two models and reports different residual classification ASRs; this tests a common rule under changed generators \cite[VII-B]{timewilltell2024}. Whisper Leak evaluates mitigation conditions across provider-models, while its prompt holdout describes the classifier protocol \cite[3.2,6]{whisperleak2025}. Preserve those per-condition results; a shared rule, a refitted local attack, a source-trained attack and a source-calibrated defense are four distinct comparisons.

\paragraph{Deployment decision}
For the proposed change, name the source, target, held-out unit, quantities held fixed or refitted, and protected outcome. Carry forward only the corresponding binding. An attack-generalization result justifies including that attacker at the target; a defended-condition result supplies its local outcome; a source-to-target defense-calibration result supports only the stated transfer. This prevents both overclaiming portability and discarding useful local evidence. Unresolved hardware/time entries in the discovery matrix identify source follow-up, not absent experiments.
''')
write('tables/r26-transfer-objects.tex',r'''\begin{table}[t]\centering\footnotesize
\caption{Three evidence objects for RQ3. The same family may supply several objects in separate experiments.}\label{tab:r26-transfer-objects}
\begin{tabularx}{\columnwidth}{@{}p{.24\columnwidth}YY@{}}\toprule
Object & Required link & Permitted reuse\\\midrule
Attack generalization & Training/profiling source $\to$ held-out inputs or systems; attack outcome. & An attacker or recognition method covers the stated target domain.\\
Defended condition & Named mechanism, local fitting, defended test and outcome. & Retain that operating point; multi-model testing alone is not held-out transfer.\\
Defense transfer & Source-selected policy/calibration held fixed $\to$ target; local-calibration comparator and attacker fit specified. & Transport the evaluated policy only over the tested direction and scope.\\\bottomrule
\end{tabularx}\end{table}
''')
replace('tables/r9-rq-findings.tex',
 'RQ3: transfer axes & Reported task/input holdouts (13 families) and model holdouts (three) address different changes. Hardware/time entries are mostly unresolved, identifying the source scope that must be established before reuse.',
 'RQ3: evidence for transfer & Attack generalization, defended-condition evaluation and defense-calibration transfer support different decisions. None of the three model H entries belongs to the mitigation audit; a family\'s holdout cannot be inherited by its defense result.')
replace('sections/03-methodology.tex','which holdouts establish portability across tasks, configurations and hardware (RQ3)',
 'which evidence distinguishes attack generalization, defended-condition evaluation and defense transfer across tasks, configurations and hardware (RQ3)')
replace('sections/03-methodology.tex','S33 reports status-rule, unresolved-binding and family-deletion sensitivity without changing archived labels.',
 'S33 retains the initial status-rule and family-deletion sensitivity. S34 documents a targeted reread of all 11 formerly unverified family cells, with versioned source receipts, old/new codes and remaining reporting gaps. It also specifies record boundaries and all cohort memberships.')

s=read('sections/04-scope.tex')
start=s.index('A study family contributes multiple records')
end=s.index('\n\\input{tables/result-record-schema}',start)
s=s[:start]+r'''A record is a comparison unit with a source-indexed parameter grid, not an independent trial. We split when a change of primitive, execution mode, target/receiver contract or separately measured cost object would alter what a result can support. We retain models, datasets, parameter values and repetitions as coordinates within that unit; numerical joins must preserve those coordinates. Source versions are reconciled within a family before extraction.'''+s[end:]
anchor=r'\paragraph{From contracts to an audit}'
addition=r'''\paragraph{Record boundaries and coverage}
The extraction frame comprises the evaluated-mitigation sections and their linked methods, figures and cost/utility analyses for the 20 mitigation families, plus six explicitly named contextual controls. A defense discussion without a scoped evaluated result stays in the map. The 39-record ledger inventories these comparison units, rather than every plotted number in the 82-family corpus. S34 publishes all record scopes and split decisions. Three examples fix the granularity:
\begin{itemize}
\item \textbf{Split:} Early Bird's $K$-prefix recovery oracle and semantic-cache processing benchmark change both primitive and measured object; their numbers cannot form one protection--cost point.
\item \textbf{Retain coordinates:} SparLeak's model-by-replacement-intensity ASR/ROUGE grid remains one mitigation record. Each intensity's inference/quality pair must be retained together; selecting the lowest ASR and highest ROUGE from different rows is disallowed.
\item \textbf{Split outcome, share package:} CachePrune's direct recovery and contextual guessing require two target contracts. They reference one shared default quality/cost package, counted once when joining configurations.
\end{itemize}

\paragraph{Question cohorts precede compatibility judgments}
Records enter one declared comparison question by the intervention and receiving object, not by score or verdict: delivered traffic, service-cache reuse, local memory/resource behavior, behavioral humanization, generator fingerprinting or fixed instructions. Three contextual singletons concern access gates, contention and filter-created views. S34 lists operational membership rules and all 39 assignments. When a mechanism spans several questions, retain the primary extracted question and document the alternative; a new cross-cohort question requires a new inventory. A shared cohort admits a pair for inspection; it does not make different targets or costs compatible. These retrospective grouping rules define the reported census, rather than a preregistered universal taxonomy.

'''
assert anchor in s;s=s.replace(anchor,addition+anchor);write('sections/04-scope.tex',s)

s=read('sections/27-intervention-contracts.tex')
s=s.replace('The final inventory retains all 528 earlier pair judgments and adds 31 related judgments for the six expansion records, with source locators and reasons. Examples illustrate this census rather than define its sample.',
 'Every related pair has source locators and a comparison reason. Examples illustrate this census rather than define its sample.')
s=s.replace('\\NRR{} and \\NRV{} retain distinct source states: the 11 unverified cells are five R4 and six R5 bindings, which are distinguished from an attack failure.',
 'The targeted source reread resolves the reporting status of the 11 formerly unverified family cells: four partial bindings and seven unreported links in the inspected scope. No new B is inferred. S34 distinguishes partial supporting evidence from an unreported contrast and preserves each original code.')
s=s.replace('SparLeak\'s matched ASR/ROUGE pairs qualify as component utility under R8, correcting its former partial code.',
 'SparLeak\'s intensity-specific ASR/ROUGE pairs supply component utility under R8.')
a=s.index('Accepting P and ? as if bound leaves the triple join')
b=s.index('\n\\soktakeaway',a)
s=s[:a]+'''The targeted reread leaves all supported joins unchanged. Its contribution is to specify the missing link: a documented classifier plus a defense score is partial evidence for protected fitting; two classifiers on one condition are not an adaptation contrast. S33 retains the pre-reinspection stress counts, while S34 reports the current codes and recomputed queries. Removing CachePrune still removes the sole triple package. These are inventories of usable evidence, not prevalence estimates.'''+s[b:]
write('sections/27-intervention-contracts.tex',s)

s=read('sections/11-discussion.tex')
s=s.replace('Each exposes a different reason why a deployment conclusion cannot be read directly from a mechanism name.',
 'Their value is the decision they change: retain an aligned result, separate a wrongly joined package, or require a result at a changed execution boundary.')
insert=r'''\subsection{A positive reuse path: from comparison to a candidate configuration}
The Early Bird $K$-prefix record and CachePrune's direct-recovery record form one of the 17 descriptive matches: both address sensitive-token recovery through cache-reuse probes \cite[V-A]{earlybird2025}\cite[5.1--5.6]{wu2026cacheprune}. This permits an analyst to retain both mechanisms as candidates for that threat, while keeping the oracle and executed-serving measurements separate. The joint audit then changes the next step. CachePrune supplies a default configuration package linking recovery, generation quality and serving cost; the analyst can use that package for a source-scoped feasibility assessment. Early Bird's semantic-cache overhead cannot price its $K$-prefix candidate, so that candidate still needs a serving-cost measurement. Neither a pooled recovery ranking nor a new-hardware guarantee follows from this comparison.

\paragraph{What the three findings add}
Record-level comparison turns a mechanism-level shortlist into correctly scoped alternatives. Configuration-level joint binding distinguishes a reusable package from borrowed utility or cost. Deployment decisions then identify the changed object and the measurement it needs. Compared with established WF practice on adaptive attacks, shifts and online costs \cite{juarez2014critical,mathews2023critical}, the LLM/agent synthesis makes three additional joins explicit: prefix versus semantic-cache primitives, discarded read outputs versus executed state changes, and component generation quality versus planner outcomes. The contribution is the source-backed decision change, not a new information-processing theorem.

'''
anchor=r'\subsection{A deployment query determines the evidence to retain}'
assert anchor in s;s=s.replace(anchor,insert+anchor);write('sections/11-discussion.tex',s)
s=read('tables/r19-deployment-decisions.tex')
s=s.replace('Changed boundary & What the old result leaves open & Minimum evidence before reuse',
 'Reuse question & Evidence decision & Retain or measure next')
s=s.replace(r'Component $\rightarrow$ workflow utility',r'Component $\rightarrow$ workflow utility')
s=s.replace(r'Component $\rightarrow$ workflow utility &',r'Bound cache-reuse package & Early Bird prefix recovery and CachePrune direct recovery permit a scoped candidate comparison; CachePrune binds a shared utility/cost package. & Retain that package for its measured configuration; measure prefix-policy serving cost separately, and re-evaluate any changed workload/hardware.\\'+'\n'+r'Component $\rightarrow$ workflow utility &')
write('tables/r19-deployment-decisions.tex',s)

# Distinguish fixed historical sensitivity from the current reread.
s=read('sections/65-audit-sensitivity.tex')
s=s.replace('This deterministic reanalysis uses the archived',
 'This section preserves the pre-reinspection sensitivity snapshot; current source-reconciliation codes and queries are in S34. The deterministic reanalysis uses the archived',1)
s=s.replace('the full cell table in Section~\\ref{app:record-joins} supplies source locators and rationales.',
 'the archived pre-reinspection cell file supplies its labels; Section~\\ref{app:record-joins} presents the current cells and S34 gives the exact changes.')
write('sections/65-audit-sensitivity.tex',s)
s=read('sections/58-record-joint-audit.tex')
s=s.replace(r'\label{app:record-joins}',r'\label{app:record-joins}'+'\n'+r'The current record cells incorporate the targeted source reconciliation in S34. Supported B joins and record/pair membership are unchanged; S33 remains the labeled pre-reinspection sensitivity snapshot.')
write('sections/58-record-joint-audit.tex',s)
for n in ['sections/56-holdout-matrix.tex','sections/59-holdout-compact.tex']:
 s=read(n);idx=s.index('\n',s.index(r'\label{app:holdouts}'))
 s=s[:idx]+ '\n'+r'This is a family-level discovery index, not a count of defense-transfer tests. The three model H entries concern attack/identification generalization; even an H in a mitigation family must be linked to its defended condition before reuse. The main RQ3 table separates those evidence objects, and S34 identifies every H entry.'+s[idx:]
 write(n,s)

replace('main.tex','Third, a six-axis holdout matrix connects reported input, model, topology, hardware, network and temporal changes to deployment decisions.',
 'Third, a six-axis holdout synthesis separates attack generalization from defended-condition tests and defense transfer. The distinction prevents a paper\'s attack-side holdout from being inherited by its mitigation claim.')
replace('sections/01-introduction.tex','The 82-family, six-axis holdout map identifies which deployment changes the sources evaluate.',
 'The 82-family, six-axis holdout map separates attack generalization from defended-condition evaluation and source-to-target defense transfer.')
replace('sections/01-introduction.tex','The SoK carries this discipline across LLM receiving views, stateful tool interventions and configuration-linked utility/cost evidence.',
 'The SoK extends this discipline to substitutions within a paper: prefix versus semantic-cache primitives, discarded reads versus executed state changes, and component quality versus workflow utility. Its positive reuse path retains a source-qualified candidate and its bound package, rather than only listing missing evidence.')
replace('sections/12-conclusion.tex','The six-axis holdout synthesis then connects those judgments to the deployment change being proposed.',
 'The six-axis holdout synthesis separates attack generalization, local defended outcomes and transported defense calibration before connecting evidence to a deployment change. A positive cache-reuse example shows how to retain a candidate and its bound quality/cost package while identifying the specific measurement needed for another candidate.')
write('sections/66-source-reconciliation.tex',r'''\section{Source Reconciliation, Record Boundaries and Transfer Objects}\label{app:source-reconciliation}
This targeted reporting audit revisits all 11 formerly unverified family R4/R5 cells and their affected record cells. It retrieves the official versioned HTML of six papers and records content hashes, section/table locators, old/new status and a rationale. Three further versioned papers support the positive reuse and holdout examples. It adds no model calls, customers or behavioral experiments. The remaining questions concern what the published evaluations bind; a new Sol run cannot establish the training provenance of somebody else's reported result.

\subsection{A bounded reading rule}
B requires the requested connection to be explicit. P applies when relevant training/profiling and defended results are described but their condition-specific connection is incomplete. U means the requested connection is not reported in the inspected methods/result passages; it does not mean the authors never performed it. A remains inaccessible source, and ? remains a binding not adjudicated within the reading scope. For R5, an undefended-versus-defended score or two detector architectures do not establish clean-trained versus protected-trained attacks on identical defended tests. We do not infer B from an implementation alone without its result binding.

\input{tables/r26-source-review}

Four family cells become P and seven become U; no additional B is inferred. Nineteen record cells are updated consistently, including AHB's offline fitting as partial under the same code-versus-run distinction. Six other record-level ? cells remain in NetEcho, Early Bird and Dangol scopes, distinct from the 11 family cells reviewed here. Current record cells appear in Section~\ref{app:record-joins}; the artifact records the 19 exact changes. These targeted decisions resolve the reporting category, not the source's unpublished execution history.

\subsection{Effect on the quantitative synthesis}
All supported joins remain unchanged: inference--utility 4/22, inference--cost 5/22, matched adaptation--inference 2/17, triple join 2/20, and all five bindings 0/14. Query masks still start from the same 33 mitigation records. The triple package remains CachePrune's two outcomes at one shared configuration. The pair census remains 741 pairs, 133 related, with 17 descriptive matches, 105 mismatches and 11 unresolved pair contracts. Family-cell reporting and pair-contract status are separate objects.
\input{tables/r26-current-sensitivity}

\subsection{Recordization and extraction coverage}
We preserve a hierarchy: family/version $\to$ comparison record $\to$ model/workload/parameter coordinates $\to$ measured outcomes. A comparison record splits when the primitive, execution mode, receiver/target contract or measured cost object changes. Multiple numerical cells within a common record are not additional independent observations. A join must match its configuration coordinates; two endpoints can share a quality/cost package without becoming a paired effect. The extraction frame is the 20 mitigation families' scoped evaluations and linked methods/outcomes plus six contextual controls. It is not an enumeration of all numeric cells or all attack experiments in the 82-family map.

\begin{itemize}
\item Early Bird: split the prefix-recovery oracle from semantic-cache processor cost (V-A versus V-B).
\item Dangol: split transformed captures from a live OHTTP loopback (9.8--9.9 versus 9.7); a common workflow target permits description, not a common execution denominator.
\item SparLeak: retain model/intensity coordinates within the random-replacement record; Table 4's ASR and ROUGE stay paired by row.
\item CachePrune: split direct and contextual recovery targets, but deduplicate the shared default quality/cost package.
\item OTRO: keep measured unpadded execution separate from a padded operating point and its derived cost.
\end{itemize}
These rules articulate the existing ledger retrospectively; they are not a claim of preregistered extraction. The released record-scope file gives every one of the 39 units, its source locator, retained parameter coordinates, configuration package and question cohort.

\input{tables/r26-cohort-rules}

Question assignment uses the primary extracted intervention/receiver surface, then the intended comparison. Network destination cover belongs to traffic-envelope even when it is implemented with a decoy agent; site/mobile behavioral edits belong to humanization. Fixed instructions and generator-identity countermeasures retain their declared narrower questions. Cost-only records stay with the mechanism they would otherwise be used to price. A record that could answer another question needs an explicit alternate-cohort audit; outside-cohort status is not evidence of incompatibility. The six nonsingleton cohorts generate all 133 related pairs; three singleton contextual groups generate none. The full cross-product remains available for alternative queries.

\subsection{What the holdout index evaluates}
The 19 H entries across six axes refer to reported attack/identification splits in the archived extraction. Their existence does not bind a defense to that split. Table~\ref{tab:r26-h-objects} lists the entries and whether the family also has a mitigation record. In particular, all three model H entries are outside the 20 mitigation families. The two topology entries concern attacker generalization: Dangol's new-composition recognition and the traffic benchmark's graph/star classifier transfer. Neither is a demonstrated source-calibration transfer of the defense.

Defense-conditioned variation is still useful. Time Will Tell's shared fixed-length instruction has model-dependent outcomes; Whisper Leak's mitigation results remain provider/condition-specific. In these cases retain the tested rule and residual attack outcome, rather than relabel multiple conditions as a held-out defense-calibration experiment. For actual calibration transfer, specify source training, frozen parameters, target testing, local recalibration and attacker fitting separately. The artifact's H-entry ledger carries each original locator and qualification; the 82-family discovery matrix remains unchanged.
\input{tables/r26-h-objects}

\subsection{Positive reuse and changed decisions}
Early Bird's prefix record and CachePrune's direct-recovery record are an existing descriptive match. Both can inform a cache-reuse threat shortlist; they do not support a numerical ranking across oracle and serving measurements. CachePrune supplies a configuration-linked recovery/quality/cost package for scoped feasibility analysis. The semantic processor benchmark in Early Bird instead leaves the prefix candidate's serving cost open. This produces a positive retention decision and a specific next measurement. The main decision table also distinguishes read-cover state effects, final-emitter captures and workflow utility, extending the established WF evaluation discipline to LLM/agent execution objects.
''')
replace('supplement.tex',r'\input{sections/65-audit-sensitivity}',r'\input{sections/65-audit-sensitivity}'+'\n'+r'\input{sections/66-source-reconciliation}')

aud=json.loads((O/'family-cell-review.json').read_text());families={r['family']:r for r in aud}
t=[r'\begin{longtable}{@{}p{.18\textwidth}p{.10\textwidth}p{.19\textwidth}p{.45\textwidth}@{}}',r'\caption{All 11 family-cell rereads. Each old code is ?. Source versions are pinned in the receipt file.}\label{tab:r26-source-review}\\',r'\toprule Family & New R4/R5 & Inspected locator & Evidence and remaining link\\\midrule\endfirsthead',r'\toprule Family & New R4/R5 & Inspected locator & Evidence and remaining link\\\midrule\endhead',r'\bottomrule\endfoot']
for family,r in families.items():
 items={a['item']:a['new'] for a in aud if a['family']==family};codes=items.get('R4','P (retained)')+'/'+items['R5']
 t.append(r['name']+r'~\cite{'+family+'} & '+codes+' & '+r['source_locator']+' & '+r['reason']+r'\\')
t.append(r'\end{longtable}');write('tables/r26-source-review.tex','\n'.join(t)+'\n')
stress=json.loads((O/'analysis.json').read_text())
import csv
ss=list(csv.DictReader((O/'status-sensitivity.csv').open()))
t=[r'\begin{table}[ht]\centering\small',r'\caption{Current query stress counts after source rereading. Only B is supported; weaker columns remain counterfactual. S33 preserves the earlier snapshot.}\label{tab:r26-current-stress}',r'\begin{tabular}{@{}lrrrrr@{}}\toprule Query & Eligible & B & B/P & B/? & B/P/?\\\midrule']
labels=['Inference + utility','Inference + cost','Matched adaptation + inference','Inference + utility + cost','All five bindings']
for q,label in zip(stress['joint'],labels):
 rr=[r for r in ss if r['query']==q['query']];t.append(label+' & '+str(q['eligible'])+' & '+' & '.join(r['selected'] for r in rr)+r'\\')
t += [r'\bottomrule\end{tabular}\end{table}'];write('tables/r26-current-sensitivity.tex','\n'.join(t)+'\n')
co=json.loads((O/'cohort-rules.json').read_text())
t=[r'\begin{longtable}{@{}p{.19\textwidth}p{.08\textwidth}p{.08\textwidth}p{.56\textwidth}@{}}',r'\caption{Declared question groups. Full record identities are in the released scope file.}\label{tab:r26-cohorts}\\',r'\toprule Question group & Records & Pairs & Membership rule\\\midrule\endfirsthead',r'\toprule Question group & Records & Pairs & Membership rule\\\midrule\endhead',r'\bottomrule\endfoot']
for r in co:t.append(r['cohort'].replace('-', ' ')+' & '+str(r['record_count'])+' & '+str(r['pairs'])+' & '+r['membership_rule']+r'\\')
t += [r'\end{longtable}'];write('tables/r26-cohort-rules.tex','\n'.join(t)+'\n')
ho=json.loads((O/'holdout-object-ledger.json').read_text())
names={'task_input_user':'Task/input/user','model':'Model','harness_topology':'Topology','network_load':'Network/load'}
t=[r'\begin{longtable}{@{}p{.25\textwidth}p{.16\textwidth}p{.10\textwidth}p{.40\textwidth}@{}}',r'\caption{H entries by evaluated object. All entries locate attack/recognition splits; defense-holdout and calibration-transfer bindings are not established by the H flag. M indicates membership in the mitigation audit, not a defended holdout.}\label{tab:r26-h-objects}\\',r'\toprule Family & Axis & M & Archived qualification\\\midrule\endfirsthead',r'\toprule Family & Axis & M & Archived qualification\\\midrule\endhead',r'\bottomrule\endfoot']
for r in ho:t.append(r['name']+r'~\cite{'+r['family']+'} & '+names[r['axis']]+' & '+('yes' if r['mitigation_family'] else 'no')+' & '+r['qualification'].replace('&',r'\&')+r'\\')
t += [r'\end{longtable}'];write('tables/r26-h-objects.tex','\n'.join(t)+'\n')
print('R26_MANUSCRIPT_WRITTEN')
