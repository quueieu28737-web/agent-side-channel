# R5: cross-fitting, operating points and leakage localization

The new experiments are in `experiments/sp2027-r5-crossfit/`. They read the immutable R4 snapshot and the full-cohort delta without modifying either, and make no model calls. The review and checklist are in the repository at `docs/R5-SP2027-审稿与修改清单.md`.

All results below use the completed 690-run cohort (115 tasks, 53 customers). The snapshot-660 replicate is in `snapshot-660/`.

- **E10.** Cross-fitted undefended network BA is 91.7%/85.5%. The training-only defense lowers it by 31–39 points, with paired intervals excluding zero. The R4 rules+program return cell (64.1%) does not recur: the rules-minus-baseline difference is +1.2/−2.0, and both intervals span zero.
- **E11.** With 1024-byte buckets, BA is 52.2%/52.7% at 12.4× bytes, versus 60.5%/52.1% at 19.8× for constant framing. The training-only selection rule picks the bucket point; on the frozen 46-task test split it costs 9.8× instead of 15.4× bytes, at 53.2%/58.4%.
- **E12.** State-changing calls alone support 91.7%/84.9%; removing them leaves 55.2%/59.9%. The rules prompt homogenizes reads (74 → 62 distinct sequences) but not writes (37 versus 36).

Manuscript changes:

- The abstract, introduction contributions, §8.4–8.6, Takeaway 4, §9.1, §9.3, the conclusion and Appendix A are updated.
- New §8.5 with Table 13, and new Supplement S15.
- The main text stays at 13 pages. The E9 table keeps the 663-run snapshot scope chosen by the full-cohort supplement.

Verification: `python -B experiments/sp2027-r5-crossfit/verify_r5.py` writes `validation_r5.json`. It checks:

- the TLS model against all 2,640 snapshot and 2,760 full-cohort captures;
- that the calibration, all sessions, and the 32 result cells of both frozen-split analyses are reproduced exactly;
- 120 fresh socket captures;
- the R4 input hashes.
