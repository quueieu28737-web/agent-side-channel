# E14: post hoc attacker and traffic-defense sensitivity

Written before this analysis is fitted or scored. This is a new analysis of an already inspected cohort, **not preregistration or an independent confirmation**. Existing E9--E13 measurements and thresholds remain immutable.

## Questions and fixed comparisons

1. Does adding a trainable sequence CNN and a random-forest leaf-fingerprint nearest-neighbor attack increase the maximum observed intent inference?
2. Where do four classical WF mechanisms fall on a common workload's leakage/byte/call trade-off, and which delay quantities are measured versus simulated?
3. How does calibrating a defense on short training workflows transfer to the full held-out workload?

Use all 690 original model episodes (414 training / 276 customer-disjoint test). Analyze the two prompt arms and cancellation/return targets separately; the statistical unit is the customer. No new independent customers, model calls, production traffic or human ratings are generated.

## Data and adaptations

Reuse E13's six measured TLS conditions, preserving actual record completion times and actual latency. Add a 1024-byte record-bucket transform and four offline WF adaptations to E13's undefended captures. All bytes include the same five-byte TLS header; generated fixed cells carry 512 plaintext bytes plus 24 bytes of TLS 1.2 AEAD overhead. WF adapters preserve every real byte/direction and use only training-fitted parameters. They do not execute dummy tools. Offline no-delay transformations do not measure contention; simulated delay is never labeled online latency.

- Tamaraw: per-direction constant slots, 40/12 ms and geometrically randomized padding to multiples of 50 cells. A faster 4/1.2 ms operating point is also reported. Preserve input causal ordering when queueing records; propagate output delay to later records. These settings instantiate the mechanism on RPC records, not a Tor deployment.
- FRONT: independently sample a uniform dummy count per direction and a Rayleigh timing window. Scale the budget to the training median cell count and window to training trace-duration quartiles; cancel outstanding dummies at the real trace end. No true record is delayed.
- WTF-PAD adaptation: send/receive-triggered burst/gap state machines with training-fitted interarrival histograms, token removal/refill and infinity tokens; no true record delay or end-of-trace extension. Exact differences from the public simulator are documented in the implementation notes; this is not a reproduction of its published Tor configuration.
- Walkie-Talkie adaptation: half-duplex directional bursts, maximum-length molding with a randomly selected training donor from a different customer, including donor-only suffix bursts. No test label, future test trace selection or sensitive/non-sensitive oracle pairing. This random-donor adaptation does not inherit the original symmetric pairing guarantee.
- Distribution-shift control: the same FRONT algorithm is calibrated on the lower half of training-customer mean trace lengths and applied to all test customers. The attacker still trains on all defended training traces; do not remove difficult test examples.

## Attacker and statistics

All attackers are defense-aware D2: algorithm/configuration are public and training examples use the evaluated defense; labels and customer identifiers are never input features. Seven families: majority, standardized logistic regression, gradient boosting, random forest, extra trees, k-FP-style forest-leaf Hamming nearest neighbors, and a trainable two-layer 1D CNN on direction/length/gap/mask sequences. CNN hyperparameters/epochs are fixed before scoring; any sequence truncation is counted. Use full-trace aggregate features in the other learners. Preserve the full original E13 attacker union for measured conditions so adding attackers cannot reduce its maximum.

Save fitted models and a source/data hash receipt before evaluating the existing test partition. Report suite-maximum BA and AUROC with 2,000 customer bootstrap draws, recomputing maxima in each draw; retain the original upper-BA < .60 and AUROC < .65 test. Report all settings, not just favorable settings. Byte/call Pareto dominance uses maxima across both targets and is descriptive for these operating points. Measured and simulated delay occupy explicitly separate plot panels.

## Power planning and external work

Provide a reproducible independent-cluster binomial planning sensitivity for positive counts 5--250, class ratios and 1/7 independent or perfectly correlated attackers. This is not an estimate of the exact heterogeneous-customer bootstrap power. Thirty positive customers is a minimum planning floor, not a guaranteed pass. A separate prospective protocol specifies new customers, fixed model versions, training freeze and independent human coding; those collections remain unperformed until real resources/records exist.

## Integrity

Check input hashes; disjoint customers; no lost/reordered real payload; no hidden test-label use; complete result grid; models fitted only on training; deterministic predictions; stable old artifacts; numeric/table/PDF consistency. Preserve failures and repairs. No claimed independent human reliability, cross-environment replication, ideal-network guarantee or end-to-end LLM utility can be inferred from this analysis.
