CURRENT REVISION ARTIFACTS

recompute.py tls: local TLS1.2 framing replay and topic-cluster statistics.
recompute.py retail: pinned retail tool replay plus task-cluster observer statistics.
recompute.py scenarios: confusion matrices from supplied author-scenario annotations.
retail_replay.py: instrumented copy of the historical suite used as an import library.

tls_records.json: per-output observed framing, splits, labels, hashes; 24 regime/policy conditions.
tls_gradient.json: absolute bytes/counts and workload-matched cost ratios.
tls_cap.json: training-only length parameter and overflow definition. socket_connections describes the gradient replay cache before additional adaptive first draws.
tls_adaptive*.json: summaries and per-topic/output/draw correctness; 50 stochastic draws.
retail_units.json: 6210 rows, 115 tasks, 3 seeds, 2 positions, 9 policies; ordered dispatch names and response lengths include failures.
retail_utility.json: three reference-state scopes; native_reward is a historical field name for DB equality, not the full evaluator.
retail_observers.json: task-bootstrap accuracy/BA, conditional AUROC, unit confusion matrices, paired gain; 48/49 task split.
retail_predictions.json: every held-out prediction and label, including rules.
retail_diagnostics.json: exact class counts, split task IDs, tool errors and preserved-state unit counts.
same_item_price_check.json: zero-price-difference check on initially successful same-item selections.
combined_result_records.json: 33 historical scoped records plus six explicit expansion records (39 records, 26 families); distinct from the 20-family reporting audit.
scenario_confusions.json: author-constructed scenario illustration; no external-validity claim.

Reproducibility is conditional on the saved source/data and scripts. No fresh model call or production API is made. Historical summaries under revision-m1-m8 remain unchanged and may differ from corrected values. No independence or human-review attestation is inferred from supplied annotation columns.
