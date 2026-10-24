# Prospective external validation protocol (not collected)

This plan is authored after inspection of E9--E14. It does not retroactively preregister those analyses and has no completed observations.

## New environments, model versions and clusters

Use retail plus an airline or stateful MCP file/Git environment with different write semantics. A fixed open-weight checkpoint and an independently hosted vendor model should each be identified by immutable weights/digest or a provider version ID. Luna/Sol aliases from the same provider do not satisfy this requirement. Separate user simulation from the tested planner model, or cross this factor explicitly. Record all rejected task templates and every failure.

Generate customer/account states from multiple prelisted templates with different statuses, payloads, call counts and action paths. Assign customers, not episodes, to train/test before any model or defense fitting. Do not relabel copied benchmark states as independent empirical people. Template-origin clusters must also be reported, with leave-template-out sensitivity. Repeated tasks add precision within customers, not independent positive customers.

Target at least 30 cancellation-positive and 30 return-positive held-out customers as a feasibility floor; the accompanying power sensitivity shows that this does not guarantee a pass. Determine the final sample size from a prespecified precision/power calculation with conservative classifier dependence and cluster variability; use a separately collected pilot for these nuisance estimates. If resources cannot support the required sample, retain paired-reduction claims and report the absolute assessment as inconclusive.

## Freeze before collection

Primary estimands: maximum defense-aware BA over the complete frozen suite for each intent, and paired joint-minus-undefended BA. Preserve the absolute criterion: upper 95% customer-cluster BA < 0.60 and suite-max AUROC < 0.65. Recompute maxima in each of 2,000 common customer draws; retain all prompts/repeats of a customer. Report class-free draws and conditioning on fitted models. Do not select configurations or tests on final outcomes. Freeze train-only calibration, donors, cell/bucket parameters, attacker settings, operating-point selection and code hashes before any final test run. Archive the plan in a timestamped repository before collection; no external preregistration is claimed here.

## End-to-end live utility

For an explicitly paired/randomized 100--150-task subset, run the real planner anew with defense enabled/disabled, feeding real delayed observations back to that planner. Keep task distributions and model settings fixed; include a fixed-rate tunnel and bounded concurrent shadow scheduler. Measure reward, wall-clock completion, time to useful response, retries, timeout/abort rate, billable tools and total bytes. Analyze by customer and preserve all failures. Replaying a saved action sequence cannot substitute for this experiment. A priori bound cover budgets and permit cancellation; do not run against other users' production accounts.

## Independent coding

Recruit two external human coders with field expertise. Prespecify a stratified 8-family/72-cell sample from the 20 mitigation families, covering origin/polarity and all audit statuses. Give each the coding codebook, exact source versions and locators without initial/existing labels. Save individual labels before any discussion; compute unweighted Cohen's kappa and percent agreement on the independent pair, then adjudicate separately. Keep the original extraction--author-verification kappa labeled non-independent. Empty templates and AI reviews are not human ratings.

## Completion gates

At least two genuinely extra environment/model settings should reproduce the qualitative findings before a cross-setting generalization claim. Any non-replication narrows the claim. Security, logical state preservation, online utility and source-code reliability have separate gates; passing one never silently closes another.
