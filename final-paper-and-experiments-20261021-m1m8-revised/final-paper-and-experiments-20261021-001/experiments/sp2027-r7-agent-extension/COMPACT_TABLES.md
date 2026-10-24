# Luna extension compact tables

Model requested/returned: gpt-6-luna; effort low. 150 runs=75 existing tasks x2 prompts, one repetition; convenience subset, 34 existing customers. Ten pilot runs excluded.

| Prompt | Reward | Wallclock p50/p95 s | Known-name dispatch/model calls | Tool errors | Infra/timeout/retry |
|---|---:|---:|---:|---:|---:|
| baseline | 32/75 | 92.52/158.98 | 498/1530 | 36 | 0/0/0 |
| rules | 33/75 | 92.52/175.50 | 505/1542 | 37 | 0/0/0 |

Known-name dispatch attempts include env.step errors; they are not successful executions. Total dispatch/unknown counts are separate in compact_manifest.json. Network dispatch ratios include unknown/errors/cover. Public ZIP recomputation requires the fixed checkout/vendor benchmark and pinned dependencies; ZIP alone is not self-contained.

D2 dispatch suite: majority/logreg/gboost; per prompt 29 train/46 test, 10/24 customers. Test positive customer clusters 5 cancel/7 return. Max reselected each customer bootstrap draw; fixed fit uncertainty excluded.

| Target | Prompt | View | BA [95% CI] | AUROC | Valid draws |
|---|---|---|---|---:|---:|
| cancel | baseline | all | 0.783 [0.500, 0.963] | 0.829 | 1994/2000 |
| return | baseline | all | 0.632 [0.500, 0.784] | 0.691 | 2000/2000 |
| cancel | baseline | writes-only | 0.875 [0.811, 0.946] | 0.925 | 1994/2000 |
| return | baseline | writes-only | 0.666 [0.536, 0.805] | 0.769 | 2000/2000 |
| cancel | baseline | reads-only | 0.500 [0.500, 0.643] | 0.500 | 1994/2000 |
| return | baseline | reads-only | 0.570 [0.500, 0.742] | 0.522 | 2000/2000 |
| cancel | rules | all | 0.738 [0.500, 0.980] | 0.850 | 1994/2000 |
| return | rules | all | 0.675 [0.500, 0.822] | 0.782 | 2000/2000 |
| cancel | rules | writes-only | 0.892 [0.671, 1.000] | 0.917 | 1994/2000 |
| return | rules | writes-only | 0.778 [0.602, 0.926] | 0.906 | 2000/2000 |
| cancel | rules | reads-only | 0.508 [0.500, 0.632] | 0.500 | 1994/2000 |
| return | rules | reads-only | 0.573 [0.500, 0.752] | 0.564 | 2000/2000 |

Network suite: full inherited fixed R4 family on local TLS replay. Defense calibration pools 58 train trajectories; each attacker fits 29 per prompt. No live replan/provider-transport claim.

| Target | Prompt | Condition | BA [95% CI] | AUROC | Dispatch/wire ratio | Criterion |
|---|---|---|---|---:|---:|---|
| cancel | baseline | raw | 0.642 [0.500, 1.000] | 0.642 | 1.00/1.00 | inconclusive |
| cancel | baseline | padding_only | 0.504 [0.500, 0.698] | 0.567 | 1.00/3.98 | inconclusive |
| cancel | baseline | shape_only | 0.583 [0.500, 0.700] | 0.767 | 3.91/4.25 | inconclusive |
| cancel | baseline | shape_const | 0.604 [0.500, 0.720] | 0.623 | 3.91/15.57 | inconclusive |
| cancel | rules | raw | 0.654 [0.583, 1.000] | 0.667 | 1.00/1.00 | inconclusive |
| cancel | rules | padding_only | 0.575 [0.500, 0.811] | 0.542 | 1.00/3.95 | inconclusive |
| cancel | rules | shape_only | 0.558 [0.500, 0.774] | 0.579 | 3.95/4.26 | inconclusive |
| cancel | rules | shape_const | 0.592 [0.500, 0.725] | 0.569 | 3.95/15.58 | inconclusive |
| return | baseline | raw | 0.849 [0.722, 1.000] | 0.851 | 1.00/1.00 | above_threshold |
| return | baseline | padding_only | 0.500 [0.500, 0.564] | 0.531 | 1.00/3.98 | meets_evaluated_suite_criterion |
| return | baseline | shape_only | 0.545 [0.500, 0.643] | 0.500 | 3.91/4.25 | inconclusive |
| return | baseline | shape_const | 0.570 [0.500, 0.714] | 0.595 | 3.91/15.57 | inconclusive |
| return | rules | raw | 0.909 [0.714, 1.000] | 0.909 | 1.00/1.00 | above_threshold |
| return | rules | padding_only | 0.500 [0.500, 0.709] | 0.500 | 1.00/3.95 | inconclusive |
| return | rules | shape_only | 0.591 [0.500, 0.750] | 0.500 | 3.95/4.26 | inconclusive |
| return | rules | shape_const | 0.500 [0.500, 0.571] | 0.500 | 3.95/15.58 | meets_evaluated_suite_criterion |

Luna reads-only keeps get_/find_/list_ only. It differs from Sol E12 no_writes complement; think/calculate/handoff/unknown tools can be outside both Luna read/write views. All retained/excluded tool names and counts are saved in D2_view_call_counts.json.

Gradient boosting default min_samples_leaf 20; 29 training rows cannot form two leaves. Actual per-entry constant-score fractions: {"D0_gboost": {"models": 32, "constant_score_models": 32, "constant_score_fraction": 1.0, "constant_prediction_models": 32}, "D2_gboost": {"models": 44, "constant_score_models": 44, "constant_score_fraction": 1.0, "constant_prediction_models": 44}, "network_decode_gboost": {"models": 16, "constant_score_models": 16, "constant_score_fraction": 1.0, "constant_prediction_models": 16}}.

Algorithm/config frozen before test outputs; fitted calibration parameters computed after complete collection on training only. No cross-provider/new-customer/independent-human validation claim.
