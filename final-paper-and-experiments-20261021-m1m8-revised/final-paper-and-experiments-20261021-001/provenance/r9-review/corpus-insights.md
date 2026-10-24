# R9 corpus map audit

Date: 2026-10-24. This note records the source-derived layer/type distribution underlying the edited Section 4 map and the exact table reorganization. No new model or LLM experiments were run.

## Sources and method

The 58 rows were parsed from `manuscript/tables/core-family-map.tex`. Family origin class was joined by citation key to `evidence/retained-release007/search-update/final-family-index.csv`; ledger groups were joined to `provenance/review-closure/family-record-concordance.csv`. The scriptless reproducible row-level extraction and aggregate counts are in `provenance/r9-review/corpus-insights.json`. Checks require exactly 58 unique map rows, 38 `inherited-runtime/application` plus 20 `workflow-origin`, and 32 `map-only` rows.

P1–P8 counts and Type I–IV counts are label incidences. A family can have several generating layers, receiver layers, or types, so these counts overlap and are not partitions. `G -> O` is displayed as two layer sets; it does not imply a one-to-one causal edge between every listed pair. Counts describe this curated corpus only, not field prevalence, risk, or study quality.

## Results

| View | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Generation, all 58 | 17 | 32 | 1 | 1 | 19 | 6 | 8 | 3 |
| Receiver, all 58 | 16 | 4 | 14 | 18 | 0 | 8 | 6 | 2 |
| Generation, 32 map-only | 11 | 15 | 1 | 1 | 11 | 4 | 3 | 1 |
| Receiver, 32 map-only | 10 | 3 | 6 | 10 | 0 | 6 | 2 | 1 |

| Threat purpose | Type I | Type II | Type III | Type IV |
|---|---:|---:|---:|---:|
| All 58 family incidences | 41 | 13 | 2 | 5 |
| 32 map-only incidences | 19 | 9 | 1 | 5 |

The map shows P2 serving/runtime as the most frequent listed signal-generation layer, while P4 application/API, P1 hardware, and P3 transport recur as receiver layers. The 32 map-only families span P1/P2/P5 generation and P1/P4/P6 receiving views; their Type IV diagnostics and Type III evasion incidences show that the wider map includes objectives beyond confidentiality. These are evidence-map observations, not claims that every family has an evaluated defense. The existing corpus partition further identifies the 32 as 22 without a scoped mitigation evaluation, five diagnostics, four unbound quantitative assertions, and SplitDecoy's boundary case.

## Main-text and table changes

Section 4 adds 258 English words on the layer and purpose distributions, overlapping-incidence interpretation, and the distinction between a broad family map and the narrower result ledger. The prior-systematization paragraph now presents four empirical comparison boundaries positively: emitter/transport, execution/link, repeated agent trajectories, and timing/adapted WF controls. It removes the old E5–E7/S12 dangling reference and does not claim a new padding method or cross-vendor result.

The table now uses two equal 29-family minipages to avoid blank rows: the left holds the first 29 Origin B families (P1: 8; P1/P2: 8; first 13 P2), while the right holds the remaining 9 P2 families followed by 5 cross-layer Origin A families and 15 orchestration/workflow Origin A families. All 58 family/citation, G/O-layer, and Type values were checked against the extracted JSON and preserved; only ordering, grouping, caption, and table note changed. Group labels describe source layers, not evidential quality.
