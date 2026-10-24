# R8 saved-OOF customer sensitivity

This separate post hoc analysis changes neither the previous frozen experiments nor their reported estimand. It uses the complete 4,140 saved episode/condition/target records from `../sp2027-r7-crossfit/predictions.json`, with the original 11 attacks' binary predictions fixed. There are no LLM calls, fits, calibration updates or new customers.

## Denominators

Each prompt/condition/target cell has 345 trajectories = 115 tasks × 3 repeats, on **53 unique customers**. The two prompts use the same customers; conditions and targets reuse the same episodes. Thus 690 model runs do not mean 690 independent customers, and summing the twelve sensitivity-cell sample sizes would be incorrect.

Across the full OOF cohort, cancellation has 54 positive episodes = 18 tasks / **14 positive customers**, including four mixed-label customers. Return has 96 positive episodes = 32 tasks / **18 positive customers**, including eight mixed-label customers. These full-cohort counts must not be confused with the original heldout subset's five/seven positive customers. A customer is positive if at least one task has the target label; its other tasks can be negative.

## Definitions

Original BA pools episodes within each true class, then equally averages class recall. Customer-equal BA first averages correctness per customer within each true class, then equally averages the class-specific customer means and finally both class rates. A mixed-label customer contributes independently to both class averages. This changes the estimand; it is not a correction proving the original was invalid. All eleven attackers are evaluated, with the suite maximum independently reselected under each weighting.

Each positive-customer deletion removes that customer's entire set of episodes, including negative tasks, and reselects the maximum over the same saved attacks. There are 14 valid deletions per cancellation cell and 18 per return cell: 192 total. The minima/maxima are deterministic influence ranges, **not confidence intervals**. The fitted models are not retrained after a customer is removed; training influence is still present in other OOF folds. These sensitivity results remain conditional on fitted attacks and do not account for retraining uncertainty, independent-population uncertainty, or previous access to the public tasks.

We omit a single mean-score customer classifier because mixed-label customers do not have one unique task-intent label. No post hoc rule assigns them a dominant label or excludes them.

## Results and reproduction

`RESULTS.md` gives all twelve cells. `results.json` retains all per-attack values, customer/class correctness strata, fold identities, deletion membership, remaining sample sizes and suite maxima/winners. Weighting can move BA in either direction: standard jointconstant cancel/return goes 60.5002/55.4593% to 58.9572/53.1546%; rules goes 58.7533/59.4001% to 56.6002/60.3987%. No absolute-defense threshold is certified from these point sensitivities.

Only Python standard library is required. From the package root:

```powershell
python experiments/sp2027-r8-cluster-sensitivity/verify.py
```

This verifies frozen input/code hashes, all numerical results via an independent direct-weight formula, original suite-max BA agreement, all customer deletions, and counts. It writes this directory's `verification.json`. To reproduce collection-free derivation, copy the whole experiment to a separate reproduction tree preserving its sibling source location, preserve `freeze.json`, remove only that copy's `results.json`, and run `analysis.py run` followed by `verify.py`. The run command refuses to overwrite a completed result. Do not rerun `freeze`: the saved freeze records the actual pre-analysis algorithm/input hashes and timestamp.

`freeze.json` was written before executing these new calculations and binds `PROTOCOL.md`, `analysis.py`, `verify.py` and both old saved-input hashes. This is an internal analysis freeze after the original OOF test predictions were already available, not prospective preregistration or independent external validation.
