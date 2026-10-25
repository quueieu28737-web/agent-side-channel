"""Apply R19 editorial changes to the immutable R18 source baseline."""
from pathlib import Path
import subprocess
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
BASE='d717c2214565e7245aedc026b2d929a9c7bd4818'
def old(name):return subprocess.check_output(['git','show',BASE+':'+(M/name).relative_to(R).as_posix()],cwd=R).decode()
def put(name,s):(M/name).write_text(s,encoding='utf8',newline='\n')
def edits(name,pairs):
 s=old(name)
 for a,b in pairs:
  assert a in s,(name,a);s=s.replace(a,b)
 put(name,s)

s=old('main.tex');a=s.index('Side-channel defenses');b=s.index('\\end{abstract}',a)
s=s[:a]+r'''Side-channel defenses for LLM serving and agent systems are evaluated at one operating point and reused at another. We systematize which deployment changes require new evidence. Our unit is the evaluated result record: one outcome bound to its target, receiver, intervention, attacker fit, workload and cost object. Across 82 study families and 39 records, eight of 15 same-family pairs measure different primitives, targets or costs; only 17 of 133 related pairs support a source-qualified descriptive comparison. Record-local auditing further separates individually reported outcomes from joint evidence: two of 20 applicable mitigation records bind inference, utility and cost, sharing one configuration. Four controlled demonstrations connect these distinctions to emitter placement, stateful cover, calibration and timing. On GLM, importing MiniMax calibration changes cancellation/return balanced accuracy by $+20.8/-17.3$ points; paired customer intervals resolve the return reduction but not the cancellation increase. The imported calibration also increases byte cost from $15.95\times$ to $18.65\times$. These target-specific, costed contrasts turn transfer boundaries into an operational decision table: identify the changed boundary, retain the evidence that still applies, and test the missing binding before deployment.
''' +s[b:];put('main.tex',s)

edits('sections/01-introduction.tex',[
('6 of 13 same-family pairs in the original 33-record audit','8 of 15 same-family pairs in the complete 39-record audit'),
('only 16 of 102 related record pairs','only 17 of 133 related record pairs'),
('Reuse evidence is scarcest where deployment needs it: matched adaptation is bound for 2/11 applicable mitigation families and protected-point utility for 3/17, while hardware and temporal transfer remain unresolved for most families.', 'Record-local joins identify the actionable gap: two of 20 applicable mitigation records bind inference, utility and cost, and both share one configuration. The 82-family holdout matrix identifies which transfer axes have source-bound evidence.'),
('Controlled experiments on a retail agent workload','Controlled experiments using saved LLM responses and a retail agent workload'),
('Moving calibration from MiniMax to GLM changes cancellation/return BA from 50.0/67.3\\% to 70.8/50.0\\%: protection moves in opposite directions, so no single transfer score summarizes it.',r'The GLM cancellation/return point contrast is $+20.8/-17.3$ BA points, with paired 95\% intervals $[-12.6,35.3]/[-38.2,-5.3]$. Thus the return reduction is resolved, while the cancellation direction remains uncertain. Table~\ref{tab:calibration-transfer} prices each target-specific contrast; Table~\ref{tab:r19-decisions} turns the findings into minimum re-evaluation requirements.')])

s=old('sections/27-intervention-contracts.tex');a=s.index('The pairwise audit');b=s.index('\\subsection{Nine-item',a)
s=s[:a]+r'''The completed audit covers all $\binom{39}{2}=741$ pairs. The 608 pairs outside the declared mechanism-question cohorts are not comparison failures. The 133 related pairs comprise 66 traffic-envelope, 45 cache-service, 15 local-memory, three behavioral-humanization, three generator-fingerprint and one fixed-instruction pair; they include all 15 same-family pairs. Three findings follow:
\begin{itemize}
\item \textbf{Same paper, different object.} Eight of 15 same-family pairs substitute primitives, targets or cost objects. CachePrune's direct recovery and contextual guessing differ despite sharing a defense configuration; OTRO's measured unpadded latency does not measure its epoch-padded operating point.
\item \textbf{Aligned outcome, unpaired population.} Of the other seven same-family pairs, four have different collection/execution populations and three lack a verified matched-test binding. Dangol's stored-capture ablation and live loopback remain distinct deployment measurements.
\item \textbf{Across records.} Of 133 related pairs, 17 (12.8\%) support a source-qualified descriptive comparison, 105 (78.9\%) have an established object/receiver/target mismatch, and 11 (8.3\%) remain unresolved. Descriptive compatibility permits scoped comparison, not pooled effects or a ranking across heterogeneous costs.
\end{itemize}
The final inventory retains all 528 earlier pair judgments and adds 31 related judgments for the six expansion records, with source locators and reasons. Examples illustrate this census rather than define its sample.

''' +s[b:]
a=s.index('\\soktakeaway{SoK Takeaway 2');s=s[:a]+r'''\paragraph{Join evidence at the record, not the family}
A family-level B means that at least one record supplies an item. It does not imply that its other B cells concern the same intervention. We therefore code all 351 record--item cells and join only B bindings within the same record and configuration (Table~\ref{tab:r19-joint}). Denominators exclude a record if any required item is inapplicable; U, ?, and P remain eligible but unbound. The six contextual controls are separate. CachePrune's direct/context records share one quality/cost package and are deduplicated at configuration level. SparLeak's matched ASR/ROUGE pairs qualify as component utility under R8, correcting its former partial code.
\input{tables/r19-joint-bindings}
\soktakeaway{SoK Takeaway 2 (Join the operating point)}{Inference is bound in 17/20 mitigation families, but the record-local inference--utility--cost join occurs in two records sharing one configuration. Reported cost can belong to another primitive, population or measurement mode. A deployment comparison should request the missing join, not combine a family's best individual cells.}
''';put('sections/27-intervention-contracts.tex',s)

edits('tables/r9-rq-findings.tex',[
('In the original pairwise audit, 6 of 13 same-family pairs','In the final pairwise audit, 8 of 15 same-family pairs'),
('Inference is bound far more often than reuse: matched adaptation 2/11 applicable families, utility at the protected operating point 3/17, cost 11/19.','The inference--utility--cost join holds for 2/20 applicable mitigation records, sharing one configuration. Separate family-level B cells need not form a record-local join.')])
edits('sections/03-methodology.tex',[(r'The final collection has \FinalCore{} core and \FinalAdjacent{} adjacent families.',r'The final collection has \FinalCore{} core and \FinalAdjacent{} adjacent families. The completed search frames, closed on October~21, 2026, combine Semantic Scholar and native arXiv queries with venue-targeted screening of S\&P, USENIX Security, NDSS, CCS and PMLR. C1--C5 screening and version deduplication operate on records before family reconciliation; the supplement retains queries, dispositions and excluded incomplete search frames.')])

s=old('tables/family-audit-matrix.tex');lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('SparLeak'):lines[i]=line.replace(r'\textbf{P}',r'\textbf{B}')
 if line.startswith(r'\midrule Bound'):lines[i]=line.replace('& 17 & 3 & 11', '& 17 & 4 & 11')
put('tables/family-audit-matrix.tex','\n'.join(lines)+'\n')
edits('tables/six-check-audit.tex',[(r'R8. Task or component utility & 2 (3) & 2 (3)',r'R8. Task or component utility & 2 (4) & 2 (2)'),('three source-follow-up corrections','source-follow-up corrections, including SparLeak\'s matched component utility')])
edits('sections/46-r8-sok-audit.tex',[
('SparLeak & ? & ? & P & Local ROUGE proxy is not autonomous workflow utility.',r'SparLeak & ? & ? & B & \S7.5/Table~4 pairs reconstruction ASR and local ROUGE by model/intensity.'),
('3 Bound, 3 Partial, 11 NR-R, 3 NA (3/17 applicable)','4 Bound, 2 Partial, 11 NR-R, 3 NA (4/17 applicable)'),
('2 Bound, 3 Partial, 11 NR-R and 4 NA (2/16)','3 Bound, 2 Partial, 11 NR-R and 4 NA (3/16)'),
('R8 3/3/11/0/3','R8 4/2/11/0/3'),
(r'\path{provenance/r8-review/family-status-overlay.json}; generated from the main-text matrix by \path{provenance/r8-review/build_overlay.py}',r'\path{provenance/r19-evidence-closure/family-status-overlay.json}; the earlier overlay remains archived')])

s=old('sections/31-result-audit.tex');a=s.index('This audit');b=s.index('\\subsection{Nine-item',a)
s=s[:a]+r'''The complete audit covers 39 records from 26 families, with 33 mitigation records from 20 families and six contextual records. Its 741 unordered pairs include 133 related-cohort comparisons and 608 outside the declared cohorts. The 15 same-family pairs are nested within the 133.
\begin{table}[t]\centering\footnotesize
\caption{Complete record-pair descriptive comparability.}\label{tab:pair-descriptive}
\begin{tabularx}{\columnwidth}{@{}Yrrr@{}}\toprule
Subset & Compatible & Incompatible & Unresolved\\\midrule
Same family ($n=15$) &7 (46.7\%)&8 (53.3\%)&0\\
Related cohort ($n=133$) &17 (12.8\%)&105 (78.9\%)&11 (8.3\%)\\\bottomrule
\end{tabularx}\end{table}
Eight same-family pairs change the primitive, target or cost object. Of seven aligned-outcome pairs, four change the collection/execution population and three lack a verified paired-test binding. The artifact preserves the original 528 judgments and identifies all 31 added related-pair judgments. Cohort membership, source locators and individual reasons are explicit; outside-cohort pairs are excluded rather than treated as adverse evidence. Section~\ref{app:record-joins} reports all 351 record-local audit cells and positive joint-binding identities.

''' +s[b:]
s+=r'''
SparLeak's \S7.5/Table~4 pairs reconstruction success and ROUGE at the same model and perturbation intensity \cite{chen2026sparleak}. R8 accepts component as well as task utility, so the current overlay corrects its partial code to B. Its reported spy overhead is attack cost and is not promoted to defense cost. The R8 distribution becomes 4 B, 2 P, 11 U and 3 inapplicable; historical records remain unchanged.
''';put('sections/31-result-audit.tex',s)

s=old('sections/37-transfer-tests.tex');a=s.index('A post hoc transfer study');b=s.index('\\input{tables/r14-calibration-transfer}',a)
s=s[:a]+r'''A post hoc study refits each target model's attackers on its own training customers and swaps only defense calibration. Table~\ref{tab:calibration-transfer} reports BA, paired changes from local calibration, and both byte and call costs. On GLM, MiniMax calibration changes cancellation by $+20.8$ points (95\% interval $[-12.6,35.3]$) and return by $-17.3$ ($[-38.2,-5.3]$). The resolved return reduction and uncertain cancellation direction motivate a target-specific transfer assessment; the imported template also increases bytes. Source-trained attackers reach undefended return BA of 77.5\% for MiniMax-to-GLM and 88.1\% in reverse. These two-endpoint results use known customer partitions.
''' +s[b:]
s=s.replace('The calibration is itself part of the defense: moved to another model, it redistributes protection between targets, so a calibrated result transfers only with its calibration population.','Calibration is a measurable deployment choice: its transfer changes target-specific BA and overhead, and uncertainty determines which directions are resolved. The decision table requires re-evaluating both targets at the new operating point.')
put('sections/37-transfer-tests.tex',s)

edits('sections/10-open-challenges.tex',[(r'\subsection{Deployment paths and reporting obligations}\label{sec:deployment}',r'''\subsection{Deployment paths and reporting obligations}\label{sec:deployment}
Table~\ref{tab:r19-decisions} makes the synthesis operational. A result supports reuse at its measured boundary; a changed boundary specifies the smallest additional comparison required. The rows are measurement obligations rather than universal security thresholds.
\input{tables/r19-deployment-decisions}''')])
put('tables/r19-deployment-decisions.tex',r'''\begin{table*}[t]\centering\footnotesize
\caption{Deployment change $\rightarrow$ missing binding $\rightarrow$ minimum decision evidence. Each row names a measurable gate for carrying a result forward.}\label{tab:r19-decisions}
\begin{tabularx}{\textwidth}{@{}p{.17\textwidth}p{.29\textwidth}Y@{}}\toprule
Changed boundary & What the old result leaves open & Minimum comparison before reuse\\\midrule
Emitter / representation & Buffered or upstream cost and inference do not price a re-emitting/streaming endpoint. & Capture the final receiver; fit its attacker; report overflow, bytes and first-output/completion delay (Exp~1).\\
Read cover $\rightarrow$ writes & Discarding a reply does not undo commits, refunds or authorization effects. & Compare live database/authorization outcomes; execute cover on the chosen isolation path; include its calls and quotas (Exp~2).\\
Customer / model calibration & A template's target-wise inference and overhead can change with the receiving trajectory distribution. & Hold out customers; refit the target attacker; report both target changes with paired intervals and byte/call ratios (Table~\ref{tab:calibration-transfer}).\\
Attacker observation & Chance-level length inference does not bind timing or flush identification. & Re-evaluate the same captures under a common expanded suite; pair the suite-max change (Exp~4: cancellation $+11.4$ points, interval $[3.7,19.6]$).\\
Loopback $\rightarrow$ WAN & A fixed tunnel horizon does not guarantee completion under network delay. & Measure completion/overflow under the target path; retune the horizon on training conditions and reprice protection (Exp~4).\\
Replay $\rightarrow$ live planner & Preserved logical responses do not measure timeout/replanning utility. & Run fresh paired planner episodes with the actual scheduler, delays and deadlines; measure success and latency. Prefix-cover utility is measured here; full framing/flush needs its own run.\\\bottomrule
\end{tabularx}\end{table*}
''')
put('sections/12-conclusion.tex',r'''\section{Conclusion}\label{sec:conclusion}
Transfer boundaries organize defense evidence into deployment decisions. The complete 39-record audit exposes eight within-family object substitutions and separates joint operating-point evidence from independent family-level bindings. The experiments put resource and uncertainty measurements on the resulting decisions: choose the receiving emitter, verify write isolation, evaluate calibration per target, and strengthen the observation model on shared captures. Calibration transfer yields a resolved return reduction alongside an uncertain cancellation change and higher byte cost, rather than a scalar model ranking. The decision table specifies the minimum re-evaluation for each changed boundary, making source-bound systematization actionable.
''')

put('sections/58-record-joint-audit.tex',r'''\section{Complete Record-Local Audit and Joint Bindings}\label{app:record-joins}
This retrospective reanalysis applies R1--R9 to each of the 39 archived result records, yielding 351 cells. It retains the original source locators and hashes; source follow-up resolves the SparLeak utility correction and distinguishes CachePrune's shared default configuration and OTRO's padded/unpadded costs. These judgments are source-bound reassessments, not additional independent annotator measurements.

\paragraph{Counting rule}
For a requested join, a mitigation record is applicable if none of the required items is inapplicable. A join is bound only if every required item is B and the evidence describes the same intervention/workload configuration. U (unreported), ? (unverified) and P (partial) are not bound; they remain distinct in the cell table. The six contextual controls are excluded from all mitigation join denominators. No family-level union of cells is used. Configuration-linked evidence need not use identical sampled requests and does not license a paired effect.

\paragraph{Positive joins and deduplication}
Inference plus utility: AHB online execution, CachePrune direct recovery, CachePrune contextual recovery and SparLeak replacement (4/22 records, three families/configurations). Inference plus cost: speculative REST padding, Dangol capture, Dangol live binding, and the two CachePrune records (5/22, three families, four configurations). Matched protected fitting/adaptation plus inference: UI offline and Dangol capture (2/17). Inference--utility--cost: the two CachePrune records share one default configuration's quality/cost package (2/20, one family/configuration). All five items together: 0/14. These scope-sensitive denominators identify missing bindings rather than measure defense failures.

\paragraph{Cost-object discipline}
The speculative REST record binds token-payload overhead, not verified live wire bytes; Dangol capture binds transformed capture cost, while its live record binds loopback wire/latency. CachePrune's secure default setting links recovery with generation quality and serving cost; its privacy-disabled cache-hit comparison is not borrowed. SparLeak's attack overhead is not a defense-cost observation. OTRO's unpadded TTFT does not price its separately derived epoch padding. These distinctions explain why cost cannot be copied by family name.

\begingroup\footnotesize\setlength{\tabcolsep}{3pt}
\input{tables/r19-record-audit}
\endgroup
''')
edits('supplement.tex',[(r'\clearpage\input{sections/56-holdout-matrix}',r'\clearpage\input{sections/56-holdout-matrix}'+'\n'+r'\clearpage\input{sections/58-record-joint-audit}')])
print('R19_MANUSCRIPT_UPDATED')
