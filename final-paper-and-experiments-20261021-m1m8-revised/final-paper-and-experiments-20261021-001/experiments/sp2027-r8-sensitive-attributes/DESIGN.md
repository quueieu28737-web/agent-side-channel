# R8 same-operation sensitive-attribute feasibility (design only)

Status: awaiting root approval. Posthoc scout of the existing known Sol cohort; no attacker trained, traffic-length/target association inspected, saved attacker predictions opened, or LLM called. No old frozen inputs or manuscript changed.

## Source and original label audit

Original `sp2027-r4-snapshot-20261023/collect.py:124–128` obtains `has_cancel` / `has_return` from reference `task.actions` names. They are expected action categories, not labels extracted from observed episode calls. Thus E12 can localize operation-class information, but does not establish inference of an attribute independent of operation type.

The cohort remains 690 episodes = 115 tasks × 2 prompts × 3 repeats, spanning 53 customers. These are not 690 independent customers or fresh observations. `source_inventory.json` records native schemas and input SHA-256 values. `task_action_inventory.json` records reference actions; `episode_metadata.json` records actual call names/kwargs/errors, without packet lengths. Sources are the existing vendor tasks_test.py and initial orders/products/users JSON. Initial order items provide item_id, product_id, name, price and options; products provide native product names. Orders provide status, address, fulfillment and payment history; users provide name, email, address, orders and payment methods. None provides a benchmark-native broad product-category field. IDs are linkage keys, never proposed attacker features.

## Proposed fixed target, subject to approval

Primary stratum: actual `return_delivered_order_items` calls requesting exactly one item ID, with an initial order owned by that episode's task customer and all requested IDs resolvable in that initial order. Target: whether the selected initial-order product is in the explicit digital-device name set in `attribute_availability.json`. The 15-name mapping is a transparent researcher-defined semantic grouping, not a preexisting dataset category or validated sensitive taxonomy. Negative means all other native names. All names are fixed before any predictive evaluation. No search over mappings by attack performance is permitted.

Native product names can instead be reported descriptively; their small independent-customer support does not justify selecting a single native category for a strong inference claim. State, payment and price thresholds would introduce additional arbitrary target choices. Initial order status is effectively operation-associated and should not be presented as an independent sensitive target.

| Same operation, one requested item | Actual call rows | Tasks | Customers | Positive / negative / mixed customers | Distinct customer–order–item instances, positive / negative |
|---|---:|---:|---:|---|---|
| Return | 138 | 20 | 15 | 8 / 9 / 2 | 20, 9 / 11 |
| Modify pending items | 181 | 28 | 17 | 6 / 12 / 1 | 21, 7 / 14 |
| Exchange | 140 | 23 | 13 | 5 / 8 / 0 | 17, 6 / 11 |

Positive/negative customer sets overlap for mixed customers; their sum is not the number of customers. Rows contain repeats and sometimes repeated calls; instance counts collapse prompt, task and repeat for the same customer/order/item. All eligible single-item calls have no saved call error, which is a cohort property rather than a success-only filter. Wider operation inventory and alternative label counts are in `attribute_availability.json`. Six modify-item calls reference an order owned by a different task customer and are excluded explicitly; 59 modify-user-address calls have no order and cannot support this order/product target. Gold exchange task106 requests one item ID twice; multiplicity is retained in kwargs and excluded from the exactly-one-requested-item stratum, not misclassified as a missing catalog item.

## Grouping and estimand

Reuse the frozen R5 customer-to-fold assignment recorded in R7 C/protocol.json; no rebalancing after target counts. All tasks/orders/items/repeats/prompts of one customer stay in one fold. Analyze baseline and rules separately. Within a prompt, collapse repeat calls for the same customer/order/item before reporting primary metrics; do not weight repeatedly executed actions as independent evidence. Report customer-cluster uncertainty and raw customer/instance denominators. This is a small exploratory known-cohort analysis, not confirmation or a general privacy-risk estimate.

For return, pooled test-fold positive/negative customer counts are (1,2), (3,2), (3,1), (1,1), (0,3). Training counts are (7,7), (5,7), (5,8), (7,8), (8,6). All training folds contain both classes; one test fold lacks positives. Only pooled OOF metrics could be meaningful, with weak precision; no mean of fold BA or claim that each fold validates a classifier. Modify and exchange have further one-class test folds; details including per-prompt counts are in `fold_feasibility.json`. These are candidate replication strata only, not additional independent cohorts.

## Observer and negative controls, before fitting

Use only the request/response record projection for one known operation call, with exactly one requested item. Exclude plaintext names, arguments, identifiers, task IDs and customer IDs from attacker features. There is no measured timing channel in these R5 records; any timing slot is a constant zero mask and must be declared. Full-task traffic would be secondary because intent, other operations and catalog reads could confound interpretation. Verify that call-to-record alignment is available before any fitting; otherwise report the projection unavailable and do not substitute guessed traces.

1. Operation-name-only control is constant inside each stratum; it cannot distinguish the attribute. A constant-size request/response surrogate should also have identical observations for every instance. This checks the definition, not observed predictive performance.
2. Fix requested-item cardinality at one; report and, where possible, condition on initial order item count. Whole-order cardinality is a confounder even when one item is selected. Do not tune matching choices by prediction effects.
3. Predefine a fixed-seed instance-label permutation control within the existing fold/operation, propagate its label to all repeats/prompts of an instance, and explicitly call it a shuffled-label sanity check rather than an independent null sample. Mixed-attribute customers mean permutation cannot be described as customer-label permutation. Keep customer-cluster inference and label-shuffle limitations explicit.
4. Compare original with a train-only calibrated constant-size projection if approved; any evidence is restricted to the chosen within-operation product grouping in this environment. No universal defense ranking follows.

## Recompute counts

Run the standard-library scripts in order: `python inventory.py`, `python availability.py`, `python fold_feasibility.py` from any working directory. They resolve paths relative to their own directory. Generated JSON is feasibility metadata only. No model, length-distribution summary or prediction evaluation is authorized by this design. Further analysis awaits approval.
