# E13: live tool timing, latency and full fixed-rate tunnel controls

Completed: **4,140 measured TLS sessions** (2,484 training, 1,656 test) driven by the original 690 saved real-agent action trajectories. See [PROTOCOL.md](PROTOCOL.md) for the frozen design and [validation.json](validation.json) for capture/state/clock/numeric checks.

No new LLM calls. These are actual local tool executions with response-gated requests, not fabricated packet times. They do not measure WAN transit, fresh LLM replanning or production APIs.

## Files and reproduction

- `frozen.json`: source hashes, training-sized tunnel horizon, original split and calibration hash.
- `attacker_freeze.json`: hashes of fitted models and analysis sources, recorded before test capture.
- `captures.zip`: every formal per-session measurement, including ciphertext records, chunk arrival timestamps, tool execution annotations, queue/deadline data and state/response checks.
- `models.zip`: the frozen training-only models. Load only after checking their receipt hashes.
- `pilot.zip`, `development.zip`: separate development records, excluded from formal totals. They preserve the initial Windows early-wakeup issue and the complete version-1 pass, whose integrity check found two truncated dummy tails. Version 2 adds a receive-drain barrier and E9-style profiling controls, then recollects the entire cohort with a new training-before-test model freeze. No version-1 sessions are pooled into final results.
- `predictions.json`, `detector_predictions.json`, `test_cuts.json`: complete saved decisions and estimated flush cuts.
- `results.json`: every attack view, full-suite customer intervals, detector results, paired effects and latency/cost metrics.
- `environment.json`: runtime/library versions. Set `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1`.

From this directory with dependencies in the Python environment:

```text
python -B test_r6.py
python -B verify_r6.py
python -B reproduce.py
python -B make_tables.py --check
```

These commands verify saved results without new traffic/model calls; compressed captures/models are read directly. `reproduce.py` leaves the frozen analysis source intact and compares exact JSON semantics: its wrapper normalizes in-memory tuple spans to JSON arrays, fixing the literal-comparison mismatch in the frozen script's `--check` path. No prediction tolerance is applied. To recollect, use a separate copy containing the sources and the original sibling R4/R5 dependencies, without generated freeze/receipt/output files: `experiment.py freeze`, `experiment.py train`, `analyze.py fit`, `experiment.py test`, then `analyze.py evaluate`. Preserve the old measurements; timing measurements need not be byte-identical across hosts. Never overwrite a frozen fit or replace test sessions with preferred reruns.

`start_utc` in a capture is the wall-clock receipt-creation timestamp; measurement timing uses `origin_clock_ns` and relative monotonic timestamps. See pipeline receipts for phase ordering. Non-payload TLS handshakes/closure alerts are outside the application-record projection.

## Baseline-prompt held-out results

| 条件 | 长度/顺序 BA | 完整攻击套件 BA | 字节倍数 | 调用倍数 | 真实响应链 p95 ms | 流量结束 p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| 原始传输 | 91.7%/86.4% | 91.7%/86.4% | 1.00 | 1.00 | 15.45 | 15.47 |
| 单调用填充 | 68.6%/54.8% | 68.6%/62.7% | 3.92 | 1.00 | 16.64 | 16.68 |
| 串行 Shadow | 50.0%/50.7% | 61.4%/53.4% | 15.11 | 3.83 | 26.23 | 46.62 |
| 最多两次在途 Shadow | 51.7%/57.7% | 51.7%/57.7% | 15.11 | 3.83 | 20.85 | 37.41 |
| 完整隧道 2 ms | 62.5%/52.9% | 62.5%/52.9% | 125.71 | 1.00 | 56.40 | 270.43 |
| 完整隧道 5 ms | 51.4%/54.5% | 53.1%/57.3% | 125.71 | 1.00 | 112.30 | 666.64 |

BA columns are cancellation/return; the full suite unions all views. Native reward preservation follows exact real-response and state preservation on saved actions, not independent online LLM trials. The original E9 threshold and evidence remain unchanged.
