# Exploratory same-operation result (R8)

## Finding and boundary

The original outcome labels are reference-action categories. This scout instead fixes the observed operation to `return_delivered_order_items`, fixes the requested item count to one, and asks whether its initial-order product belongs to the explicitly frozen 15-name digital-device grouping. It therefore avoids defining the new label by the write-operation name. This does not make the researcher-defined grouping a native benchmark category or a demonstrated real-world secret.

The original 690-episode cohort contains 138 eligible calls in 114 episodes. Exact full-session TLS record reconstruction equals the saved raw socket-replay records, with matching episode SHA, ordered calls and UTF-8 byte lengths; exact per-call slices are available. These are oracle known-call slices, not evidence that a passive observer can automatically locate them. There is no measured timing channel or provider-link capture.

Averaging each prompt/customer/order/item's repeated-call record summaries produces 20 instances per prompt (9 positive, 11 negative), from 15 customers (8 have positives, 9 have negatives, 2 have both). The same 20 instances and their aggregate network features are identical in baseline and rules. These are correlated views of the same customers, not two independent replications. One test fold has no positive customers; all training folds have both classes. Pooled OOF metrics use the frozen original customer folds; there is no mean over fold BA.

## Exact primary results

Both prompts have identical results. The frozen three-model raw suite maximum BA is **30.3030%**, attained by RF, with customer-bootstrap suite-max interval **[16.6667%, 52.7273%]**. Each draw reselects among the same three fitted predictions. The RF-alone interval differs and is retained below. No constant predictor was silently inserted into the three-model raw maximum.

| Original score direction | BA (%) | Fixed-prediction customer 95% CI (%) |
|---|---:|---|
| LR | 25.7576 | [9.7222, 43.7552] |
| RF | 30.3030 | [9.9844, 52.5000] |
| GB | 23.7374 | [5.5556, 40.3869] |

The constant-class LR control is exactly **50% BA [50%,50%]**. Operation-name and canonical constant-size controls provide identical all-zero feature vectors. RF/GB can still give fold-dependent decisions from training composition/ties despite identical within-fold inputs; their full predictions and statistics are retained. No informative observation is available in these controls.

The initial full-order item-count-only diagnostic has suite-max BA **51.5152% [40.6250%,68.7500%]**. The fixed-seed shuffled-label diagnostic has **65.1515% [47.4330%,85.7192%]**, attained by LR. This is one pre-fixed shuffled target, not a permutation distribution, a significance test, or a p-value; its high value illustrates that this tiny grouped cohort can produce unstable apparent classification. It does not validate a null hypothesis.

Below-chance BA does not establish an absence of information or defense effectiveness; reversed associations may exist. Scores and labels retain their frozen original orientation, with no post-result flipping, tuning, target replacement or extra attack search. These results **cannot confirm inference of this non-action attribute and do not prove an absence of such leakage**. They provide no general defense ranking.

## Confounding and uncertainty

Per prompt, initial whole-order item-row counts 1/2/3/4/5 have instance counts 6/3/2/7/2 and positive counts 3/0/1/5/0. The corresponding negative counts are 3/3/1/2/2. Thus fixing the requested item count does not balance full-order size. Cells with two or five order items have no positive instance, and customer support in every cell is small. No matched adjustment is fitted after observing these results. `confounding_support.json` includes exact counts; customers may occur in multiple size cells.

Bootstrap intervals condition on the fixed fitted models and sample customers with replacement (2000 seed-fixed draws), weighting each retained item instance equally within sampled customers. They do not account for attacker training uncertainty, target-grouping choice, or broader population sampling. One-class draws are omitted and their valid count is recorded. The raw suite-max upper bound near chance is not a calibrated security threshold.

## Reproduction and evidence

`protocol.json` was written before fitting and binds source/input SHA-256; protocol SHA is `c2c7c67363f80a89c5df947380e7f0716196844ce4365a2b9770fd732d28ad59`. `verification.json` separately confirms sources, labels, customer separation, repeat aggregation, 150 saved model reloads, 600 exact scores, denominators, BA and every bootstrap interval. `descriptive_metrics.json` adds original-direction AUROC with customer-bootstrap intervals and every fold's scores/BA/AUROC; one-class fold metrics are null, not zero. `descriptive_verification.json` records positive score-column class checks and two-class training support. `make_table.py` prints a standalone suggested LaTeX table without changing the manuscript. Models are approximately 7.4 MB, below the 100 MiB per-file limit.

## Suggested main-text paragraph (English)

As an exploratory check beyond operation-category labels, we fixed the observed operation to single-item returns and predicted membership in a frozen, researcher-defined digital-device product grouping. The retained known cohort comprised only 20 customer–order–item instances from 15 customers per prompt (9 positive and 11 negative instances); repeats were aggregated and the original customer folds retained. The fixed LR/RF/GB suite attained 30.3% pooled OOF BA (customer-bootstrap suite-max 95% CI, 16.7–52.7%), compared with 50% for a constant-class predictor. A single fixed shuffled-label control reached 65.2%, underscoring instability rather than providing a permutation test. These small, posthoc results neither confirm non-action-attribute inference nor establish an absence of leakage.

## Suggested supplementary subsection (English)

Same-operation semantic-attribute scout. We used only exact known-call TLS-record slices for `return_delivered_order_items` requests containing one item ID, with the item resolved against the saved initial order of the episode customer. The binary target is membership in the explicitly listed 15-name digital-device set; the benchmark supplies product names but no broad category taxonomy. Source hashes and protocol/code were frozen before fitting three fixed learners. Within each prompt, record count/total/max/min in each direction were averaged across repeated calls sharing customer, order and item; identifiers, plaintext and timing were excluded. The unchanged five customer folds supplied pooled OOF predictions, and the reported percentile intervals resample customers conditional on fixed predictions. Original-direction per-learner BA, AUROC, every fold score and training support are retained. Operation-only and canonical constant-size inputs are constant, and initial whole-order item count is reported as a confounder. Baseline and rules yield identical aggregate features and do not constitute independent replications. The single shuffled-label run is a sanity diagnostic, not a permutation distribution or p-value. Severe small-sample support and unbalanced order-size cells preclude confirmatory attribution, generalized defense claims or a no-leakage conclusion.
