# R9 publication verification

This revision reorganizes the current paper around four demonstrations and makes the audit rules, family map, record index and experimental navigation available in one submission PDF. It adds no model runs and changes no experimental measurements.

## Verify the published release

From the package root:

```text
python provenance/r9-review/verify_publication.py
python verify_package.py
```

The first command checks the current PDF/source closure, preserved experimental files, numerical transcription, link audit, visual-review receipt and anonymous paper-source bundle. The second validates the package manifest and retained experimental checks. Neither command claims a new security guarantee or an independent human recoding study.

`validation.json` and `visual_qa.json` bind the final PDFs. `content-review.json` records a separate source review; final page geometry is covered by the final validation. `bibliography-layout-audit.json` checks all 77 cited bibliography URLs against the PDF's 107 URI annotations. `condensed-numerical-audit.json` checks 51 scientific data rows and 346 numeric tokens against R8.

`prior-manuscript/` and `prior-release/` preserve the R8 source/PDF and publication metadata. The initial record/index construction receipts retain their drafting-time hashes; the final verifier checks the published record and experiment indexes. The authoring scripts (`rewrite_*`, `prepare_revision`, `refine_navigation`, `finish_navigation`, `release_setup`, `release_docs`) document the editing sequence and are not required to verify or rebuild the release. Some are intentionally one-time transformations; do not replay them against the final manuscript.

To rebuild the existing sources, use `build_pdfs.py`; `--publish-copies` also updates the three PDF locations and compiler logs. A new build changes PDF timestamps/hashes and requires new visual/link audits, anonymous bundle and publication manifests before release. `render_pages.py --final` creates local inspection rasters and does not approve their appearance automatically.

The anonymous ZIP contains only the paper PDFs and their LaTeX source closure. It excludes development history and machine-specific logs; it is not a hosted anonymous copy of the full experimental artifact.
