# Defense transfer boundary analyses

All analyses here are exploratory and use the two completed endpoint cohorts with the original 69 training / 46 test task partition. They add no new independent customers or authenticated fixed-weight models.

- `evaluate_full_suite.py`: primary expanded endpoint suite (original six plus total exchange count), with saved predictions and independently recomputed point BA. The 28 rows separate attacker transfer from defense calibration transfer.
- `run_calibration_transfer.py`: 690 actual TLS loopback captures, source training calibration on target trajectories, plus local write-only padding. No fresh model calls.
- `run_attack_transfer.py` and `evaluate_calibration_transfer.py`: retained earlier LR/GB/majority exploratory analyses; do not substitute these smaller-suite numbers for the expanded suite.
- `run_write_detector.py`: train-only length-based write detector and downstream inferred-write features. Tool types supervise training only; test selection uses the detector.
- `request_field_accounting.json`: exact request serialization accounting; field omission is not a valid API intervention or a causal semantic privacy result.

All cost ratios use summed target-model test transport bytes. Original model studies and their frozen results remain unchanged.

## Read-only reproduction

Run `verify_transfer.py` for all 28 saved point metrics, 2,000-draw customer intervals, 690 capture hashes and wire-cost denominators. `verify_write_detector.py` reconstructs the training-only detector, retains exchange-level predictions, and checks downstream point metrics and intervals. `account_request_fields.py` reproduces the 59 request-field rows, retaining one invalid `return` alias separately from valid return-tool calls. `paired_transfer_intervals.py` gives paired suite-max contrasts on common customer draws, conditional on fitted attackers. These commands make no new model requests.

The expanded seven-attack results supersede the smaller-suite summaries for manuscript comparisons. They retain the original endpoint attacks and add total exchange count; they are not the Sol timing/CNN union. Source-trained attack transfer and source-calibration transfer with target-trained attackers answer different questions and remain separate matrices.
