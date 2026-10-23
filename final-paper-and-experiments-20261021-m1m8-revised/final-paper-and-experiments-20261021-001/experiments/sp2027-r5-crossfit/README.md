# R5: cross-fitting, operating points and leakage localization (E10–E12)

This directory only reads the immutable R4 snapshot (`../sp2027-r4-snapshot-20261023/`) and the full-cohort delta (`../sp2027-r4-full-20261023/`). No model is called, and no R4 file is modified: `verify_r5.py` checks R4 hashes against the package `SHA256SUMS.json`.

## Why

The E9 held-out split has 5 cancellation-positive and 7 return-positive customers (5–7 in the completed cohort). Its 50.0% defended point estimates equal the suite floor set by the majority baseline. E9 also measures a single operating point (15.3× bytes), and it does not explain why the rules prompt fails. R5 addresses all three.

| Experiment | Script | Question | Output |
| --- | --- | --- | --- |
| E10 | `e10_crossfit.py` | Does the training-only defense hold with more positive customers? | `e10_crossfit_results.json` |
| E11 | `e11_select.py` | Can a cheaper operating point be chosen without seeing test data? | `e11_selection.json`, `e11_heldout_results.json` |
| E12 | `e12_localization.py` | Where does real-agent intent leakage live? | `e12_localization_results.json` |

## Design

- **E10.** Customer-grouped, stratified 5-fold cross-fitting over all 690 completed episodes (115 tasks, 53 customers; 14/18 positive customers). Set `R5_COHORT=snapshot` to reproduce `snapshot-660/`. In each fold, the template, donor pools, caps and all attackers are fit on the other folds only. The out-of-fold predictions are pooled, and intervals come from 2,000 customer-cluster bootstrap draws. Six configurations were fixed in `r5lib.FRONTIER` before evaluation.
- **E11.** The selection rule is written in the docstring of `e11_select.py`. Inner 5-fold CV runs inside the 69 frozen training tasks. A configuration is eligible only if all four inner network BAs are ≤ 60%, and the cheapest eligible one is chosen. Its choice is recorded before a single evaluation on the frozen test tasks (46 in the completed cohort). Result: `r4_bucket` was selected.
- **E12.** An oracle observer ablation of undefended traces: full trace, trace with state-changing calls removed, and state-changing calls only. Cross-fitted with the E10 folds.
- **Transport.** `tlsmodel.py` is an analytic TLS 1.2 AES-GCM record model: each fragment carries 24 bytes of overhead, with 16,384-byte fragments. It matches all 2,760 socket-measured sessions of the completed cohort exactly, and 120 fresh loopback captures (via `tlslab.py`) of new cross-fitted sessions.

## Main results (completed 690-run cohort, network view, baseline prompt, core suite)

E10–E12 use all 690 completed episodes (115 tasks, 53 customers; 14/18 positive customers): the R4 snapshot runs plus the 27 runs in `../sp2027-r4-full-20261023/delta/runs/`. The same analysis on the 660-episode snapshot grid was run first and is kept in `snapshot-660/`.

| Configuration | Cancel BA [95% CI] | Return BA [95% CI] | Bytes× / Calls× |
| --- | ---: | ---: | ---: |
| Undefended (E10) | 91.7 [82.1, 100] | 85.5 [76.6, 93.4] | 1.0 / 1.0 |
| E9 point, constant framing (E10) | 60.5 [51.5, 70.5] | 52.1 [50.0, 60.3] | 19.8 / 5.0 |
| 1024-B buckets (E10) | 52.2 [50.0, 60.5] | 52.7 [50.0, 60.2] | 12.4 / 5.0 |
| Rules + 1024-B buckets (E10) | 53.4 [50.0, 60.6] | 50.7 [50.0, 57.3] | 12.4 / 5.0 |
| Writes-only cover (E10) | 53.5 [50.0, 65.8] | 56.1 [50.0, 67.4] | 11.3 / 2.9 |
| E11 selected (buckets), frozen 46-task test | 53.2 [50.0, 69.5] | 58.4 [52.9, 69.1] | 9.8 / 3.8 |
| E9 point, frozen 46-task test (reference) | 50.0 [50.0, 60.6] | 50.0 [50.0, 65.5] | 15.4 / 3.8 |
| E12: writes removed | 55.2 | 59.9 | – |
| E12: writes only | 91.7 | 84.9 | – |

Further results:

- **Paired reductions versus raw transport:**
  - E9 point: −31.2 [−41.6, −21.5] and −33.4 [−41.0, −21.5].
  - Buckets: −39.4 [−48.3, −27.9] and −32.8 [−39.2, −23.4].
- **Rules minus baseline with the bucketed defense:** +1.2 [−7.0, 7.5] and −2.0 [−7.4, 4.2]. There is no interaction.
- **Extended suite:** it changes no E9-point or bucket cell by more than 1.7 points.
- **Rules prompt and call sequences:** distinct read-only sequences fall from 74 to 62. State-changing sequences stay at 37 versus 36 (4.08 versus 4.09 bits).
- **Snapshot-660 comparison:** on the 660-episode grid, the bucket point gives 50.6/51.6 with upper bounds of 59.2/58.3. On the full cohort, the upper bounds are 60.5/60.2, at the 60% criterion.

## Reproduce

Requires Python ≥ 3.11, numpy, scipy, scikit-learn ≥ 1.9, cryptography and pydantic. Use `OMP_NUM_THREADS=1`. From this directory:

    python -B e10_crossfit.py --config r4      # run each FRONTIER name; they can run in parallel
    python -B e10_crossfit.py --merge
    python -B e11_select.py
    python -B e12_localization.py
    python -B verify_r5.py                     # writes validation_r5.json
    python -B make_tables_r5.py                # manuscript/tables/r5-main.tex, r5-supp.tex

Runtime on 4 cores is about 30 minutes for E10 when run in parallel, 15 minutes for E11 and 4 minutes for verification.

## Scope

This is the same single benchmark and model alias as E9. E10 adds statistical power, not a new population. Intervals condition on fitted attackers. Cross-fitted templates see more customers than the E9 template and are therefore larger, which explains why calls rise from 3.8× to 5.1×.
