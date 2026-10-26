"""Write manuscript accounting/sensitivity from preserved record labels."""
from pathlib import Path
import csv,json,re
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
def read(n):return list(csv.DictReader((O/n).open(encoding='utf8')))
def put(rel,s):(M/rel).write_text(s,encoding='utf8',newline='\n')
def change(rel,a,b):
 s=(M/rel).read_text(encoding='utf8');assert a in s,rel;put(rel,s.replace(a,b,1))
a=json.loads((O/'analysis.json').read_text())
names={'inference_utility':'Inference + utility','inference_cost':'Inference + cost',
'adapted_inference':'Matched adaptation + inference','inference_utility_cost':'Inference + utility + cost',
'adapted_inference_utility_cost':'All five bindings'}
joins=read('joint-accounting.csv')
table=r"""\begin{table}[t]\centering\footnotesize
\caption{Query accounting from the same 33 mitigation records. Out: at least one required item is inapplicable; Eligible: remaining records; Bound: all required items are B.}\label{tab:r19-joint}
\begin{tabularx}{\columnwidth}{@{}Yrrrr@{}}\toprule
Query & Out & Eligible & Bound & Fam./Cfg.\\\midrule
"""
for r in joins:table+=names[r['query']]+f" & {r['excluded_records']} & {r['eligible_records']} & {r['bound_records']} & {r['bound_families']}/{r['bound_configurations']}"+r"\\"+'\n'
table+=r"""\bottomrule\end{tabularx}
\par\smallskip\raggedright Required items by row: R7/R8; R7/R9; R4/R5/R7; R7/R8/R9; all five. The two sets of 22 eligible records differ. Six contextual controls are outside the starting 33. Fam./Cfg.\ deduplicates bound records. CachePrune supplies the triple join: two outcomes at one configuration. Joins preserve cost scope and do not imply paired effects. S33 lists every exclusion and status.
\end{table}
"""
put('tables/r19-joint-bindings.tex',table)
change('main.tex',
'First, comparison of all 741 record pairs identifies 133 related pairs, of which 17 support a source-qualified descriptive comparison. Eight of 15 same-family pairs concern different primitives, targets or costs: a shared paper or mechanism name can conceal incompatible evaluation objects.',
'First, a complete pair inventory distinguishes source-qualified comparisons, known object mismatches and unresolved bindings. Comparisons within the same paper expose changes of primitive, target and cost that mechanism-level summaries conceal.')
change('main.tex',
'The audited collection contains one bound inference--utility--cost package, supplied by two CachePrune records sharing one configuration.',
'CachePrune illustrates this distinction: two recorded outcomes share one inference--utility--cost package at a single configuration.')
change('sections/01-introduction.tex',
'We examine all 741 pairs of 39 result records. Among 133 related pairs, 17 permit a source-qualified descriptive comparison; eight of 15 same-family pairs concern different primitives, targets or costs. The resulting comparison reasons expose substitutions that paper-level summaries conceal.',
'The complete inventory of 741 record pairs separates supported descriptive comparisons from object mismatches and unresolved evidence. Within-family contrasts expose substitutions of primitive, target and cost that paper-level summaries conceal. Cohort accounting and family-deletion checks make the dependence on grouping and record multiplicity inspectable.')
change('tables/r9-rq-findings.tex',
'Eight of 15 same-family pairs concern different primitives, targets or costs; only 17 of 133 related pairs support descriptive comparison. Shared mechanism names do not bind execution or state effects.',
'Six of the 11 families with multiple records contain a primitive, target or cost mismatch. The full pair inventory separates descriptive matches, mismatches and unresolved bindings; shared mechanism names do not bind execution or state effects.')
change('sections/03-methodology.tex',
'The record-local extension reuses these bindings and documents targeted source-follow-up changes.',
'The record-local extension reuses these bindings and documents targeted source-follow-up changes. The pair inventory fixes the mechanism-question cohorts; joint queries start from the same 33 mitigation records and publish their eligibility masks. S33 reports status-rule, unresolved-binding and family-deletion sensitivity without changing archived labels.')
change('sections/27-intervention-contracts.tex',
'Eight of 15 same-family pairs substitute primitives, targets or cost objects.',
'Eight of the 15 same-family pairs substitute primitives, targets or cost objects, distributed across six of the 11 families with multiple records.')
change('sections/27-intervention-contracts.tex',
'Of 133 related pairs, 17 (12.8\\%) support a source-qualified descriptive comparison, 105 (78.9\\%) have an established object/receiver/target mismatch, and 11 (8.3\\%) remain unresolved.',
'Of 133 related pairs, 17 support a source-qualified descriptive comparison, 105 have an established object/receiver/target mismatch, and 11 remain unresolved.')
change('sections/27-intervention-contracts.tex',
'Examples illustrate this census rather than define its sample.',
'Examples illustrate this census rather than define its sample. The 15 same-family pairs share records and families. Removing KVGov leaves five mismatches among 12 pairs; removing Whisper Leak leaves eight among 12. Across all 26 family deletions, related-pair compatibility ranges from 7.8\\% to 15.2\\%. Resolving all 11 uncertain pair judgments favorably would increase the compatible count from 17 to 28, with the 105 known mismatches unchanged. S33 reports each cohort and deletion. These are inventory sensitivities, not independent-sample prevalence estimates.')
change('sections/27-intervention-contracts.tex',
'Denominators exclude a record if any required item is inapplicable; U, ?, and P remain eligible but unbound. The six contextual controls are separate. Only CachePrune supports the 2/20 join: two outcomes share one quality/cost package, not two independent confirmations.',
'All joint queries begin with 33 mitigation records. A query excludes a record only when a required item is inapplicable; U, ?, and P remain eligible but unbound. Table~\\ref{tab:r19-joint} separates excluded, eligible and bound counts, with deduplicated families/configurations. The six contextual controls are separate. CachePrune supplies the triple join: two outcomes share one quality/cost package.')
change('sections/27-intervention-contracts.tex',
'This is more informative than treating every family-level B as a complete deployment result.',
'This is more informative than treating every family-level B as a complete deployment result. Accepting P and ? as if bound leaves the triple join at two records, but changes matched adaptation--inference from two to 16 of 17. Thus uncertainty concentrates differently by query. Removing CachePrune removes the sole triple package; no other deletion does. These checks locate which additional source bindings would change a decision, rather than turn missing reports into evidence of failure.')
change('sections/10-open-challenges.tex',
'The 2/20 inference--utility--cost join is one family/configuration with two recorded outcomes, rather than an estimate of field-wide practice.',
'The inference--utility--cost join identifies one family/configuration with two recorded outcomes. Its status-rule stability is conditional on leaving unreported evidence unbound; its positive support depends on CachePrune. S33 exposes those dependencies. Executable counts and sensitivity checks do not measure agreement between independently coding researchers.')
change('sections/12-conclusion.tex',
'These literature-derived outputs make the scope of a defense claim inspectable before it is carried into a new deployment.',
'Published query membership, source-linked reasons and family/status sensitivity make these outputs inspectable before a defense claim is carried into a new deployment.')

# Append S33 so all historical supplementary section numbers remain stable.
change('supplement.tex',r'\input{sections/64-case-study-register}',
r'\input{sections/64-case-study-register}'+'\n'+r'\clearpage\onecolumn'+'\n'+r'\input{sections/65-audit-sensitivity}')
change('sections/58-record-joint-audit.tex',
'The six contextual controls are excluded from all mitigation join denominators.',
'The six contextual controls are excluded from all mitigation join denominators. Section~\\ref{app:audit-sensitivity} expands every query from the common 33-record starting set, including each excluded identity and triggering item.')

s=r"""\section{Audit Accounting and Judgment Sensitivity}\label{app:audit-sensitivity}
This deterministic reanalysis uses the archived 39-record/351-cell audit and all 741 pair judgments. It adds no sources, model calls, customers or independent recoding. The original labels, cohort definitions, source locators and rationales are unchanged. The released tables record both input hashes and every query membership. The goal is to expose which choices support a finite-corpus statement and which additional evidence would change it.

\subsection{Common starting set and query masks}
There are 33 mitigation records from 20 families and six contextual controls. Every join starts from the same 33; a required inapplicable item excludes that record from that query only. Partial, unverified and unreported bindings stay eligible. All required items must be B to count as bound. Table~\ref{tab:r25-membership} makes this rule visible record by record; the full cell table in Section~\ref{app:record-joins} supplies source locators and rationales. Inference--utility and inference--cost each admit 22 records but not the same set. Triple-join eligibility covers 20 records, 14 families and 19 archived configuration groups; its two positive records reduce to one CachePrune configuration. Configuration identifiers deduplicate the archived packages and do not imply common sampled requests.

\subsection{Status-rule stress checks}
Table~\ref{tab:r25-relaxation} varies accepted statuses while holding applicability, cohorts and records fixed. B is the supported result. The other columns deliberately weaken that standard: accepting P tests the effect of treating partial evidence as sufficient, and accepting ? treats an unverified binding as if satisfied. P may encode a known missing or mismatched operating-point link, so these stress counts are not additional supported joins or a recoding of sources. U remains unreported in these columns. If U is also mechanically accepted, every eligible row passes by construction; the released all-status column documents this vacuous extreme rather than presenting it as evidence.

\begin{table}[ht]\centering\small
\caption{Status-rule stress counts, with applicability held fixed. Only the B column denotes supported joins.}\label{tab:r25-relaxation}
\begin{tabular}{@{}lrrrrr@{}}\toprule
Query & Eligible & B & B or P & B or ? & B or P or ?\\\midrule
"""
relax=read('status-relaxation.csv')
for r in joins:
 vals=[next(x['selected_records'] for x in relax if x['query']==r['query'] and x['rule']==rule) for rule in ['B','B_P','B_question','B_P_question']]
 s+=names[r['query']]+' & '+r['eligible_records']+' & '+' & '.join(vals)+r'\\'+'\n'
s+=r"""\bottomrule\end{tabular}\end{table}
The triple join is unchanged under these relaxations, whereas matched adaptation--inference rises from 2 to 15 when ? is accepted, and to 16 when P is also accepted. The distinction matters operationally: the latter query needs resolution of fit/test bindings, while the triple join needs presently unreported outcome bindings. Stability to P/? does not authenticate the source interpretation or establish that additional unreported evidence does not exist.

\subsection{Pair scope and family dependence}
The 133 related pairs belong to six mechanism-question cohorts (Table~\ref{tab:r25-cohorts}). The other 608 are outside those declared queries, not failed comparisons. Resolving all 11 uncertain related judgments as compatible gives 28 compatible pairs instead of 17; retaining them as unresolved leaves 17. The 105 known mismatches stay fixed. This is a conditional completion range within the stated cohorts, not robustness to every alternative cohort construction.

\begin{table}[ht]\centering\small
\caption{Exhaustive related-pair accounting, stratified by declared question.}\label{tab:r25-cohorts}
\begin{tabular}{@{}lrrrr@{}}\toprule
Cohort & Pairs & Compatible & Mismatch & Unresolved\\\midrule
"""
for r in read('pair-cohorts.csv'):
 s+=r['cohort'].replace('-',' ')+' & '+' & '.join(r[k] for k in ['pairs','compatible','incompatible','unresolved'])+r'\\'+'\n'
s+=r"""\bottomrule\end{tabular}\end{table}
The 15 same-family pairs arise from 11 families, and their eight mismatches occur in six families. Pairs share records; families with more records contribute more pairs. Table~\ref{tab:r25-deletions} removes every family and all its incident pairs, one family at a time. Related-pair compatibility spans 7.8--15.2\%; the same-family mismatch fraction spans 5/12--8/12. Deleting KVGov removes three mismatches, while deleting Whisper Leak removes three compatible pairs. Neither operation adds independent observations. We report descriptive counts and dependency checks rather than binomial confidence intervals over dependent pairs.

For the triple join, removing CachePrune leaves zero bound records among 18 eligible records. Removing any other mitigation family retains the two records and their single configuration. The archived \texttt{joint-leave-family-out.csv} gives all 100 query-by-family deletions, and \texttt{query-membership.csv} gives all 165 query-by-record decisions. These diagnostics expose concentration and rule dependence; they do not measure independent coder agreement or validate the framework by counting its own outputs.

\clearpage
\begin{table}[ht]\centering\small
\caption{All 33 mitigation records and their five query memberships. B: eligible and bound; E: eligible but not bound; x with item numbers: excluded because those required items are inapplicable. IU=R7/R8; IC=R7/R9; AI=R4/R5/R7; IUC=R7/R8/R9; All=R4/R5/R7/R8/R9. Source rationales are in Section~\ref{app:record-joins}.}\label{tab:r25-membership}
\begin{tabular}{@{}lccccc@{}}\toprule
Record & IU & IC & AI & IUC & All\\\midrule
"""
membership=read('query-membership.csv')
for rid in dict.fromkeys(r['record_id'] for r in membership):
 vals=[]
 for q in names:
  r=next(x for x in membership if x['record_id']==rid and x['query']==q)
  vals.append('B' if r['bound']=='True' else ('E' if r['eligible']=='True' else 'x'+r['inapplicable_items'].replace('R','')))
 s+=rid.replace('_',r'\_')+' & '+' & '.join(vals)+r'\\'+'\n'
s+=r"""\bottomrule\end{tabular}\end{table}

\clearpage
\begin{table}[ht]\centering\small
\caption{All 26 leave-one-family-out pair inventories. C: compatible related pairs; M: same-family mismatches. Counts reuse remaining records and are not sampling replicates.}\label{tab:r25-deletions}
\begin{tabular}{@{}lrrrr@{}}\toprule
Removed family & Related pairs & C & Same-family pairs & M\\\midrule
"""
for r in read('leave-family-out.csv'):
 s+=r'\cite{'+r['removed_family']+'} & '+' & '.join(r[k] for k in ['related_pairs','compatible','same_family_pairs','same_family_incompatible'])+r'\\'+'\n'
s+=r"""\bottomrule\end{tabular}\end{table}
"""
put('sections/65-audit-sensitivity.tex',s)
print('R25_MANUSCRIPT_UPDATED')
