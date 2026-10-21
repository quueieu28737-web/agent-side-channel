# Blinded coding protocol (checklist item B1)

This protocol replaces the supplied AI-assisted coding columns with an independent,
blinded human audit. **Nothing in this directory is a human-coding result.** The
self-test (`selftest_results.json`) only checks that the analysis code reproduces the
historical agreement statistic from the two supplied columns (α = 0.876).

## Roles
- **Coders (≥2):** security researchers who did not design the checks, did not write the
  manuscript and have not seen the AI-assisted columns. Each signs `COI_DECLARATION.md`.
- **Adjudicator (1):** not a coder; resolves disagreements using `ADJUDICATION_LOG.csv`.
- **Custodian:** generates and distributes sheets and freezes the manifest. Does not code.

## Procedure
1. `python -B make_blind_sheets.py --coders C1 C2` creates the sheets. Commit `sheets/MANIFEST.json`
   **before** distributing them, so that the hashes prove the sheets were not edited afterwards.
2. Send each coder only `audit_<coder>.csv`, `pairs_<coder>.csv`, this codebook and the
   source PDFs or URLs. Do not send the manuscript, the supplement or any CSV under
   `experiments/revision-m1-m8/`.
3. Coders work independently and do not discuss cases. Each cell needs a status and an
   evidence locator (section, table or line) in the source.
4. The custodian collects the sheets and commits them unchanged. Then run
   `python -B analyze_agreement.py --audit ... --pairs ...`.
5. The adjudicator resolves every disagreement and records the reasoning in
   `ADJUDICATION_LOG.csv`. Export the resolved labels in the audit-sheet format as
   `adjudicated_audit.csv`, then rerun the analysis with `--adjudicated`.
6. In the manuscript (Section 2.3, Table 9 and Takeaway 2), report α with the
   family-cluster interval and the number of changed cells. If any denominator changes,
   regenerate the affected tables.

## Audit statuses (one per cell)
| Status | Use when |
|---|---|
| Bound | The source explicitly establishes the item for at least one scoped result of the family, and the locator shows it. |
| Partial | A supported element coexists with a proxy or an unlinked operating point. |
| NR-R | Not reported within the inspected scope. |
| NR-V | Material exists, but the binding to the reported result cannot be verified (e.g. code without a run binding). |
| NA | The item cannot apply to this family's claim (e.g. no adaptive attacker is possible). |

## Items
| Item | Question for the coder |
|---|---|
| R1 Target & protection polarity | Are the hidden target and the protected interest (confidentiality, attribution, bot evasion, authorized diagnosis) stated? |
| R2 Receiver fields & linkage | Are the observer's actual fields stated, and how observations are linked across sessions or documents? |
| R3 Placement & action dispatch | Is it stated where the protection ends, and whether cover or edits are executed, stored or transmitted? |
| R4 Protected-condition fit | Is an attacker fitted or calibrated on defended data? |
| R5 Matched adapted test | Are a clean-trained and a defended-trained attacker compared on the same defended test units? |
| R6 Workloads & generator shifts | Are the tasks, systems and holdouts that define portability stated? |
| R7 Defended inference effect | Is inference under the defense measured with a stated metric and denominator? |
| R8 Task or component utility | Is objective task or component utility measured at the same operating point? |
| R9 Mechanism or protocol cost | Is the cost of the deployed mechanism measured, with a stated cost object? |

## Pair judgments
For each record pair and judgment type (descriptive, paired_effect, transfer) assign one of:

- **COMPATIBLE**: the required fields align.
- **INCOMPATIBLE**: a mismatch in mechanism, receiver, target or cost object is positively established.
- **UNRESOLVED**: a required binding is missing or unverified.

Follow the contracts in manuscript Table 4, which is provided to coders as an excerpt.
