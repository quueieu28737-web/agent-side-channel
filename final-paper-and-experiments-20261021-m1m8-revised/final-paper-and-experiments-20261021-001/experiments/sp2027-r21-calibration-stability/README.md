# R21: calibration source versus training-customer sensitivity

This post hoc experiment addresses M2. Original R14 data and predictions are immutable. No LLM generation, customer collection or outcome-dependent resampling is performed.

## Question and falsifiable interpretation

The earlier GLM contrasts (+20.8 cancellation / -17.3 return BA points) do not imply that imported calibration is uniformly worse. The question is whether a source-calibration change can be distinguished from the local pipeline's training-customer sensitivity. If local recalibration or attack refitting moves BA by comparable amounts, we cannot attribute the observed contrast to model source alone. A nonmonotone point estimate is not a significant interaction test.

## Frozen design

`protocol.json` was written before the new results. It records the original inputs and run source hashes, 100 predetermined seeds, the seven-attack suite, contrasts and inference rules. The first replicate is part of the 100; it was used to measure runtime, not to choose the sample size. There are 29 training customers and 24 disjoint test customers (69 and 46 original tasks); both endpoints use the same customer partition.

For each replicate:

1. Draw 29 training customer IDs with replacement, retain all tasks for every selected customer, and use the same draw for both source endpoints. Cluster sizes vary; a replicate need not contain exactly 69 training episode occurrences. Rebuild the original template, donors and caps. The original donor deduplication and deterministic cover seeds are retained. The saved donor pool ordering follows the resampling order, as in the unchanged calibrator.
2. Apply both calibrations to all 115 trajectories of both target endpoints. Capture 460 actual TLS 1.2 loopback sessions per replicate, saving lengths, directions, tool labels for training the decoder, and byte/call costs. No generated timing or inferred record-length substitution is used.
3. Refit all seven attacks using the original target training population (calibration-only sensitivity).
4. Draw an independent training-customer bootstrap, shared across conditions/endpoints. Refit the suite using it (joint calibration/attacker sensitivity). Also refit on the original local-calibration captures to isolate attacker-training sensitivity.
5. Keep the original 46 target test tasks fixed for training-sensitivity spreads. Separately take 20 paired customer bootstrap draws per training replicate for exploratory joint train/test sampling intervals. Reselect both suite maxima on every draw. Exclude and count undefined single-class test draws; never redraw them. Single-class training fits use constant predictions, retaining their draws.

The resulting training-sensitivity percentile ranges are descriptive spreads on the fixed test population, not confidence intervals for a new population. The optional 100 x 20 joint bootstrap reuses observed customers and is not a confirmatory study. There is no claim of fixed-weight, independent-provider or new-customer replication.

## Original eight contrasts and multiplicity

The original table contains **eight** target-level contrasts: two target endpoints x two comparisons (imported joint / write-only padding versus local joint) x two targets. For each contrast, swap the *entire seven-attacker prediction vector* between conditions within each test customer; keep all of that customer's tasks together and reselect the maxima. Use 99,999 seeded Monte Carlo swaps, the two-sided absolute max-BA difference and `(extreme + 1)/(draws + 1)`. Apply Holm's step-down correction to all eight p-values. This tests conditional prediction-vector exchangeability, not a randomized causal model-source intervention. It does not remove attacker-training uncertainty; the separate resampling experiment addresses that component.

Implementation references: [SciPy paired sample permutation documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html) and [statsmodels Holm correction source](https://www.statsmodels.org/stable/_modules/statsmodels/stats/multitest.html). The implementation enumerates a synthetic clustered case as a check. It reproduces all 84 original attacker prediction arrays (12 rows x seven attacks) before using the new results.

## Reproduction

Use Python 3.12 and the numerical dependency versions recorded in `environment.json`, with the same dependency paths as the archived R12/R14 studies (NumPy, SciPy, scikit-learn). No API credentials are needed.

```
python run.py run --workers 8
python verify_baseline.py
python verify_statistics.py
python verify_predictions.py
python analyze.py conditional
python analyze.py aggregate
```

`run.py freeze` is a one-time protocol creation step and refuses to overwrite it. Completed replicates are cached, with no selective repetition. The source and historical inputs are checked before resume. `replicates/` saves calibration and prediction outputs; `captures/` saves compressed TLS sessions. `summary.json`, `conditional_tests.json` and verification receipts support the paper's revised statements.
