# Timing boundary and statistical power

The appended analysis algorithms and configuration were frozen at formal run 44/150, before any formal test trajectory output was available. The collection plan itself was frozen before formal collection. The appended algorithms do not change that original plan.

The implementation deliberately waits until all 150 trajectories are collected before executing calibration and analysis. Calibration parameters will therefore be fitted after Luna test collection, using only the fixed 58 training trajectories. They must not be described as parameter values frozen before Luna test collection. Calibration/analysis output timestamps and process logs are retained. No test examples or results are used to select caps, templates, donors, features, classifiers or thresholds.

The calibration pool has 58 trajectories (29 tasks x 2 prompts, 10 existing customers). Each fixed attacker is fitted separately by prompt/condition on 29 training trajectories and evaluated on 46 test trajectories (24 disjoint existing customers). The test has only five cancellation-positive and seven return-positive customer clusters.

The inherited HistGradientBoostingClassifier uses min_samples_leaf=20. With 29 samples per model and a minimum of 40 samples to form two leaves, the fixed classifier is expected to emit constant scores. Its defaults are retained, and actual constant-score/prediction proportions will be reported from every retained D2/network prediction entry. The suite includes the majority control, fixed logistic regression, and the inherited network decoding/count attackers. Constant gradient-boosting outputs are a limitation of the small training cohort, not evidence that leakage is absent.
