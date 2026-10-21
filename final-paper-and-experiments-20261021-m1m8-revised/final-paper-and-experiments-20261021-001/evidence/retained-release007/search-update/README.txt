Finite supplementary search and source-scoped reconciliation
Date:21October2026. Public metadata/source access only;0 model endpoint calls.

Outcome
Four complete SemanticScholar queries returned538 occurrences/522unique IDs.
Two complete native arXiv Edge queries returned77 occurrences,adding43 IDs.
Combined615 occurrences deduplicate to565 IDs; every ID has a reasoned route.
15new core source-bound rows and7selected adjacent merge proposals are supplied.
The combined manuscript proposal is82families=58core+24adjacent;60 is historical.

What completion means
records.csv completes dispositions for this bounded returned frame, including
16missing-abstract rows and1unavailable-primary-fulltext row. Those are not
exclusions, nor admitted core. A referral/adjacent metadata route is not a
whole-source claim or automatic final inclusion. The manuscript editor must
explicitly merge the22 selected additions and keep the remaining routes.

What was not completed
arXiv API attempts timed out. DBLP API failed certificate validation; an OS-TLS
diagnostic returned a bot-verification page, not bibliographic JSON. No TLS
checks or verification were bypassed. S2broadS1 reported2104but only999were
acquired before the declared resource cap; the bounded S1R was an openly
documented subsequent refinement, not a preregistered success. S4R returned429
and no S2 retry was attempted. Native arXiv A3 traffic/LLM timed out without
verified results; A4 was not submitted. These are not zero-result queries.
The historical IEEEQ4/ACM backlogs are not closed by this supplement.

Main files
PLAN.txt,plan.json,amendment-finite-scope.txt,finite-queries.json:actual scope.
querylog-combined.json:successful/failed queries and raw receipt pointers.
records.csv:565unique ID routes,criterion,reasons,24-word-max index excerpts.
fulltext-review.csv:49source-scoped rows,not49new core papers.
addition.csv/json:15new core,observer/signal/target/evaluation/defense/utility/
 cost/RQ/version/locator/hash and explicitNRconditions.
addition-adjacent.csv/json:7selected adjacent proposals,with C3/C5 boundaries.
source-verified-adjacent.csv:30source-scoped adjacent contexts;not all selected.
new_refs.bib,new_refs_adjacent.bib:15+7version-bound proposed citations.
coverage.csv,coverage60.csv:17/24 and25/60 fixed-known query recovery;
 calibrated index recall remainsNR,index non-return does not mean absence.
exclusion-audit.csv/audit-changes.csv:204same-workflow checks,4reroutings.
SYNTHESIS-SENSITIVITY.txt:concrete changes to RQs,positive cases,closest prior.
summary.json,verification.json,manifest.json:reconciliation/limited verification.

Audit and uncertainty
The exclusion audit uses seed20261021,all177high-risk original exclusions,
and27other reason-stratified samples(at most10/reason). It found1new core,
1previously retained title/version alias and2adjacent-context reroutes.
It is not an independent human audit or an unbiased false-negative estimate.
Core suggestions were also checked against C3:two latent-content inversion
papers were moved to adjacent rather than inflating auxiliary-channel scope.

Raw/data handling
raw/*.body andsources/* contain acquired publisher/preprint content for local
source checking. Do not redistribute full texts in anonymous artifacts by
default. Export CSV reasons/locators/short excerpts,metadata receipts,query
logs andhashes instead. Primary webpage rendering is labeled separately from
originalHTML/PDF:LLM-WFIN uses the official publisher's rendered primary article
returned by web search; failed direct403/429routes remain recorded.

Reproduction without new access
screen.py→make_deliverables.py→finalize.py recompute local classification and
summary,not new searches. coverage60.csv pins the original keys despite later
main-manuscript expansion. Network collection scripts are no-rerun guarded;
do not use them as an implicit resubmission of API or model requests.
