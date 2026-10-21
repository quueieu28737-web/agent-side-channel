"""Apply source-level manuscript corrections; measurements are generated separately."""
from pathlib import Path
import re,json,csv
P=Path(__file__).resolve().parent/'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001'
M=P/'manuscript'
def write(f,s):(M/f).write_text(s.strip()+'\n',encoding='utf-8')
def edit(f,a,b):
    p=M/f;s=p.read_text(encoding='utf-8')
    if a not in s: print('NOT FOUND',f,a[:70]);return
    p.write_text(s.replace(a,b),encoding='utf-8')

s=(M/'main.tex').read_text()
s=re.sub(r'\\title\{.*?\}\n\\author',lambda m:r'''\title{SoK: Evidence Boundaries of LLM and Agent Side-Channel Defenses\\A Result-Record Audit and Two Controlled Case Studies}
\author''',s,flags=re.S)
abstract=r'''\begin{abstract}
Published side-channel defenses protect specific observations and execution environments. Reusing these results in LLM-based workflows requires identifying which guarantees survive changes in receivers, tool state and attacker adaptation. We systematize \FinalN{} study families (\FinalCore{} core and \FinalAdjacent{} adjacent), including 39 intervention result records from 20 mitigation families. A nine-item reporting audit and three deployment checks bind each result to its target, observer, execution boundary, workload and measured cost. The audit distinguishes established incompatibility from missing or unverified evidence; only 3 of 17 applicable families bind task or component utility, and 2 of 11 bind a matched adaptation contrast. Two controlled case studies illustrate the resulting evaluation obligations. Replays of 48 saved responses over two TLS~1.2 links reproduce downstream re-emission after upstream length padding. With matched workload denominators, 512-byte buckets cost 2.30$\times$ and 1.43$\times$ for two sentence-prefix workloads; a cap fitted to training lengths reaches 50\% test accuracy at 2.18$\times$ for the verbosity target. Replaying 115 retail reference programs shows that same-item writes can change workflow state, and that preserving task objects differs from preserving an account or a shared database. Simple count or position rules recover cancellation labels despite cover calls. These are local mechanism tests, not a combined autonomous-agent evaluation. The contribution is a reusable evidence audit that identifies which comparisons are supported and which require new measurements.
\end{abstract}'''
s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:abstract,s,flags=re.S)
s=s.replace(r'\IEEEtriggeratref{87}','')
(M/'main.tex').write_text(s,encoding='utf-8')
write('sections/01-introduction.tex',r'''
\section{Introduction}\label{sec:introduction}
Encryption conceals message content, yet LLM serving engines and agent systems expose packet sizes, cache timing, memory-access patterns, visited domains and tool-invocation sequences \cite{weiss2024prompt,promptpeek2025,earlybird2025,agentprint2025,uitraces2026,jeong2026wra}. A published defense result applies to a particular observer and operating point. Reusing it across a frontend, a tool dispatcher or another workload can change both the observable signal and the cost being measured. We study this interpretation problem without assuming that the original authors claimed end-to-end protection.

Our systematization asks which evidence permits such reuse. It separates three obligations:
\begin{enumerate}
\item \textbf{Bind the receiving projection.} Target-oblivious postprocessing is a sufficient condition for preserving an upstream information bound (Proposition~1). A frontend with access to decoded content or an unprotected backward computation requires a separate argument or measurement \cite{netecho2025,politis2026splitdecoy}.
\item \textbf{Bind execution and protected state.} Read-only decoy requests and GUI actions operate on different interfaces and serve different objectives \cite{jeong2026wra,zhu2026turing}. For tools, unchanged argument values do not imply unchanged database state. The relevant contract must identify task objects, the user's account and shared state separately.
\item \textbf{Bind adaptation, utility and cost.} An attack on defended data must specify how the attacker was fitted; an overhead must identify the same workload and deployed mechanism as the claimed protection. Missing bindings limit reuse without establishing that the original study omitted or failed the experiment.
\end{enumerate}

\paragraph{Contribution and scope}
The end-to-end principle, state isolation and adaptive evaluation are established ideas. Our contribution is their application to a source-bound repository of heterogeneous LLM and agent measurements. We provide:
\begin{itemize}
\item \textbf{A result-record repository:} \FinalN{} study families (\FinalCore{} core and \FinalAdjacent{} adjacent), with 39 intervention records and 78 utility/cost field positions from the 20 mitigation families. Records separate source versions, receiver views, execution modes and cost objects that a paper-level score can conflate.
\item \textbf{A comparability audit:} nine reporting items, numbered R1--R9, and three operational checks. Among applicable families, utility is bound in 3/17 and a matched adaptation contrast in 2/11. The latter includes a capture-based result and does not establish live-protocol adaptation. A 24-scenario author-constructed exercise illustrates rule application; it is not an external validation benchmark.
\item \textbf{Two controlled case studies:} a TLS~1.2 replay of saved responses and a separate replay of 115 retail reference programs. They test receiving boundaries, state scopes and attacker-view choices. They neither execute an autonomous LLM agent nor measure the joint protection of the two paths.
\end{itemize}

Table~\ref{tab:synthesis-decisions} links source-local findings to the new comparison judgments. For example, separating Dangol's stored-capture and live-protocol records prevents an invalid subtraction; separating Early Bird's two mechanisms prevents using a semantic-cache cost to price KV-prefix isolation. The retail study adds a concrete evaluation consequence: full account equality and a simple rule attack can reverse an apparent privacy--utility interpretation.

Figure~\ref{fig:system-model} depicts the two paths as an analysis model, not a jointly tested system. Figure~\ref{fig:defense-decision} summarizes the checks.
\begin{figure*}[t]
\centering\input{figures/fig1-system-model}
\caption{Observation and execution boundaries represented by a result record. The case studies test these paths separately.}
\label{fig:system-model}
\end{figure*}
\begin{figure*}[t]
\centering\input{figures/defense-decision-procedure}
\caption{Three checks for deciding which evidence can be reused in a target deployment.}
\label{fig:defense-decision}
\end{figure*}
''')

# Retain the original schema/contract exposition, replace the invalid validation claims.
s=(M/'sections/04-scope.tex').read_text()
s=s[:s.index(r'\paragraph{Validity evaluation:')]+r'''
\paragraph{Illustration rather than external validation}
We retain a 24-scenario exercise constructed by the authors from the same corpus used to develop the checks: seven Compatible, twelve Incompatible and five Unresolved cases. The Incompatible category includes proposed transfers with established record mismatches; these are not twelve independently observed deployment failures. The supplied annotation file agrees with the author labels on 23/24 and 22/24 cases for its two coder columns. Agreement between these columns is 21/24 ($\kappa=0.795$). These descriptive results do not establish framework accuracy on unseen deployments, independent ground truth or superiority over other reading procedures.

The original headline rule predicts Compatible for every case. Its 7/24 accuracy is a class-count consequence. Always predicting Incompatible instead gives 12/24, 100\% recall for that category and 0\% recognition of compatible cases. Table~\ref{tab:m1-validity} reports all outcomes rather than a headline accuracy advantage. A fair comparison would supply the same source information to competing procedures and use independently constructed held-out scenarios; that experiment has not been performed.

\input{tables/scenario-confusions}

The retained synthetic indexing comparison (Supplement S7) likewise does not establish effectiveness of the three checks. Its 512 roots each contain three query judgments; thus 695 and 476 decision-correct/count-incorrect judgments are out of 1,536 queries per arm. The joint endpoint favors the structured checklist over raw \scope{} traversal. We use \scope{} only as a schema for locating evidence.
'''
write('sections/04-scope.tex',s)

edit('sections/03-methodology.tex',r'A central methodological contribution of our repository is separating four mutually incompatible \emph{threat polarities} that prior surveys conflate under generic ``attack/defense\'\' labels:',r'We use four narrative groupings for objectives and observer roles. They are not mutually exclusive classes: an unauthorized identity inference can be both attribution and a confidentiality concern. Each record separately specifies the inference target, observer, authorization relation and protected interest:')
# Exact straightforward replacement independent of quote escaping above.
p=M/'sections/03-methodology.tex';s=p.read_text();s=re.sub(r'A central methodological contribution.*?labels:',r'We use four narrative groupings of objectives and observer roles, not mutually exclusive classes. An unauthorized identity inference can be both attribution and a confidentiality concern. Each record separately specifies the inference target, observer, authorization relation and protected interest:',s)
s=s.replace('The 204-record exclusion audit rerouted', 'The exclusion audit selected 177 high-risk pattern matches plus 27 reason-stratified records (seed 20261021), rather than all 396 initially excluded records. This enriched 204-record subset rerouted')
s=s.replace('historical October 8 native IEEE/ACM exports','historical October 8--9 native IEEE/ACM exports')
s=s.replace('38/40 forward seeds resolved)', '38/40 forward seeds resolved; seed resolution and the number of distinct returned works are different counts)')
s=s.replace(r'\subsection{Independent human dual-coding and reliability}',r'\subsection{Supplied coding records and agreement}')
start=s.index('To ensure that eligibility routing');end=s.index(r'\begin{enumerate}',start)
s=s[:start]+r'''The supplied package records a primary AI-assisted coding workflow and a second coding column described by its provenance as a domain-expert review. We recompute agreement from those saved columns. The files alone do not verify coder identity, blinding or independence from the primary decisions; we therefore report annotation agreement rather than newly verified independent human validation. The recorded scope is:
'''+s[end:]
s=s.replace('Independent three-class','Three-class').replace('Independent five-state','Five-state').replace('Independent coding','Recorded coding')
s=s[:s.index(r'\soktakeaway{SoK Takeaway 1')]+r'''
The historical confidence intervals resample individual screening records, audit cells and pairwise judgments respectively. Cells within families and three judgments within a pair are dependent, so these intervals are conditional descriptive summaries, not cluster-robust generalization intervals. The 36 cells for four added families are outside the 144-cell agreement calculation. Agreement also does not establish coding correctness, and $\kappa$ depends on category prevalence.

\soktakeaway{SoK Takeaway 1 (Search and evidence scope)}{The supplementary queries returned 25/60 snapshot families and 17/24 known seed papers. These overlaps motivate complementary discovery methods; they neither estimate field-wide recall nor identify why each missing paper was absent. Objective, observer and authorization must be specified separately when comparing interventions.}
'''
write('sections/03-methodology.tex',s)

edit('sections/27-intervention-contracts.tex','Focusing on the', 'The 13 within-family pairs are included in the 102 within-cohort pairs: $528=426+102$, with no additional subtraction of 13. Focusing on the')
edit('sections/27-intervention-contracts.tex',r'(dual-coded at 94.0\% agreement, $\kappa=0.916$)',r'(the supplied 50-pair subsample, not all 102 pairs, has 94.0\% agreement across its 150 judgments, $\kappa=0.916$)')
s=(M/'sections/27-intervention-contracts.tex').read_text();start=s.index('To avoid conflating component studies')
s=s[:start]+r'''Table~\ref{tab:six-check-audit} reports nine audit items R1--R9, separate from deployment Checks~1--3. They are requirements for the particular reuse claims considered here, not universal obligations that every component paper must satisfy. R4 records protected-condition fitting; R5 records a matched clean-versus-adapted contrast on defended tests. R7--R9 record inference, utility and cost. A family-level Bound entry means at least one scoped result meets the item, not that every result in that family does.
\input{tables/six-check-audit}

For Dangol, R5 is Bound for in-fold stored-capture experiments; the live-refit paired comparison in Table~\ref{tab:result-lineage} remains \NRV{}. These are different records, so we retain the family count of two and explicitly restrict its meaning.

\soktakeaway{SoK Takeaway 2 (Joint evaluation gap)}{Across 20 mitigation families, 17 bind inference outcomes, 11 bind cost, 3 bind utility and 2 bind a matched adaptation contrast. Excluding structurally inapplicable entries, the latter three rates are 11/19, 3/17 and 2/11. \NRV{} means unverified binding, not an absent experiment. CachePrune binds inference, utility and cost at one operating point; this is not a claim that it also binds adaptive evaluation.}
'''
write('sections/27-intervention-contracts.tex',s)

write('sections/32-controlled-placement.tex',r'''
\section{Two Controlled Case Studies}\label{sec:controlled-placement}
The two studies test distinct observers. The transport observer sees TLS application-record lengths on a selected link. The tool-dispatch observer sees ordered tool names, write counts and response byte lengths, including failed calls; it is an instrumented dispatch view, not an encrypted-network observer. Neither experiment combines these views or runs an autonomous agent. Saved outputs and reference programs let us vary the specific boundary while holding the prescribed workload fixed.

\subsection{Transport placement and workload-matched framing}
For 24 public topics, the saved corpus contains one prompted brief and one prompted expanded \texttt{gpt-6-luna} response (48 outputs; 12 training and 12 disjoint test topics). These are designed prompt conditions, not a sample of natural task lengths. The original placement experiment passes text through two TLS~1.2 connections: the frontend decodes and removes upstream framing before sending new terminal chunks. Exact plaintext hashes are checked. Equalizing the upstream length projection leaves the unpadded terminal projection separable (100\% verbosity classification); padding both projections reduces the evaluated classifier to 50\%. This reproduces the receiving-boundary mechanism identified by NetEcho rather than discovering a new failure mode.

The revised framing replay uses \texttt{ECDHE-RSA-AES128-GCM-SHA256} sockets and parses application-data records. T1 contrasts brief versus full expanded responses. T2 contrasts the brief with the first two period-delimited sentences of the expanded response. T3 contrasts the first two versus first three sentences of the same expanded response. Thus T2/T3 are derived prefixes, with two examples per topic, not independently generated explanations. T4 relabels both brief and expanded responses by topic domain; it has 24 test outputs from 12 topics, not 12 expanded outputs. Its unpadded accuracy is 45.8\% (95\% topic-bootstrap interval 25.0--66.7\%); its test majority-class baseline is 58.3\%. T4 is a weak-signal control, not a defense success.

\input{tables/controlled-placement}

Every cost ratio divides defended application-record bytes by unpadded application-record bytes for the \emph{same texts}, over all 48 examples in that workload. The count includes TLS record headers and encryption overhead; handshakes, TCP/IP, upstream bytes and latency are excluded. The 4-byte length prefix is included. Buckets of 256/512 bytes use 128-byte writes; 1024-byte buckets use 256-byte writes. Consequently the 1024-byte single-quantum wire size is 1,140 bytes, not 1,082. The workload-matched 512-byte ratios for T2/T3 are 2.30$\times$/1.43$\times$; dividing both by T1's 720.96-byte denominator would yield the invalid earlier ratios below one.

A tighter comparison selects a constant application-frame cap using \emph{training lengths only}: round the largest framed training response (1,194 bytes) up to a multiple of 128, yielding 1,280 bytes. Ten 128-byte records cost 1,570 wire bytes (2.18$\times$ T1). Longer messages would emit additional 128-byte records without truncation; no test message overflows. This produces identical length sequences on the saved T1 test set and 50\% accuracy for the evaluated classifiers. It is a feasible cap for these data, not a globally optimal padding protocol or a guarantee for future lengths. The retained 16,848-byte cap (23.37$\times$) is only a deliberately loose control.

\subsection{Matched attacker adaptation}
We use $D_0$ for an attacker fitted on unprotected training data and $D_2$ for one fitted on defended training data; both are evaluated on the identical defended test examples. The threshold uses total TLS record payload bytes. $D_2$ uses the first four or all twelve training topic pairs; these budgets do not represent multiple independently sampled training sets. At a 1024-byte bucket, $D_0$ constantly predicts the expanded class and scores 50\%, while $D_2$ scores 70.8\% (58.3--83.3\%). An offset of 512 bytes permits 100\% adapted accuracy. This demonstrates why a shifted $D_0$ alone is insufficient, without claiming novelty for adaptive evaluation.

Random-tail padding is evaluated over 50 draws per output. The first draw is socket measured and the remaining 49 use the record-length accounting checked against the socket replay. Each topic's paired correctness is averaged over its outputs and draws before 10,000 topic-bootstrap resamples (seed 20261021). Fractional accuracies therefore do not imply additional independent topics; the intervals condition on these saved outputs and fitted attackers. Positive adaptation gains span 13.5--50.0 percentage points; both constant caps have zero gain.

No measured accuracy of 50\% proves absence of all leakage. The constant-cap construction makes only the specified record-length sequence constant when there is no overflow. Timing, connection behavior, request metadata and content are outside that projection. No sequence/timing attack, TLS~1.3 native padding, QUIC or live token/SSE stream is evaluated.

\soktakeaway{SoK Takeaway 3 (Match the workload and receiver)}{Framing outcomes depend on the length distributions, absolute sizes and bucket boundaries of the specified workload. Cohen's $d$ is a standardized mean difference, not entropy or a sufficient predictor of padding cost. Upstream protection and low accuracy of a clean-trained attacker each require additional evidence before reuse at a new receiver.}

\input{sections/35-tau-cover-bridge}
''')

write('sections/12-conclusion.tex',r'''
\section{Conclusion}\label{sec:conclusion}
This SoK organizes \FinalN{} study families and 39 intervention result records into an audit of receiving projections, execution boundaries and matched evaluation objects. Its contribution is to show which comparisons the existing measurements support, which conflict, and which remain unresolved. The author-constructed scenario exercise illustrates the rules without establishing external decision accuracy.

Two separate mechanism studies reinforce the audit obligations. Workload-matched TLS accounting removes the apparent sub-baseline cost advantage, and a training-fitted cap provides a much cheaper constant-length control than the original loose cap. Retail reference execution distinguishes same-value inputs from state preservation and exposes cancellation labels to simple rule attacks even when user state is preserved. Neither study establishes joint protection for autonomous agent workflows. The reusable result is the evidence boundary and the specific additional measurement each transfer claim requires.
''')

# Audit numbering is independent of the three operational checks.
p=M/'tables/six-check-audit.tex';s=p.read_text()
s=s.replace('Splitting Check~4 (D1 vs.\\ D2) and Check~6 (inference, utility, cost) exposes component-level variance without requiring every study to run an end-to-end deployment evaluation.','R1--R9 describe evidence for scoped reuse claims; they are separate from deployment Checks~1--3.')
for a,b in [('1. Target','R1. Target'),('2. Receiver','R2. Receiver'),('3. Placement','R3. Placement'),('4a. Protected-condition fit (D1)','R4. Protected-condition fit'),('4b. Matched adapted test (D2)','R5. Matched adapted test'),('5. Workloads','R6. Workloads'),('6a. Defended','R7. Defended'),('6b. Task','R8. Task'),('6c. Mechanism','R9. Mechanism')]:s=s.replace(a,b)
s=s.replace('jointly binds 6a, 6b and 6c','jointly binds R7, R8 and R9').replace('Independent two-coder agreement','Supplied two-column agreement')
s+=r'''
% Dangol R5 is capture-scoped; live refit remains NR-V. See main text.
''';write('tables/six-check-audit.tex',s)

# Remove the remaining optimistic generalizations from literature discussion.
edit('sections/11-discussion.tex',r'violates $I(S;Y\mid Z)=0$. Section~\ref{sec:controlled-placement} demonstrates this boundary on real loopback TLS~1.2 sockets and shows how required terminal framing overhead scales with natural task length separability ($d\in[0.25,10.4]$).',r'need not satisfy $I(S;Y\mid Z)=0$. The sufficient-condition theorem then ceases to certify the bound; leakage must be checked separately. Section~\ref{sec:controlled-placement} demonstrates the specified re-emission mechanism on TLS~1.2 sockets.')
edit('sections/11-discussion.tex',r'AHB\'s own','AHB\'s own')
s=(M/'sections/11-discussion.tex').read_text()
s=s.replace('despite an unauthorized cover call having mutated production state','although the endpoint does not establish authorization of the earlier call')
s=s.replace(r'98.333\% CI',r'98.333\% Bonferroni-adjusted CI (three contrasts)')
s=re.sub(r'Section~\\ref\{sec:controlled-placement\} \(Tables~.*?\(\$\+22.5\$pp to \$\+49.0\$pp\)\.',r'Section~\\ref{sec:controlled-placement} gives a matched TLS adaptation example. The separate retail study shows why prior-based baselines and rule attacks must accompany a learned observer; an improvement over $D_0$ alone does not establish useful inference.',s)
s=s.replace(r'$D_2$: comparing a clean-trained classifier $D_0$ against a defended-trained classifier $D_2$',r'comparing a clean-trained classifier $D_0$ against a defended-trained classifier $D_2$')
write('sections/11-discussion.tex',s)

write('tables/synthesis-decisions.tex',r'''
\begin{table*}[t]\centering\footnotesize
\caption{Source-local findings, cross-study synthesis and the resulting measurement obligation. These are reuse judgments, not accusations that the source authors claimed end-to-end protection.}\label{tab:synthesis-decisions}
\begin{tabularx}{\textwidth}{@{}p{.14\textwidth}YYY@{}}\toprule
Check & Source-local evidence and locator & Synthesis added by record separation & Changed judgment / controlled evidence\\\midrule
1. Receiver & NetEcho IV-C--E/Fig.5: frontend re-emission; SplitDecoy 5.1--5.3: backward gradient support. & Protected upstream and forward views do not cover newly exposed downstream or backward inputs. & Bind the final observer or prove the postprocessing condition. Two-link TLS placement reproduces this mechanism; costs use identical texts.\\
2. Execution & WRA 8.1/Table8: read-only query decoys; AHB 5.2.3/Table1/E.3: live GUI humanization. & Objectives, live action semantics and protected state scopes differ, so their utility outcomes are not contradictory. & Evaluate task objects, full account and shared database separately. Retail same-item writes change status; known-position filtering defeats cover in the specified dispatch view.\\
3. Adaptation and cost & UI Traces 6.1: delayed-trace refit; Dangol 9.7: capture versus live protocol; Early Bird's KV-prefix versus semantic-cache mechanisms. & A paired attack contrast requires the same defended tests; costs from another mode or mechanism cannot price the claimed protection. & Keep source-local comparisons and mark missing bridges unresolved. TLS adapted accuracy remains 70.8\% under 1024B buckets; the retail class-prior baseline exceeds the legacy learned accuracy.\\\bottomrule
\end{tabularx}\end{table*}
''')

write('sections/10-open-challenges.tex',r'''
\section{Implications, Ethics and Limits}\label{sec:agenda}
\subsection{Reporting obligations and open problems}
The nine audit items identify evidence needed for particular transfer claims: R1 target and protected interest; R2 receiver fields and linkage; R3 intervention placement and execution; R4 defended-condition fitting; R5 matched adaptation contrast; R6 workload and generator shifts; and R7--R9 inference, utility and cost. They do not require every component study to implement an autonomous agent. Inapplicable and unverified items must remain distinct from unreported evidence.

Three priorities follow. First, terminal streaming protocols should account for new target-bearing inputs at each frontend, using realistic length tails and timing observations. Second, tool contracts should state the protected state scope and successful/rejected-call effects; same-value payloads and repeated-call idempotence are different from a no-change guarantee. Third, cover evaluation should include policy-aware count and sequence attacks before describing a privacy--utility frontier. Constant write counts alone need not hide order, names, identifiers or response lengths. Workload-level cache-reuse costs and cross-generator fingerprint portability remain separate open problems \cite{addagada2026kvgov,wu2026cacheprune}.

\subsection{Ethics and artifact scope}\label{sec:ethics}
The revision executes only local loopback sockets and cloned public benchmark databases. It invokes no production tool, sends no cover action to a real account and makes no new model API call. The synthetic and retail programs are prescribed reference executions; they are not observations of real user consent. The other-account cancellation condition is a simulator control, not a recommendation to cancel orders belonging to other users. A deployable decoy would require explicitly controlled resources and a separate isolation argument.

The corpus includes both confidentiality protection and bot-detection evasion. Authorization and protected interests must be stated: AHB's humanization objective differs from user privacy against a passive observer \cite{zhu2026turing,jeong2026wra}. Source analysis does not authorize evasion of third-party controls. The local artifact retains saved model outputs and their source provenance; model availability, terms at the historical generation date and fresh-generation reproducibility have not been independently revalidated in this revision. An accessible immutable anonymous repository remains a submission task; local files and hashes do not constitute a public release.

\subsection{Threats to validity}
The purposive corpus and narrow-query overlaps do not estimate field-wide recall. The four objective groupings overlap. Supplied coding columns support agreement calculations, while coder identity, blinding and independent adjudication cannot be established from those columns alone. Four added families were outside the baseline agreement sample. Cell-level historical bootstrap intervals and a high $\kappa$ do not establish external validity.

The 24 scenarios were constructed by the authors from the development corpus. Their labels and annotations are retained as illustrative material; no fair held-out superiority comparison is claimed. The synthetic indexing experiment has a negative joint result and supplies no proof of framework effectiveness.

TLS results condition on 48 saved outputs from one model, 12 held-out topics, prompted verbosity and two prefix constructions. Topic bootstrap intervals do not capture model, prompt or generation variability. The implementation uses TLS~1.2 replay, not token streaming, TLS~1.3 padding or QUIC. Timing and stronger traffic classifiers are untested. The retail study uses gold reference programs, 97 eligible tasks and three repeated seeds, not autonomous planning. The instruction-aware heuristic was developed on the available task collection; the 48/49 split holds out classifier tasks, not policy development. These two observer models and experiments are separate, so their results cannot establish joint end-to-end protection.
''')

edit('sections/30-reproducibility-guide.tex',r'D0 / D1 / D2 & Clean-trained attacker / Protected-condition fitting / Matched $D_0$-vs-$D_1$ comparison on the same defended test set.',r'D0 / D2 & Attacker fitted on clean / defended training data; compared on the same defended test set. Legacy D1 denotes the fitting condition, now R4.')
edit('sections/30-reproducibility-guide.tex','with independent human dual-coding records','with supplied coding records')
edit('supplement.tex',r'\title{Supplementary Evidence: When Do LLM Side-Channel Defenses Protect Agent Workflows?}',r'\title{Supplementary Evidence: Evidence Boundaries of LLM and Agent Side-Channel Defenses}')
edit('supplement.tex',r'\IEEEtriggeratref{78}','')

# Remove misleading residual wording in supporting sections while preserving archived evidence unchanged.
for p in M.rglob('*.tex'):
    s=p.read_text(encoding='utf-8')
    s=s.replace('payload-idempotent','same-value').replace('Payload-idempotent','Same-value')
    s=s.replace('state-idempotent','state-preserving').replace('State-idempotent','State-preserving')
    s=s.replace('Appendix Appendix','Appendix').replace('Tables XC','Table X')
    p.write_text(s,encoding='utf-8')
print('Core manuscript revision applied')
