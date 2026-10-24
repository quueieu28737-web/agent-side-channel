# R7 strengthened E12 oracle localization

Independent posthoc extension of the known original 690 Sol episodes. `PLAN.md` and `protocol.json` fix the original R5 customer five-fold split, exact original E12 oracle filtering, all nine legacy network attacks, fixed CNN and k-FP-style learner (11 attacks), and 2,000 customer-cluster bootstrap draws with suite maximum reselected in every draw. The standard prompt is `baseline`; `rules` is the independent rule arm.

The oracle retains only true write exchanges (`writes_only`) or removes all such exchanges (`no_writes`, reads only), then reconstructs raw TLS records using the original analytic model. True call names define the oracle filter. These are diagnostic ablations, not a deployable defense. No new model API calls or captures are used. All third timing values are zero; the presence mask only indicates existing records.

The full-view OOF predictions are reused from the preceding verified R7 crossfit undefended cells. Their original prediction and verification hashes are fixed in this independent protocol. All new models are fitted only on the other four customer folds. There is no defense calibration for these undefended oracle views.

## Reproduction

From the package root (the directory containing `experiments/`), create an isolated Python 3.12 environment and install this experiment's actual pinned dependencies. The public PyTorch CPU index is included in `requirements.txt`.

```powershell
py -3.12 -m venv .venv-r7-cv
.venv-r7-cv/Scripts/python.exe -m pip install -r experiments/sp2027-r7-localization/requirements.txt
.venv-r7-cv/Scripts/python.exe -B experiments/sp2027-r7-localization/verify.py
```

On POSIX, use `python3.12 -m venv .venv-r7-cv` and `.venv-r7-cv/bin/python` for the two Python commands. These requirements pin NumPy 2.5.4, SciPy 1.18.1, scikit-learn **1.9.0**, joblib 1.6.0, and torch 2.14.1+cpu. Do not substitute the agent-extension/Luna requirements, which use scikit-learn 1.9.1. The ignored `revision-preview/r7-deps` and `revision-preview/r3/deps` paths used during development are optional local setup details, not prerequisites for readers.

All hashes in the new protocol are relative to the package root. Verification rejects resolved paths outside that root and requires the original exact SHA-256. The original crossfit provenance files remain unchanged, including their historical development paths; this development checkout is not an anonymous archive.

`verify.py` checks 40 independently compressed model bundles, all 2,760 new OOF records and 30,360 attack score/prediction pairs. It reloads the saved models, refits the complete legacy suite, checks exact original E12 call/record filtering, original customer folds and zero train/test overlap, duplicates and original labels, and the zero timing channel. No model file exceeds 100 MiB.

`detailed_results.json` and `RESULTS.md` include all 12 full/reads/writes × prompt × target rows, per-attack and full-union BA/AUROC intervals, winners and paired full-minus-filtered differences. `retained_fraction.json` records the fraction of call and wire information retained by the oracle; these are diagnostic retained-information fractions, not a deployment cost reduction claim.

`table.py` emits a two-row baseline main-table tabular to stdout. `table.py --detail` emits all rows for S21; neither changes the manuscript. Generated local fragments are `main_table.tex` and `s21_table.tex`. `artifact_manifest.json` records all artifact hashes and sizes. Intervals condition on fitted attacks. This extension is neither preregistered nor confirmatory.

## Reproducibility dependency-closure erratum

The initial portable source list omitted imported retail/Tau and R6 helper dependencies. `dependency-closure.json` is an explicitly **unfrozen supplement**, containing only 36 existing source/data files whose exact hashes were already bound by the original R4 runtime manifest or R6 frozen attacker manifests. Both experiments import the same R5 retail/Tau and R7/R6 learner helper chain; localization already recorded the four R6 Python hashes in its primary protocol.

`dependency-path-map.json` separately enumerates only these 36 package-relative dependencies and the three original authority manifests. It does not modify the original frozen path map or protocols. The checker rejects paths outside the package and verifies both the file hash and its exact original authority table/key. The R4 runtime manifest SHA is additionally checked against an original hash-verified episode inference fingerprint; the R6 attacker manifest's frozen SHA must match the original R6 frozen manifest.

`verify.py` now performs this check before importing experiment modules. A standalone fast closure check is `python -B dependency_check.py` from this directory. Its receipt is `dependency-verification.json`. The original numerical receipt `verification.json` remains byte-identical; inspect both receipts together. No fitting, predictions, data, model weights, primary frozen source or result files were changed by this erratum. Third-party Python packages must still match the reported runtime environment; this is a repository source/data closure supplement, not an assertion that arbitrary installed package versions reproduce the result.


The closure now also explicitly includes the eight R4 split/protocol/runtime and inference-fingerprint inputs discovered during relocated execution. The five snapshot fingerprint files are checked against the original runtime manifest’s `sp2027-r4` keys under a single fixed snapshot alias; split/protocol use the original scalar SHA fields, and runtime SHA remains bound to a hash-verified original episode. There are 36 dependency entries, including source and non-Python inputs; the runtime manifest is also one of three authority anchors.
