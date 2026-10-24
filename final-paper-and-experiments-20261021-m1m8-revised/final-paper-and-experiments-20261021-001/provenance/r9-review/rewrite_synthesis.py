"""Consolidate scope statements and remove supplementary dependencies from the main argument."""
from pathlib import Path
O=Path(__file__).resolve().parent;M=O.parents[1]/'manuscript'
def put(rel,s): (M/rel).write_text(s.strip()+'\n',encoding='utf8',newline='\n')
def edit(rel,a,b):
 p=M/rel;s=p.read_text(encoding='utf8');assert a in s,(rel,a[:80]);p.write_text(s.replace(a,b),encoding='utf8',newline='\n')
p=M/'main.tex';s=p.read_text();a=s.index('\\begin{abstract}');b=s.index('\\end{abstract}',a)
s=s[:a]+r"""\begin{abstract}
Encryption conceals content while exposing the structure of agent workflows. We systematize 82 study families through 39 source-bound result records, linking each defense outcome to its observer, execution boundary and evaluation conditions. This record-level view reveals three consequential transfer errors: attributing upstream protection to a plaintext-aware downstream emitter, treating discarded read cover as safe state-changing cover, and pricing one mechanism with another's utility or cost. The complete 58-core-family map and 20-family audit make these distinctions inspectable. Four experimental demonstrations connect the synthesis to deployment choices. Streaming reverses a buffered cost comparison; isolated and live cover have different state effects; real-agent traces separate behavioral compliance from operation privacy; and timing-aware comparisons expose when inexpensive transport shaping competes with costly shadow execution. The resulting contribution is a reusable evidence base and an operational method for selecting, comparing and validating defenses at the boundary where their protection is needed.
"""+s[b:];p.write_text(s,encoding='utf8',newline='\n')
put('sections/01-introduction.tex',r"""
\section{Introduction}\label{sec:introduction}
Encryption conceals message content, yet LLM engines and agents expose packet sizes, cache timing, visited domains and tool sequences \cite{weiss2024prompt,promptpeek2025,earlybird2025,agentprint2025,uitraces2026,jeong2026wra}. A defense result applies to a particular receiver, execution boundary and workload. Reusing a headline score across a frontend, dispatcher or tool provider can change both its protected signal and its cost object.

Our SoK uses the \emph{evaluated result record} to make these transfers inspectable. Separating Dangol's stored-capture and live-protocol results prevents subtracting unmatched scores; separating Early Bird's KV-prefix and semantic-cache mechanisms prevents pricing one with the other's overhead. Combining signal origin with observer access and threat polarity explains why read-only privacy cover and state-changing bot evasion have different utility consequences. These findings emerge from binding evidence across records that a paper-level summary combines.

\paragraph{Contributions}
\begin{itemize}
\item \textbf{A populated evidence framework.} A complete map of \FinalCore{} core and \FinalAdjacent{} adjacent families, 39 source-bound records and a nine-item audit of 20 mitigation families. Explicit rules identify compatible, incompatible and unresolved comparisons.
\item \textbf{Three concrete transfer failures.} Frontend re-emission defeats an upstream-only protection claim; discarded retrieval cover does not justify live action cover; stored/live measurements and component costs cannot be interchanged. Source locators identify both the failed transfers and positive examples binding the required evidence.
\item \textbf{Four demonstrations that change deployment choices.} Streaming/state tests and repeated agent trajectories from 53 customers expose adaptation rebounds, state side effects and timing leakage. Matched comparisons identify cases where inexpensive transport shaping competes with costly shadow execution, while the same audit separates measured logical conformance from end-to-end planner utility.
\end{itemize}
The synthesis connects established mechanisms---decoys, isolated execution, constant-rate tunnels and framing---to concrete evidence requirements for agent systems. Its distinctive output is a source-linked account of which transfers work, which fail, and which experiment resolves the difference (Table~\ref{tab:rq-findings}).
\input{tables/r9-rq-findings}

\soktakeaway{Scope of claims}{We contribute record-level systematization and controlled demonstrations of evidence transfer. The real-agent target is a requested operation category; the known retail cohort contains 53 customers. Measurements establish fitted-suite inference, logical state conformance and scoped resource costs. Deployment-wide security and live defended-planner utility require the additional validation specified in \S\ref{sec:validity}.}

Figure~\ref{fig:system-model} places trace and action paths on the same agent--tool chain. This joint view makes the receiving representation and the execution boundary explicit before selecting a defense.
\begin{figure*}[t]
\centering\input{figures/fig1-system-model}
\caption{Observation and execution boundaries. The four demonstrations test emitter placement, stateful execution/link composition, real-agent operation signatures, and timing with matched transport controls.}
\label{fig:system-model}
\end{figure*}
""")
# Methodology: positive method description; full caveats consolidated in 9.3.
p=M/'sections/03-methodology.tex';s=p.read_text()
a=s.index('The Boolean queries overlap');b=s.index('\\subsection{Coding procedure',a)
s=s[:a]+r"""The Boolean queries recover 25/60 previously indexed families (41.7\% seed-set coverage); proceedings and citation routes supply complementary families. The assembled corpus and source versions define the scope of the synthesis. Appendix~\ref{app:records} provides the complete result-level index.

"""+s[b:]
a=s.index('These version-bound locators');b=s.index('\\soktakeaway',a)
s=s[:a]+r"""Every record carries a publicly inspectable source locator, enabling readers to check the exact result behind a comparison. The archive retains the initial extraction and author-adjudicated columns, disagreements and subsequent source corrections. Appendix~\ref{app:equivalence} describes this audit trail.

"""+s[b:];p.write_text(s,encoding='utf8',newline='\n')
p=M/'sections/04-scope.tex';s=p.read_text()
s=s.replace(r'Attacker training/calibration ($D_0$ vs.\ $D_2$)',r'Attacker training/calibration ($D_0$: clean-condition fit; $D_2$: protected-condition fit)')
s=s.replace('Across 77 cited entries, the bibliography labels 49 arXiv-only, 21 venue-labelled (5 also cite a preprint), 1 book, 2 standards and 4 vendor documents; these are citation forms, not peer-review certifications (Supplement S18).\n','')
s=s.replace(r'unreported (\NRR{}), unavailable (\NRA{}) or unverified (\NRV{})',r'unreported (U), unavailable (A) or unverified (?)')
a=s.index('\\paragraph{Rule-application consistency check}')
s=s[:a]+r"""\paragraph{Executable comparison rules}
The record schema and comparison contracts precede the audit results. Table~\ref{tab:audit-rules} gives all nine operational rules and a shared evidence-status alphabet; Table~\ref{tab:family-audit} applies them to every mitigation family. Twenty-four constructed cases and seven mechanism checks exercise rule application in the artifact, while the source-linked cases in \S\ref{sec:discussion} explain the substantive comparison judgments.
""";p.write_text(s,encoding='utf8',newline='\n')
p=M/'sections/28-fingerprint-dependencies.tex';s=p.read_text()
s=s.replace(' Supplement S2 maps each dependency to its supporting holdout.','')
s=s.replace('This is not proof of an invalid original split; it bounds portability.','This bounds portability to the tested configuration.')
s=s.replace(r'The supplementary archive example fixes labels and units and finds a 0.3447-nat sequence increment under archive-receiver ordering. Its small common-task control leaves task-distribution explanations unresolved (Supplement S4).',r'A representation comparison therefore holds target labels and evaluation units fixed while changing the observed features.')
s=s.replace('We neither rewrite its headline score nor quantify optimism.','This supports an adjacent attribution comparison under its reported inputs.')
s=s.replace('These are record-grounded boundary findings, not new theorems.','Together they identify which evidence must travel with a reuse claim.')
p.write_text(s,encoding='utf8',newline='\n')
p=M/'sections/11-discussion.tex';s=p.read_text().replace('E6 tests this distinction with actual simulator mutations.',r'Exp~2 (\S\ref{sec:exp-state}) tests this distinction with simulator mutations.').replace('E5/E6 supply direct contrasts where $D_0$ reaches chance and $D_2$ recovers the signal; E14 expands the attacker families.',r'Exps~1--2 supply direct contrasts where $D_0$ reaches chance and $D_2$ recovers the signal; Exp~4 expands the attacker families.').replace('(E6)',r'(Exp~2)')
p.write_text(s,encoding='utf8',newline='\n')
# Preserve deployment/ethics, rewrite a single validity section with the material limitations.
p=M/'sections/10-open-challenges.tex';s=p.read_text()
s=s.replace('These are access assumptions, not a measured prevalence estimate.','Each position defines a specific observable projection.')
s=s.replace('The single-ingress experiments establish no multi-endpoint anonymity.','Our measurements use a single ingress endpoint.')
s=s.replace('Only this local gateway design is measured; the provider-specific paths are feasibility examples, not backend validations.','Our local measurements implement the gateway path; the provider-specific paths identify deployments for follow-up measurement.')
s=s.replace('Thus our results do not justify application-layer dummy execution for every passive-link deployment.','The choice therefore follows the required observation boundary.')
s=s.replace('This supports a large, source-linked comparison; it supplies no independent human judgments.','Authors retain responsibility for the source-linked comparison and its interpretation.')
a=s.index('\\subsection{Threats to validity')
s=s[:a]+r"""\subsection{Threats to validity and scope of evidence}\label{sec:validity}
\paragraph{Source synthesis}
The purposive corpus supports comparisons within the assembled evidence base; seed-set query coverage is not field-wide recall. Of 77 cited entries, 49 are arXiv-only, 21 venue-labelled (five also cite preprints), and seven are books, standards or vendor documents. These labels identify source form. Initial AI extraction and author adjudication are dependent stages, so their archived agreement measures process consistency rather than independent human reliability. Constructed cases similarly check rule execution. Source locators and applicability-sensitive denominators support direct scrutiny; independent blind-recoding templates are available for extension.

\paragraph{Statistical scope}
The original BA/AUROC screen is an author-chosen engineering threshold, not a security definition. No reported joint design confirms that two-target absolute criterion; the measured paired reductions establish improvements against specified fitted suites. Confidence intervals reselect the suite maximum but condition on fitted predictions and omit retraining uncertainty. The frozen split has only 5/7 positive customers and the full cohort 14/18; repeats add execution coverage, not independent customers. Reference-program calibration uses the known population. Real-agent calibration is frozen before held-out collection, while development had access to the full task set; the cross-fit, timing follow-ups and sensitivity analyses are exploratory known-cohort evidence.

\paragraph{Targets and deployment utility}
The operation-category targets are coupled to intended actions. Their localization establishes operation signatures, not latent customer-attribute recovery. A small same-operation product diagnostic is inconclusive (Appendix~\ref{app:experiments}). Our utility audit distinguishes measured original agent reward, checked defended logical state/response conformance, and unmeasured live defended-planner utility. Local RPC timing excludes LLM generation, WAN transit and timing-dependent replanning. WF adapters support matched metadata comparisons; original-protocol equivalence and equal-utility deployment comparisons require further measurements.

\paragraph{External validity}
Sol and Luna are mutable aliases from one provider in one retail environment, each also used in a separate user-simulator context. The additional Luna study has 29 training episodes per prompt. Fresh independent customers, fixed open weights, cross-vendor and cross-environment tests, provider-backend measurements and live replanning are the next validation axes. The present synthesis supplies the source bindings and comparison obligations needed to design those tests.
""";p.write_text(s,encoding='utf8',newline='\n')
put('sections/12-conclusion.tex',r"""
\section{Conclusion}\label{sec:conclusion}
This SoK makes the evaluated result record the unit of defense comparison. Its 82-family map, 39 source-bound records and nine-item audit expose transfers hidden by paper-level grouping: protection lost at a new emitter, read cover moved across a state-changing boundary, and utility or cost borrowed from another mechanism. Four demonstrations show why those distinctions change deployment choices. They separate compliance from operation privacy, expose scheduling leakage, and identify inexpensive transport alternatives to costly shadow execution on a common workload. The practical contribution is an inspectable path from published evidence to a justified comparison: identify the receiver, preserve the intended state, and bind inference, utility and cost to the same operating point.
""")
put('sections/30-reproducibility-guide.tex',r"""
\section{Audit Trail and Logical Equivalence}\label{app:equivalence}
\paragraph{Evidence organization}
The package separates the 82-family source map, 39-result ledger, 180-cell audit, transport tests, dispatch tests and real-agent studies. Each source record has a version and section/table/figure/paragraph locator. Authors reviewed all family labels and verified the result records and audit cells as described in \S2.3. Initial AI-assisted extraction and subsequent author adjudication remain distinct archived columns; the supplementary process statistics and blind-recoding templates support follow-up audit. The supplement supplies detailed algorithms, full result grids and archived coding decisions; the main paper contains the comparison rules, complete family matrix and record index needed to follow the synthesis.

\paragraph{Logical equivalence}
For deterministic tools, a real action gives $(s_{t+1},o_t)=T(s_t,a_t)$. The defended dispatcher forwards that action unchanged, runs cover on a disjoint state $s_t^{\rm sh}$ and suppresses cover responses. With equal initial states and realized real actions, induction gives
\[
s_t^D=s_t,\qquad \pi_{\rm plan}(D(H_t))=H_t.
\]
Here $H_t$ is the logical message/action/response history, excluding wall-clock time. Payload-preserving framing and terminal shadow flush maintain the invariant, provided timeouts, shared-state side effects and timing-dependent tool behavior are absent. Checks compare every real-call projection and scoring field across all 690 trajectories and four program conditions. These establish implementation conformance to isolation. The utility boundary in \S\ref{sec:validity} explains the further live-planner measurements.

The reproducibility index resolves each archived experiment in Appendix~\ref{app:experiments} to protocol, inputs, predictions and checksums. Saved-output verification reproduces the reported metrics without new model calls, while measured captures and analytic reconstructions retain their separate provenance.
""")
put('sections/51-r9-extensions.tex',r"""
\paragraph{Extensions and sensitivity}
The same-provider Luna extension contains 150 formal runs on 75 existing retail tasks, two prompts and one repeat. Standard-prompt write-only dispatch BA is 87.5/66.6\%, versus 50.0/57.0\% for get/find/list reads; rewards are 32/75 and 33/75, with seven protocol-error episodes retained. This tests the operation diagnostic under another model alias.

A customer-composition check on fixed cross-fit predictions changes standard-prompt joint-constant BA from 60.5/55.5\% to 59.0/53.2\% under equal-customer-within-class weighting. Rules-arm return changes from 59.4\% to 60.4\%. Across 192 leave-one-positive-customer checks, standard-prompt cancellation ranges 57.3--62.0\%; these are influence ranges, not confidence intervals.

The same-operation attribute check fixes single-item returns and a pre-fit digital-device grouping. Per prompt, 20 customer--order--item instances from 15 customers use the original customer folds and fixed LR/RF/GB learners. Maximum OOF BA is 30.3\% [16.7,52.7], versus 50\% for a constant predictor; a single fixed shuffled target gives 65.2\%. Both prompts have identical features. Below-chance predictions can reflect reversed associations, and one shuffle is not a permutation distribution. This diagnostic is inconclusive for non-action attributes; its full predictions remain in the supplement.
""")
# Positive research-question guide.
s=(M/'tables/r8-rq-findings.tex').read_text().replace('These record-level distinctions correct cross-paper transfers, not a new theorem.','These distinctions identify the evidence required to reuse a result.').replace('E5--E7','Exps~1--2').replace('E9--E14','Exps~3--4').replace('Full utility under timing-dependent replanning remains unestablished.','The same audit locates the utility boundary of our demonstrations.')
put('tables/r9-rq-findings.tex',s)
# Current table captions: no historical experiment IDs in the main argument.
for rel in ['tables/transfer-streaming.tex','tables/r7-e6-main.tex']:
 p=M/rel;s=p.read_text().replace('E5','Exp 1').replace('E6','Exp 2').replace('S12','the archived full policy grid')
 p.write_text(s,encoding='utf8',newline='\n')
print('SYNTHESIS_CONSOLIDATED')
