# Complete R4 cohort: incremental supplement

This extends the immutable 663-run release at commit `9e1278bf500034486c025407f51866e0ff0da439`. It completes the original 690-run protocol: 414 train and 276 test episodes, two prompts, three repetitions, GPT-6.1 Sol / low. Final collection concurrency was two. No model, prompt, split, calibration or pre-test analysis was changed.

The original main paper, S14, PDFs and snapshot keep their original denominators. Read `manuscript/main.tex` or the package's `pdf/full-cohort-supplement.pdf` for the full-cohort result. The incremental ZIP requires the base release; it is not a standalone copy of all historical records.

## Contents

- `delta/runs/`: exactly 27 new episode records. All 663 earlier records are reused by hash.
- `delta-model-records.zip`: requests, outputs and attempts for those 27 episodes only. The three original snapshot record ZIPs supply the other 663 episodes.
- `captures.zip`, `sessions.json`: 2,760 full-cohort local TLS replay observations, linked to episode and calibration hashes.
- `results.json`, `predictions.json`: 32 result cells and 176 prediction sets for the full 276-test-episode cohort.
- `inputs.json`: exact old/new membership, base file dependencies, original source mapping and input hashes.
- `validation.json`: original frozen full-cohort verifier receipt.
- `extension_validation.json`: all 11,586 decisions aligned to tools/dialogue, complete state and required-output rescoring, frozen source and capture checks.
- `reproduction_validation.json`: offline reconstruction, exact refit/result equality and original-verifier rerun receipt.
- `release_manifest.json`: all supplement bytes and base dependencies; `verify_release.py` checks it.
- `pipeline_status.json`, `supervisor_status.json`: preserved operational receipts. A historical timeout remains in supervisor metadata; final attempt exited successfully with all 690 complete.

## Main findings

Baseline raw network cancellation/return BA is 97.2%/94.0%; joint shape cover and framing reach 50.0%/50.0%, at 15.39× bytes and 3.83× calls. Rules increase measured workflow compliance from 86.2% to 97.1% but retain raw network BA of 97.2%/93.5%. Reward is 110/138 for baseline and 105/138 for rules. See the PDF for confidence intervals and every ablation.

No condition meets the finite-suite criterion for both targets jointly. Baseline shape-only return meets it for that one target. TLS observations are local replays of actual model trajectories; provider traffic is not measured. Program conditions reuse the same trajectory, so reward equality is structural. This is an author-verified, single-model benchmark extension, not independent external replication.

## Reproduction

Use the preserved Windows/Python 3.12 environment with numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.0, cryptography and pydantic. Frozen source manifests retain original Windows path serialization. Keep this directory next to `sp2027-r4-snapshot-20261023`, `sp2027-r2`, `sp2027-r3`, `reviewer-audit` and `tau-cover-bridge` in the full package. The original local `sp2027-r4` workspace is not required.

From the package root:

    python -B experiments/sp2027-r4-full-20261023/verify_release.py
    python -B experiments/sp2027-r4-full-20261023/verify_extension.py
    python -B experiments/sp2027-r4-full-20261023/reproduce.py --reanalyze

`reproduce.py` without `--reanalyze` reruns the original frozen verifier against saved predictions. With it, the fixed attackers are also refitted and results/predictions must exactly equal the saved JSON objects. Temporary reconstruction reuses source bytes from the base snapshot and its `pretest-source/`; original analysis files are not patched. Repeated source hashing is memoized and all cached files are rehashed at exit. This changes no scientific calculations. Model records and attempts remain in their original ZIPs; temporary request-only archives support the original verifier's request-provenance check. `verify_extension.py` separately checks full model outputs, scoring and alignment.

All commands are offline. Reproducing observations does not require credentials or fresh stochastic inference. Regenerate the supplement source with `publication.py`, then run `pdflatex` twice in `manuscript/`. The base main paper remains 13 body pages; this is a separate completion supplement.
