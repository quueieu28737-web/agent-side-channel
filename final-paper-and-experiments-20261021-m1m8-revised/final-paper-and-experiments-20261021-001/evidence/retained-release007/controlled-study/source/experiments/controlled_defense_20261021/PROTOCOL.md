# Controlled intervention placement study, 2026-10-21

User authorization: current request explicitly authorizes new searches, two
controlled experiments and new Luna collection. Prior sealed campaigns and
negative results remain original evidence. This is a new controlled system.

## Fixed questions and predictions

E1 tests whether fixed upstream padding is inherited by a new content-aware
emitter. H0: upstream-only padding removes the held-out length inference at
both links. H1: padding equalizes upstream application-record sizes while the
unprotected new emitter restores a length-correlated observable; padding the
final link removes that specific size feature. A failure to equalize the
upstream link, or identical final lengths across goals without endpoint padding,
refutes the intended mechanism on this stack. No result is predetermined.

The secret is the private response-format requirement (brief vs expanded) for
the same synthetic public topic. 24 topic pairs, one response per requirement;
12 topics train and 12 test by a seeded topic split before collection. The
attacker sees ciphertext sizes only; topic, goal labels, text and run paths
are not features. Threshold fitted independently for each link/arm on training
topics, no tuning using test results. Timing is measured as a secondary cost;
size equalization alone is not a total-traffic privacy certificate. Model output
is collected once and replayed identically through actual localhost TLS links
for the three paired placement arms; model-generation latency is not measured.
The frontend buffers, removes padding and emits 128-byte chunks. Primary outcome
is held-out balanced accuracy from total server-to-client application TLS-record
payload bytes; a cluster bootstrap resamples paired test topics. Ciphertext
streams and TLS-record parsing receipts are retained. Each response/arm has one
transport execution. Synthetic fixtures are tests, not study observations.

E2 tests whether cover routing preserves objective task state. H0: all cover
classes leave live task state and success identical to no cover. H1: discarded,
isolated shadow and genuinely read-only cover preserve business state, while
state-changing cover can alter it in overlapping/protected-resource cases.
24 fixed tasks, 12 inventory and 12 calendar; one Luna action plan per task.
Every original plan is replayed without repair under baseline and the four
cover classes. Cover insertion precedes the first plan action. Same-resource,
protected-disjoint and spare-disjoint conditions are fixed in advance, including
tight/slack resource availability. The local tool broker enforces actor,
confirmation and parameter checks; it never fixes a model plan. Failures are
retained. Domain state and audit logs are reported separately. Read-only is
implemented using a pure getter; general idempotent mutation is not assumed
safe. Record goal success, protected-state violations, exact live-state changes,
cover dispatch count, local elapsed time and paired differences vs baseline.
Resample whole tasks for intervals, not correlated arms. These are model-plan
replays in a finite controlled tool system, not full interactive agent runs.

## Model boundary and finite budget

Exact requested model gpt-6-luna, OpenAI built-in provider via existing ChatGPT
Codex CLI login; reasoning low. No model/provider fallback. Only public synthetic
topic requests and public synthetic tool task state/schema are transmitted.
No manuscript, previous logs, labels/expected grading answers, or private records.
72 application-generation admissions at most (48 E1 +24 E2), sequential,
120 seconds local wait per turn, 90 minutes total collection wall budget including
cleanup. No application retry. Provider internal retries and provider network
request count are NR; CLI does not expose them. Output length is requested but
not a hard provider token cap. Observed usage is recorded; unknown is not zero.
No extra ready-prompt generation: preflight uses only model list and empty
ephemeral thread attestations. Each response requires the exact returned model,
empty execution roots, no available tools, one final answer, known usage, clean
exit/EOF. Protocol or identity failures stop new admissions; content failures
with complete transport are retained. Timeouts stop collection and preserve all
started attempts. Local no-model tests precede collection and source/input hashes
are frozen before the first admitted turn. CPU analysis and local TLS replays
have separate 10-minute bounds each. Original campaigns are never resumed.

## Interpretation and reproducibility

Primary causal contrasts vary only placement/routing for the same saved output
or plan. The controlled construction demonstrates mechanism and applicable
conditions, not a prevalence or general-model claim. Retain all failures, zero
effects and contradictory evidence. Sources, protocol, input split, raw model
events, model identity, usage, observer streams, states, scripts and checksums
are saved. Publication tables are generated only from verified final receipts.
Human double coding remains an external task; no AI result is relabeled human.
