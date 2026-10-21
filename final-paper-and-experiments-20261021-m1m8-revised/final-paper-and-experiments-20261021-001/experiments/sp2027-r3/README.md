# Post-review corrections (R3)

This is post hoc reanalysis, not a new preregistered validation study. R2 raw sessions, captures, registration and historical outcome labels are preserved. Current manuscript tables use R3 for E6/E7 suite intervals and request-only identification.

## Changes

- Refit the fixed R2 attacker suite with the same task-grouped folds. Save all 184 out-of-fold prediction sets.
- Resample tasks jointly across attackers, then recompute maximum BA/AUROC in each of 2,000 bootstrap draws. Percentile intervals condition on fixed predictions; retraining, overlapping-fold dependence, feature search and unknown attacks are outside their coverage. They are approximate descriptive uncertainty, not a calibrated security guarantee.
- Restrict count-rule threshold candidates to training counts.
- Fit request-size-to-tool and majority classifiers on training calls only. Evaluate each of 582 reference calls once per target-stratified partition. Keep in-sample purity separately.
- Fit training-fold shape templates and record held-out overflows. This is a feasibility audit only: defense effectiveness with training-only templates, pools and caps has NOT been rerun.
- Reassess P5 (source protection premise absent) and P7 (no network configuration passes both targets). Do not aggregate judgment counts as framework validation.

## Reproduce

Saved run: Python 3.12, numpy 2.5.4, scikit-learn 1.9.0 and scipy 1.18.1; see run_metadata.json. The script sets native math threads to one before imports. From this directory, run these commands in order:

    python -B reanalyze.py
    python -B make_tables.py
    python -B verify_r3.py

Reanalysis refits classifiers from R2 observations and takes several minutes. Verification only recomputes statistics and tables; no model API, TLS capture or external service is invoked. Regenerated AUROC values can vary slightly across platforms. R3 BA point estimates match R2; interval changes result from recomputing the suite maximum.

## Evidence limits

Defense calibration uses the known public task population and complete reference plans. Database equality under a shadow sandbox is not task-quality or authorization evidence. E8 still contains stand-in planners only. Independent human coding, external compatible/negative scenarios, a checklist baseline and a screened second search remain research work, not completed validation.
