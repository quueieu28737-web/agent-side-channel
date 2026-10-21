Purpose and scope
=================
Additive, retrospective OFFLINE diagnostics requested by the 2026-10-20 review.
No LLM/API/agent calls, no trace acquisition, no Luna, and no original classifier
refit. The original 19-fit analysis and 2026-10-18 36-fit controls remain unchanged.
This is not blind preregistration: their results were known at configuration time.

Execution
---------
Python 3.9 with the existing NumPy/SciPy/scikit-learn installation:
  python -B diagnostics.py selftest
  python -B diagnostics.py prepare
  python -B diagnostics.py run
  python -B diagnostics.py verify
Each command writes new exclusive artifacts. Do not repeat commands into the
same directory. The immutable freeze hashes diagnostics.py, protocol.json,
original code, admitted data, source scripts, split metadata and saved outputs.
The run executes exactly 12 new fits: failure-only, empty-only, activity-only,
each using the original 3 logistic C candidates and 1 random-forest candidate.
Validation-only selection, seeds, split, training weights and test evaluation
are unchanged. All 12 fits must complete before any diagnostic test prediction.
No model objects/weights are serialized. Raw probabilities and selection/fit
receipts suffice to reconstruct all reported numerical scores.

Retained population and feature permissions
------------------------------------------
All 4,200 admitted records remain. Error-present OR result-absent is an analyst
metadata flag, not verified failure or task success. Failure-only uses its two
underlying binary fields. It is NOT an observer-valid deployable attacker.
Empty-only uses absence of projected Wikipedia JS events, not raw archive
emptiness. Activity-only contains total projected event count plus 7 local-page
timestamp summaries. It excludes action types/order, error flags, text and URLs.
Timestamp sum/mean/std/median/p90 are PAGE AGE summaries. No authenticated
cross-document elapsed duration exists; none is imputed. URL only gates origin;
opaque page_key is neither a feature nor a document identifier.

Field-level permission mapping is in field-permissions.csv. See pinned source
page_tracer.js and agent_runner.ts for actual collection provenance. It concerns
own-document JS capability, not a claim all ordinary sites deliver this archive.

Support and confounding
-----------------------
The admitted source split has dataset=frames and exact question strings but no
semantic family annotation. No family labels are invented. Dataset support by
identity is an authoritative coarse label; identity-exact-question-support.jsonl
is the full exact-question support relation. identity-question-form-proxy.json
uses ONLY the first ASCII word, grouped what/which/who/when/where/how/other.
That grammatical proxy is not a semantic task-family label or balance guarantee.
It is not used by any classifier. All-14 common-question support is reported by
partition. Additional semantic family balance or near-duplicate checks remain NR.

Projection example
------------------
projection-example.json deterministically chooses the shortest admitted record
(ties by ID) that has a nonempty first-document proxy and additional archive
events. It gives EVERY ingested event's inclusion/exclusion, type, time, trigger,
opaque URL digest, complete retained archive view and complete first-document
proxy. No timestamp sorting occurs; source callback-array order is retained.
HTTP navigation is excluded as a predictor, while its marker can delimit the
reconstructed proxy. No frame/document IDs exist. This is a complete INGESTED
record projection, not a claim the sanitized JSON reproduces all raw fields.
Original raw bytes remain bound in the pinned public tar and prior inventory.
Source code's DOM/URL text, collector clocks, answer, error text and metadata are
excluded; failure flags enter ONLY the explicitly analyst-only diagnostic.

Inference
---------
All-record results are the primary diagnostic description. Flagged/unflagged
strata recompute equal question weights WITHIN each subgroup and have different
identity/question compositions. Differences across strata are descriptive,
not a causal failure effect or authenticated success-only comparison.
No new confidence interval is selected/reported for these diagnostic baselines.
The original H2/H3 intervals are unchanged and condition on fixed fits/selection/
noise; they exclude refitting, task-family or deployment uncertainty. A weak
binary baseline cannot exclude higher-order failure/length interactions.

Implementation note
-------------------
The Windows sandbox denies Path.resolve() on new paths; code uses absolute()
within the explicit workspace instead. The no-fit check initially completed
asynchronously; a second attempted check correctly refused to overwrite its
existing JSON. No fit was repeated. These were engineering events, not missing
or discarded statistical results.
