# E14: expanded attacks and classical traffic controls

This directory is a post hoc analysis of the completed Sol cohort. It contains **no new LLM decisions or measured network sessions**. It adds new fitted attacks to E13's measured captures and constructs explicit offline WF adaptations from its undefended captures.

## Inputs, outputs and inference

- Input: all 690 Sol trajectories, the original customer-disjoint 414/276 split, and E13 `captures.zip` / saved attacker predictions.
- Transformed grid: 13 conditions × 690 trajectories = 8,970 rows, including six measured and seven simulated conditions. The two prompt arms and two intent targets produce 52 evaluation cells.
- New learners: logistic regression, gradient boosting, random forest, extra trees, k-FP-style leaf fingerprints and a trained 1D-CNN, plus a majority control. The full original E13 suite is retained on measured conditions.
- `results.json` reports every suite maximum, customer-cluster interval, strongest learner, truncation count, resource cost and absolute-criterion outcome. No cell passes the original absolute criterion.
- `PROTOCOL.md`, `freeze.json`, `calibration.json` and `fit_complete.json` preserve the before-fit configuration. The test cohort had already been analyzed in E13. `ERRATA.md` clarifies metadata-fragment conservation and the extended power-planning grid without changing frozen bytes.
- `models.zip` contains the 52 fitted model packs. `model_archive_manifest.json` verifies every uncompressed model hash against the original fit receipt. Joblib/PyTorch models should only be loaded from a trusted source.
- `validation.json` checks the complete grid, disjoint customers, source/data hashes, deterministic transformation reproduction and metric reproduction. `retraining_validation.json` records a separate refit of all 312 new learned models and exact prediction comparison.
- `common-suite.json` re-evaluates the saved predictions under exactly the same seven models in every condition. The strongest-available unions contain 17–22 models for measured conditions and seven for offline controls, so a direct dominance interpretation across those unequal unions is invalid. The cost plot uses the common seven; gray upper endpoints retain full-union maxima. The single passing subset cell does not override its failing full-union assessment.

## Reproduce without calling an LLM

Use Python 3.12 and the package versions recorded in `freeze.json` (including NumPy, scikit-learn and CPU PyTorch). `requirements.txt` lists the exact numerical dependencies and Matplotlib for plot checks. Use a separate environment from the Luna extension, whose recorded scikit-learn version differs. After activating a Python 3.12 virtual environment, run from this directory:

```text
python -m pip install -r requirements.txt
python -B verify.py
python -B run.py reproduce
python -B power.py --check
python -B report.py --check
```

To refit every learned model in memory and compare its predictions with the saved output, run from the package root:

```text
python -B provenance/r7-review/retrain_robustness.py
python -B provenance/r7-review/common_suite.py --check
```

`prepare` and `fit` are creation commands and deliberately refuse to overwrite an existing freeze or completed fit. Reproduction uses the archived models directly. All commands above are local; none collects new model/API runs.

## Interpretation

The main contribution of this comparison is identifying which clock and execution boundary a measured reduction covers. The WF adapters preserve abstract fragment size/direction/order metadata and execute no dummy tools. Their simulated schedule span begins at the first input record. E13 latency begins at the measured RPC origin. Plot panels keep these time semantics separate. The byte/BA frontier is descriptive for the tested settings, with no certified or global dominance claim.

`IMPLEMENTATION.md` supplies the primary-source references and exact differences from Tor/WF implementations. `power.json` is a binomial design sensitivity under explicit population assumptions, not the empirical power of the heterogeneous customer bootstrap. No new independent customer, cross-vendor model, human coder or live LLM replanning result is implied by this directory.
