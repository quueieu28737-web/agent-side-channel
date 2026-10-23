# R4 immutable completion snapshot — 2026-10-23

This is an interim release of real GPT-6.1 Sol / low agent episodes. The original collection continues outside this directory. Do not overwrite this snapshot with later runs.

## Cohort

- Planned: 115 tasks × two prompt arms × three repeats = 690 episodes.
- Fixed cutoff: 2026-10-23 10:01:03 UTC; 663 episodes completed (414 train, 249 test).
- Primary: all 69 training tasks and all 41 test tasks with the full six-cell prompt/repeat grid; 660 episodes total, 246 test episodes, 22 test customers.
- Three additional complete test episodes from task 105 are preserved; 27 runs were incomplete. Selection uses completion status at cutoff, never reward or leakage. Late-task composition can affect generalization.
- All 414 training runs preceded calibration freezing and the first test inference. The original split and calibration remain byte-identical; analysis_split.json selects complete test tasks without changing training.

## Results and files

results.json contains all 32 target/view/prompt/program cells, suite maxima, intervals, paired prompt differences and utility. predictions.json retains 176 fitted-attacker prediction sets. sessions.json and captures/ retain 2,640 TLS loopback sessions. runs/ contains all 663 complete episode records. completion_summary.json accounts for the additional three episodes.

The model chose structured actions from public policy, schemas and real sandbox observations. Reference plans were used only for scoring. No host tools were available to the model. The same model supplied a separate user-simulator context. The network measurement is local replay, not provider traffic.

The program conditions preserve the original trajectory and reward by construction. Baseline intent BA falls from 96.7%/93.4% to 50.0%/50.0% with online shadow cover plus constant framing, at 15.33× bytes and 3.83× calls. Rules reach 96.7% measured workflow compliance but retain 96.7%/92.8% network BA. Customer-cluster intervals remain too wide to certify joint protection.

## Validation and reproduction

Validated runtime: Windows, Python 3.12.14, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.0. cryptography and pydantic are also required by the preserved sandbox/TLS helpers. Original runtime details are recorded in runtime_manifest.json. Native path entries reflect the original Windows execution.

From the package root:

    python -B experiments/sp2027-r4-snapshot-20261023/verify_snapshot.py

The final receipt is validation.json. This verifies original code/runtime and pretest hashes, all episode membership and model fingerprints, model records, training-only recalibration, sandbox state and required-output scoring, online cover reconstruction, TLS accounting, sklearn point metrics, customer-cluster suite intervals and paired contrasts. A read cache avoids repeated hashing of immutable files and rechecks every cached input before emitting the receipt. The cache changes no scientific calculations.

To reproduce the offline analysis from preserved trajectories:

    python -B experiments/sp2027-r4-snapshot-20261023/defense.py capture --workers 8
    python -B experiments/sp2027-r4-snapshot-20261023/evaluate.py
    python -B experiments/sp2027-r4-snapshot-20261023/verify_snapshot.py
    python -B experiments/sp2027-r4-snapshot-20261023/publication.py

These commands do not invoke the model. Existing captures are validated and reused. Conduct fresh transport captures in a copy of the release. Fresh stochastic model generations cannot be guaranteed from a mutable alias and require a separate new collection, not an in-place overwrite. Operational collectors included for provenance are not release rebuild commands.

## Frozen protocol and amendment

protocol.json, split.json, calibration.json and inference source files are unchanged. The original pretest analysis is preserved in pretest-source/. The derived defense/evaluation code changes only primary cohort membership and exact grid assertions; the verifier adds required-output scoring and independent structured-state comparison (verification_amendment.json). All 663 episodes are additionally aligned to their actual model decisions. snapshot_amendment.json records the user-authorized publication cutoff before attack analysis and hashes every completed episode. analysis_source_hashes.json binds derived sources. No Luna episode is in the formal cohort.

model-records-baseline.zip and model-records-rules.zip contain requests, outputs and attempts for the 660 primary episodes. additional-completed-records.zip contains the other three. historical-pilots-and-failures.zip preserves excluded pilots and completed recovery logs. Protocol/model/transport amendments explain the earlier Luna pilot and switch to a fresh Sol cohort. Inference remains Sol / low; scheduling concurrency changed during collection, most recently to 2. Repetition IDs are not provider random seeds.

The immutable snapshot preserves operational evidence without turning connection errors or recovery logs into paper findings. Independent external replication, native provider-traffic measurement, online delay/feedback effects and multi-model generalization are outside this release.
