# Current R8 paper and reproducibility package

Current PDFs: pdf/main.pdf (17 pages, body at most 13), pdf/supplement.pdf (52 pages). Standard IEEEtran conference/compsoc; references precede the appendix. Current closure and hashes are in provenance/snapshot.json, SHA256SUMS.json and artifact-index.json.

## Evidence hierarchy

The SoK contributes 82 families and 39 source-bound result records, with a 58-family map and 20-by-9 applicability-aware main-paper audit. Concrete transfer errors concern re-emission, execution/state and mismatched evaluation/utility/cost objects. R1–R9 are reuse-evidence conditions rather than paper-quality scores.

The original Sol collection is 690 runs, 115 tasks and 53 customers. E9 freezes calibration before test collection; development had the full population. E10–E14 are exploratory known-cohort extensions. The prior 150-run Luna study is same-provider and same-environment. R8 adds no LLM calls or customers.

## New analysis

- experiments/sp2027-r8-cluster-sensitivity: 12 fixed-prediction cells, 192 positive-customer deletions and customer-class-equal weighting. These measure influence, not refitting uncertainty or new confidence intervals.
- experiments/sp2027-r8-sensitive-attributes: exact call/record alignment, same-operation/single-item strata, fixed researcher-defined semantic grouping, old customer folds, repeat aggregation and negative controls. Each prompt has 20 instances and 15 customers; there are not 138 independent calls. Frozen fitting and independent score reloading do not provide stable above-chance evidence for the selected attribute.
- provenance/r8-review/defense-self-audit.json: matched seven-model costs, full unions, flush removal and our own utility evidence boundary.
- provenance/r8-review/family-status-overlay.csv: per-family applicability. Unverified source bindings are separate from negative experiments.
- provenance/r8-review/all-citations-form-labels.csv: all 77 cited forms, including 49 arXiv-only and 21 venue-labelled (five also with preprints). These labels do not independently certify peer review.

## Validation and rebuilding

~~~text
python -B provenance/r8-review/verify_publication.py
python -B provenance/r8-review/make_tables.py --check
python -B experiments/sp2027-r8-cluster-sensitivity/verify.py
python -B experiments/sp2027-r8-sensitive-attributes/verify.py
python -B verify_package.py
~~~

The attribute module records runtime dependencies and a frozen plan. Its verifier reloads trusted serialized models and recomputes scores; never load such models from an untrusted source. No API key or model call is needed. R7 dependency closures and receipts remain bound to their original experiments.

Rebuild using Python provenance/r8-review/build_pdfs.py --publish-copies with pdfLaTeX and BibTeX. This updates root/package PDFs and current logs but not release metadata/manifest automatically. Delivered hashes describe the completed publication build.

## Preservation and submission

The prior-package-manifest in provenance/r8-review records all 7,252 prior files; the prior manuscript snapshot and old experiments are byte-checked. R8 permits explicit current manuscript/PDF changes while preserving old experiment code, protocols, data and receipts.

The current checklist records missing external studies: new customers, cross-vendor/open-weight and second-environment transfer, live planner utility under defense, real provider backends, independent human recoding. Neither paired reduction nor state equality certifies security.

provenance/r8-review/anonymous-paper-source.zip contains paper PDFs, LaTeX closure and standard class/style files without Git history or machine logs. It is not the separately hosted anonymous experimental artifact. Conference registration, final author review, conflicts and AI-use declarations remain author submission actions.
