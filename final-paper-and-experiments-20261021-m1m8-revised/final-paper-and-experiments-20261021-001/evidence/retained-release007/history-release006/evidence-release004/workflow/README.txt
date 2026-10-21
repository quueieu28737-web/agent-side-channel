WORKFLOW COMPARISON: SAVED-OUTCOME DECOMPOSITION AND INTERVAL REPLAY
Date: 2026-10-20, Europe/London
Scope: reviewer requests 21--23. Offline only, 0 model calls, 0 fits.

Canonical derived result: attempt-002/result.json.
attempt-001 is retained as the first successful arithmetic replay; its numerical
outputs agree. Before attempt-001 ran, a Python syntax error (one missing closing
parenthesis) stopped compilation before input reads or output creation. It was
fixed locally, not by changing any saved experimental data or scoring endpoint.
attempt-002 additionally binds hashes before each input read and checks them at
the end. All 3,189 read-only source files retain their recorded hashes.

ORIGINAL DATA AND BOUNDARY

The source is experiments/scope_workflow_v2_20261019. The casepack contains 546
roots: 16 development, 512 primary and 18 source-transfer. The formal schedule
contains only the 530 nondevelopment roots times 3 arms = 1,590 slots. Each slot
has 3 queries. An approved missingness analysis retains original slot 37 (T arm,
primary root W9cfac0408c9ffc) as an unscored infrastructure HOLD; its 3 queries
are not false outcomes, true outcomes, or zero cost. No raw outcome is replaced.

decompose.py reads the public packets, saved reference, source bindings, saved
schedule, original slot responses and closure hashes, and saved analysis. It
does not import the live runner, model transport, classifier, or source project
code, and has no network/model/subprocess entry point. It independently
implements the finite packet interpreter, compares all 546 references, and
reconstructs every one of the 1,589 saved joint scores (and each saved per-query
grade). Independent code replay is not independent researchers or independent
test/construct design. The same model-assisted project prepared these cases.

The exact extraction replay command (requires a NEW output path) is:

  python -B evidence/reviewer-substantive-20261020-001/workflow/decompose.py
    --out evidence/reviewer-substantive-20261020-001/workflow/attempt-NEW

No repeated extraction is required to inspect the delivered result. The script
refuses an existing output directory. The delivered arithmetic verifier is
read-only and can be run directly:

  python -B evidence/reviewer-substantive-20261020-001/workflow/verify.py

To additionally recheck source-file SHA256 values, append:

  --project <LOCAL_WORKSPACE>

For an anonymous supplement copy, verify.py can be placed alongside attempt-002
and checks saved derived rows without requiring the original private response
tree. Source-path hashes establish local provenance, not publicly hosted raw
data availability or rights/anonymity clearance.

JOINT ENDPOINT AND ERROR DECOMPOSITION

For root i, arm a, query q, J_iaq=1 only if the supplied schema, case/query IDs,
exact evidence-ID set, decision, and BOTH equal/possible-world counts pass.
Original root score S_ia = (J_ia1+J_ia2+J_ia3)/3, in {0,1/3,2/3,1}.
Every primary arm retains 512 roots, not 1,536 independent observations.
Component rows below are descriptive query counts, not alternative tests:

Arm  decision+count+  decision+count-  decision-count+  both wrong  missing
R               624              537                2         373        0
T               693              476                5         359        3
V               494              695                2         345        0

All 4,767 observed formal queries pass the shared schema and evidence-ID gate.
Thus formatting does not explain any original zero. The frequent global-count
error is substantive under the original semantics, even when a decision can
be correct by ignoring globally irrelevant domains. Wrong possible-world
counts are R 654/1,536, T 579/1,533, V 862/1,536 on primary queries. The original
global configuration space always has 4 states; it does not contract merely
because a variable is irrelevant to the queried receiver. These errors are
not removed or rescored. V's 695 decision-right/count-wrong versus T's 476
diagnoses endpoint composition; it does not establish a causal explanation.

Original means: R=624/1536=40.625%; V=494/1536=32.16145833%; T ranges from
693/1536=45.1171875% to 696/1536=45.3125%. The entire missing T root spans [0,1].
V-T joint bounds are [-202/1536,-199/1536]=[-13.15104167,-12.95572917] pp.
Decision-only contrast ranges [17/1536,20/1536]=[1.10677083,1.30208333] pp,
but changes the endpoint. It is not a rescue of the original +10 pp claim.

STRATA (POST-OUTCOME, DESCRIPTIVE; NO ADDITIONAL p-VALUES OR INTERVALS)

Root-strata.csv preserves one whole root across all arms. Each template 0--7
has 64 roots; its V-T joint contrast (pp) is:
0 [-15.625,-14.0625]; 1 -15.10416667; 2 0; 3 +5.72916667;
4 -19.27083333; 5 -6.77083333; 6 -29.16666667; 7 -25.

All primary inputs have 11 nodes, 11 edges, maximum input-to-output edge-depth
4 and 4 global configurations. There is NO full-graph-size or full-world-space
gradient to estimate. The union of potentially visible receiver-ancestor cones
varies 6/8/9/10/11 nodes, with 64/128/192/64/64 roots; V-T is respectively
0/-11.71875/-13.71527778/[-15.625,-14.0625]/-25 pp. Cone size is confounded with
the constructed template, not independently manipulated graph complexity.

Number of mixed-equality queries per root is 0/1/2 (288/208/16 roots), with
V-T [-13.31018519,-12.96296296]/-12.98076923/-12.5 pp. Relevant configuration
variables number 1 or 2 (256 roots each); V-T is -14.453125 and
[-11.84895833,-11.45833333] pp. Exact reference equal-count diversity is 1/2/3
(16/292/204 roots); V-T is -8.33333333/[-13.12785388,-12.78538813]/-13.56209150 pp.
These choices were made after aggregate outcomes were known. No best subset
is promoted. Query-strata.csv also provides receiver-cone/depth/truth-label/
equal-count counts; within-root queries remain correlated.

95% ENVELOPE: EXACT ALGORITHM, NOT A BOOTSTRAP

The casepack builder uses random.SystemRandom().shuffle once per root to
assign R/T/V to 3 fresh request positions. The saved dispatch schedule is the
randomization replay record; one must not regenerate its permutations. Each
root is a separate allocation unit, not each query. Empirical primary position
counts (positions 0,1,2) are R=(167,167,178), T=(157,189,166), V=(188,156,168).
No equal-position balance is assumed.

Condition on fixed bounded potential scores for each arm at each request slot,
independent root permutations and no cross-request interference. For each root
D_i=S_iV-S_iT lies in [-1,1]. Its expected value averages the slot-position
potential scores. For N=512, Hoeffding yields

  P(|mean(D)-E mean(D)|>=h) <= 2 exp(-N*h^2/2).
  alpha=.05; h=sqrt(2*ln(2/.05)/512)=0.12004034891499009.

Let Delta_L/Delta_U be the original full-denominator contrast extremes when
the missing T root ranges over [0,1]. Take the union over that possible score:

  [max(-1,Delta_L-h), min(1,Delta_U+h)]
  =[-0.25155076558165673,-0.009516942751676569]
  =[-25.15507656,-0.95169428] percentage points.

No missing-at-random assumption or zero imputation is used. This is the
original conservative conditional finite-randomization bound, not an IID
paper population CI, bootstrap, t interval, or exact permutation p-value.
Provider state/interference assumptions are not mechanically certified. The
original all-clean acceptance is still false; unknown usage remains unknown.

FILES

decompose.py: source-bound extraction, reference/scorer replay, strata.
verify.py: read-only saved-row arithmetic verifier, optional source hashes.
attempt-002/root-scores.csv: one row per formal slot with metadata/raw hash.
attempt-002/query-components.csv: 4,770 scheduled query rows incl 3 missing.
attempt-002/decision-count-cross.csv: all-arm, both-source component cross-tab.
attempt-002/format-failures.csv: schema/ID penalties and total-count errors.
attempt-002/root-strata.csv: same-root joint endpoint strata and missing bounds.
attempt-002/query-strata.csv: descriptive, correlated query counts.
attempt-002/input-hashes.json: original inputs and closure/hash lineage.
attempt-002/result.json: combined results and explicit scope/failure boundary.

No result is researcher validation, a demonstrated process benefit, real-paper
contradiction detection, reduced evidence-acquisition cost, private-goal leakage,
or deployed defense evaluation. A receiver-oriented traversal/global-enumeration
mismatch is a future testable explanation, not established by these diagnostics.
