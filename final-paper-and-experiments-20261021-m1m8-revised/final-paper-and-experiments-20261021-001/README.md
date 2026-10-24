# Current R7 paper and reproducibility package

Current PDFs: `pdf/main.pdf` (17 pages; main body at most 13) and `pdf/supplement.pdf` (48 pages). LaTeX is in `manuscript/`. References precede the appendix. `artifact-index.json` resolves logical modules to preserved physical archives.

## Evidence and current analysis

- Original Sol cohort: 690 real runs, 115 tasks, 53 customers, two prompt arms, three repeats. The original 414/276 split and calibration remain unchanged.
- Primary E10 update: 11 attacks, complete customer five-fold cross-fitting, 60 fitted packs and 45,540 score checks. Standard-prompt BA: undefended 91.7%/85.5%; joint constant 60.5%/55.5%; joint buckets 57.1%/52.7%. The paired decreases and absolute gate are separate outcomes.
- E13/E14: 4,140 saved live tool sessions; 13 measured/simulated conditions and 52 evaluation cells. All 312 new learned models were exactly refit and reloaded. The cost plot matches the seven common attacks and separately retains larger full-union maxima; unequal attack unions cannot establish matched dominance. Actual tool clocks and simulated WF schedules are not interchangeable.
- E12: a separately frozen stronger oracle write-call ablation in `sp2027-r7-localization`, retaining the original folds and full old attack union. Oracle filtering is diagnostic, not a deployable defense.
- Additional Luna collection: 150 formal runs, 75 existing tasks, two prompts, one repeat; 58 training and 92 test trajectories, 10/24 customers. Each prompt-specific attacker fits 29 training examples and tests 46. The 10 pilot runs are separate. These are same-provider model aliases and the same environment, not cross-vendor/open-weight/new-customer validation.
- Source audit: three publicly justified status corrections are an explicit overlay on preserved prior tables and coding columns; 11 bindings remain unverified. No independent-human reliability claim is made.

## Current checks

From this package directory:

```text
python -B provenance/r7-review/verify_publication.py
python -B verify_package.py
python -B verify_revision.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

The package check uses SHA-256 for every publication file and the live LaTeX closure. It excludes only the original local collector directory `experiments/sp2027-r4` and Python bytecode caches. Earlier document-specific verifiers retain earlier layouts and should not be applied to the current PDFs. Prior experiment verifiers remain valid for their immutable inputs.

## Local reproduction without LLM calls

```text
python -B experiments/sp2027-r7-robustness/verify.py
python -B experiments/sp2027-r7-robustness/run.py reproduce
python -B provenance/r7-review/retrain_robustness.py
python -B experiments/sp2027-r7-crossfit/verify.py
python -B experiments/sp2027-r7-localization/verify.py
python -B experiments/sp2027-r7-agent-extension/verify_public.py --network
```

Check each module's README for exact versions and command working-directory requirements. Experimental dependencies include NumPy, SciPy, scikit-learn, CPU PyTorch and cryptography; pypdf is needed for document checks and matplotlib for plot regeneration. Exact frozen runtime versions are saved in each experiment. Public raw evidence redacts only the local home-directory prefix with original/public hashes and replacement counts. Scientific observations, model names, decisions, actions and scores are retained. Luna public-ZIP verification additionally requires the hash-checked benchmark/tool sources in this checkout; the ZIP alone is not a standalone package. Tool counters distinguish registered-name dispatch attempts (including failed calls), unknown-name attempts and model calls.

Rebuild with standard IEEEtran 1.8b (conference, compsoc), pdfLaTeX and BibTeX:

```text
python -B provenance/r7-review/build_pdfs.py
```

The `--publish-copies` option additionally updates the root/package PDF copies and normalized compiler logs. It does not update the package manifest automatically; published checksums describe the delivered build. Rendering receipts record inspected PDF hashes. Plot/table generators support read-only `--check` as documented.

## Archive map and limits

The full Sol release and 663 snapshot, R2/R3/R5/R6 experiments, old coding records and prior ZIPs remain immutable. `provenance/r7-review/prior-package-manifest.json` and the history check verify preservation. `prior-root-readme.md` / `prior-package-readme.md` retain earlier guides. `reviewer-comments.txt`, the 40-item coverage index, author attestation, source overlay and current validation receipts explain each change.

Data validation is not an absolute-security certification. No configuration in E14 meets the original absolute criterion. Same-provider extra runs do not supply a second environment, fixed open weights, different-vendor data, new positive customers, live-cover planner utility or two external human coders. The prospective protocol specifies those remaining studies without claiming they have been run. Model archives use trusted Python serialization and should not be loaded from an untrusted source.
