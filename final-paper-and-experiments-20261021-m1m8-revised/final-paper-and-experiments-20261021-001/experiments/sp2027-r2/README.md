# sp2027-r2: historical controlled transfer tests (E5–E7)

R3 NOTICE: raw observations and registration remain unchanged. Current manuscript interpretations, E6/E7 suite intervals and held-out request-only identification use ../sp2027-r3/. Historical judgment counts are not a validation score. P5 lacks the source-protection premise; no E7 configuration meets both target criteria.

This directory adds three controlled experiments requested in the second-round
S&P 2027 self-review. They test claims that the paper's audit marks as
*unresolved*, rather than re-demonstrating the mechanisms of Section 8.1–8.3.
No model API, production tool or external network is contacted. All TLS
observations are real loopback socket captures through a byte-transparent relay.

| File | Role |
|---|---|
| `PREREGISTRATION.json` | Seven audit-derived transfer claims (P1–P7), judgments and decision thresholds. Committed in git **before** any E5–E7 code was run (commit `16f6254`). |
| `tlslab.py` | TLS 1.2/1.3 loopback harness; counts only post-handshake application records; TLS 1.3 tickets disabled. |
| `e5_streaming.py` | E5: the 48 saved responses emitted as SSE-style token streams (and buffered, for anchoring) under 7 framing policies; D0/D2 threshold and sequence attackers; closed-world identification among 48 responses. |
| `e6_e7_retail_cover.py` | Generates E6/E7 sessions: 115 retail reference programs × 3 seeds × 8 cover policies; cover calls are sampled from other tasks' programs and placed at random positions; shadow or live execution. Replays 4 cover policies × 3 framings over TLS 1.2 (4,140 sessions). |
| `e67_eval.py` | Evaluates E6 (dispatch view) and E7 (network view) from the saved files with task-grouped 5-fold CV and task-cluster bootstrap. |
| `resolve_predictions.py` | Applies the pre-registered thresholds to the results. |
| `*_results.json`, `PREREGISTRATION_OUTCOMES.json` | Historical results; current E6/E7 summaries and judgment reassessment use R3. |
| `e5_streaming_captures.json`, `e6_sessions.json`, `e7_records.json` | Raw per-unit observations (record-length sequences, tool traces, state outcomes). |

## Checklist-B toolkits (added after E5–E7)

| Directory | Checklist item | Status |
|---|---|---|
| `agent/` | B3 autonomous-agent experiment (E8) | Pipeline complete; LLM backends tested against a mock server; stand-in runs only. **No LLM results.** |
| `coding/` | B1 independent blinded coding | Sheets, codebook, declarations and an analysis with family-cluster intervals. The self-test reproduces α = 0.876 from the supplied columns. **No human coding has been done.** |
| `release/` | B2 anonymous artifact, K8/K9 confirmations | Anonymity scan (0 hits) and a deterministic zip builder; author-confirmation form. **Not uploaded.** |
| `search/` | B4 recall | Second arXiv frame: 37/58 core families, a queue of 617 unscreened records. **No recall estimate.** |

## Run

Python 3.11, numpy, scikit-learn 1.9, cryptography, pydantic, tiktoken (o200k_base).

```
python -B e5_streaming.py          # ~2 min
python -B e6_e7_retail_cover.py    # ~15 min (sessions + 4,140 TLS sessions)
python -B e67_eval.py              # ~5 min
python -B resolve_predictions.py
python -B make_tables.py           # regenerates manuscript/tables/transfer-*.tex, supp-transfer.tex
python -B verify_r2.py             # read-only checks, standard library only
python -B refresh_manifest.py      # after rebuilding the PDFs: snapshot + SHA256SUMS
```

A complete second execution of the four experiment scripts reproduced every result,
capture and session JSON file byte-for-byte (SHA-256).

## Scope (read before citing a number)

* Token segmentation uses o200k_base as a proxy; the generating model's tokenizer and
  timing were not saved. Latency figures are token-interval accounting, not measurements.
* TLS 1.3 padding is applied at the application layer (an obfuscation field); Python's
  ssl module does not expose OpenSSL's record-padding callback.
* Retail sessions replay gold reference programs; there is no LLM planner. Shadow cover
  assumes the tool provider executes designated cover calls in a per-session sandbox.
* The profiling decoder assumes the attacker can issue its own calls to the public tool
  API to learn request/response sizes per tool.
* 18 of 115 tasks contain a cancellation and 32 a return; intervals are task-cluster
  bootstrap intervals and are wide. "Best attacker" is the maximum over all attackers.
* The predictions were written by the same authors who designed the audit; they are a
  falsifiable internal test, not external validation.
