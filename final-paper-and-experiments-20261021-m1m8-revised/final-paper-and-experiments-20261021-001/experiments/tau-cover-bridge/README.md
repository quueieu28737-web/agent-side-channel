# Executed-cover routing on tau-bench retail

This directory contains the controlled T2(c) experiment requested in the side
conversation. It uses all 115 retail test reference programs at upstream commit
`59a200c6d575d595120f1cb70fea53cef0632f6b`, its original tools, business data and
native reward. The controller replays public reference programs; there is no
model or simulated human user in this experiment.

Read `PROTOCOL.txt` before interpreting the measurements. The interventions are
discarded cover, isolated-shadow execution, a pure order-details read, and a
live cancellation, compared with no cover. Three fixed random seeds and two
insertion positions are repeated observations within a task, not 690 independent
tasks. The sample is the 115-task census, with ineligible-cover cases retained.

## Commands

Use the bundled Python or an environment with NumPy and Pydantic:

```
python -B prepare.py
python -B bridge.py test
python -B bridge.py run --out runs/new-original-run
```

The first local attempt was stopped for repeated whole-state scoring overhead.
Its code and all 851 saved cells remain unchanged. The continuation executes
only missing `(task, seed, position, arm)` cells. It memoizes identical original
native rewards within a task using a hash of the complete final business state:

```
python -B continue_fast.py --prior runs/frozen-001 --out runs/continuation-002
python -B verify.py --out runs/continuation-002
```

Do not rerun either command into an existing output directory. All new tests use
new paths. `verification.json` checks the complete cell census, exact retention
of the prior rows, reconstructed state hashes, and original native rescoring of
every unique task/final-state combination. This is saved-result verification,
not new task collection.

The measured policy event is an unconfirmed injected write in this explicitly
scripted context. The experiment does not infer unobserved consent from a real
conversation. The native reward is exact benchmark state/output scoring, not a
claim that an autonomous agent completed the benchmark. Public reference outputs
are supplied only for the existing native output predicate. Task planning and
dialogue quality are outside this routing experiment.

## Files

- `sources.json` and `vendor/`: pinned upstream bytes and acquisition receipts.
- `runs/frozen-001/`: the retained first attempt and engineering-stop receipt.
- `runs/continuation-002/`: prior+new cells, per-task progress, final receipt,
  summary, paired effects and independent numerical verification.
- `summary.csv`: every frozen arm, insertion position and endpoint.
- `paired-effects.csv`: treatment minus no-cover, whole-task bootstrap intervals.

Only local CPU and synthetic benchmark records are used. No original manuscript,
Luna run, sealed release or private model log is changed. A local open-source
code bundle is different from a publicly hosted repository; this directory does
not claim an external publication receipt.
