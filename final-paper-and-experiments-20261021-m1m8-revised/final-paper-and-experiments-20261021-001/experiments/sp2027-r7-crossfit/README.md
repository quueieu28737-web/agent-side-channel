# R7 crossfit artifacts

This is a posthoc analysis of the known original 690 Sol episodes. It uses the original R5 customer five-fold split and train-only calibration. The network attack union includes every legacy extended network attack (9) plus the fixed 1D CNN and k-FP-style leaf-distance learner (11 total). All timing values supplied to the new learners are exactly zero. The presence mask only marks existing records.

## Portable prediction verification

From the package root (the directory containing `experiments/`), create an isolated Python 3.12 environment and install this experiment's actual pinned dependencies. The public PyTorch CPU index is included in `requirements.txt`.

```powershell
py -3.12 -m venv .venv-r7-cv
.venv-r7-cv/Scripts/python.exe -m pip install -r experiments/sp2027-r7-crossfit/requirements.txt
.venv-r7-cv/Scripts/python.exe -B experiments/sp2027-r7-crossfit/verify.py
```

On POSIX, use `python3.12 -m venv .venv-r7-cv` and `.venv-r7-cv/bin/python` for the two Python commands. These requirements pin NumPy 2.5.4, SciPy 1.18.1, scikit-learn **1.9.0**, joblib 1.6.0, and torch 2.14.1+cpu. Do not substitute the agent-extension/Luna requirements, which use scikit-learn 1.9.1. The ignored `revision-preview/r7-deps` and `revision-preview/r3/deps` paths used during development are optional local setup details, not prerequisites for readers.

`verify.py` is the portable reproduction entry point. It reloads the independently compressed model bundles, reproduces all saved predictions exactly, refits the complete legacy suite for a second exact check, and checks the original customer split, zero customer overlap, donor provenance, and zero timing columns. `portable-path-map.json` explicitly limits relocation of the old absolute development paths to the same relative paths under this package's `experiments/` directory. Every relocated file must match the SHA-256 in the original frozen manifest. The frozen protocol and input manifest remain unchanged.

`run.py` is the frozen original execution source. Its original protocol equality check includes absolute development paths; it is **not** a portable restart command for a different checkout. For a fresh cross-checkout training run, create a separately named run directory and new protocol, preserving this frozen source and all original artifacts. This development checkout retains historical local paths in its provenance files and is not presented as an anonymous release archive.

`protocol_initial_failed.json` records the initial unsuccessful direction-string adapter. No complete cell bundle or numerical result was saved by that execution; intermediate legacy fits were discarded. `protocol.json` records the corrected frozen run. The fixed adapter maps c2s/s2c to +1/-1 and appends zero timing.

## Outputs

- `predictions.json`: all 4,140 episode/target/condition OOF records and 45,540 attack score/prediction pairs.
- `detailed_results.json`, `RESULTS.md`: every attack's BA/AUROC intervals, the maximum over the complete union, paired decreases, costs, winners, and threshold classifications.
- `f<fold>-<condition>-<prompt>-<target>.zip`: 60 independent trained model bundles, each below 100 MiB. No aggregate model file is required.
- `verification.json`: exact prediction and split audit results.
- `bootstrap_suite_ba.npz`: all common customer-cluster bootstrap suite maxima (point estimate followed by 2,000 draws).
- `table.py --prompt baseline`: emit a main-text LaTeX tabular fragment to stdout; `--prompt all` includes both prompt arms. The generator never edits the manuscript.
- `artifact_manifest.json`: output hashes and file sizes.

Intervals condition on fitted attacks. The suite maximum is reselected over all 11 attacks on every customer-cluster draw. Paired BA decrease is undefended minus defended. This is neither preregistered nor confirmatory evidence.


## Reproducibility dependency-closure erratum

The initial portable source list omitted imported retail/Tau and R6 helper dependencies. `dependency-closure.json` is an explicitly **unfrozen supplement**, containing only 36 existing source/data files whose exact hashes were already bound by the original R4 runtime manifest or R6 frozen attacker manifests. Both experiments import the same R5 retail/Tau and R7/R6 learner helper chain; localization already recorded the four R6 Python hashes in its primary protocol.

`dependency-path-map.json` separately enumerates only these 36 package-relative dependencies and the three original authority manifests. It does not modify the original frozen path map or protocols. The checker rejects paths outside the package and verifies both the file hash and its exact original authority table/key. The R4 runtime manifest SHA is additionally checked against an original hash-verified episode inference fingerprint; the R6 attacker manifest's frozen SHA must match the original R6 frozen manifest.

`verify.py` now performs this check before importing experiment modules. A standalone fast closure check is `python -B dependency_check.py` from this directory. Its receipt is `dependency-verification.json`. The original numerical receipt `verification.json` remains byte-identical; inspect both receipts together. No fitting, predictions, data, model weights, primary frozen source or result files were changed by this erratum. Third-party Python packages must still match the reported runtime environment; this is a repository source/data closure supplement, not an assertion that arbitrary installed package versions reproduce the result.


The closure now also explicitly includes the eight R4 split/protocol/runtime and inference-fingerprint inputs discovered during relocated execution. The five snapshot fingerprint files are checked against the original runtime manifest’s `sp2027-r4` keys under a single fixed snapshot alias; split/protocol use the original scalar SHA fields, and runtime SHA remains bound to a hash-verified original episode. There are 36 dependency entries, including source and non-Python inputs; the runtime manifest is also one of three authority anchors.
