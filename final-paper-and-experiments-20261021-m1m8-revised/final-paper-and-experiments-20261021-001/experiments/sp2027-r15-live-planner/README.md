# Live planner utility diagnostic

50 deterministically selected previously used retail tasks, two fresh model-execution arms, 100 episodes. This evaluates a prefix-shadow scheduler with isolated executed cover, fixed local delays and deterministic injected response deadlines. It has no full-episode flush, constant TLS framing, or measured WAN. It does not measure the full E9 joint defense's live utility.

`protocol.json` predates collection. Both arms share the delay/fault schedule; failures remain in the denominator. `live_metrics.json` logs response waits, timeout observations, and subsequent real actions. `verify_and_analyze.py` independently reconstructs state and native reward and computes task-paired, customer-bootstrap reward differences.

`ADAPTER_RESOLUTION_AMENDMENT.json` records a runtime import bug: the first97 episodes loaded the R12 backend using180s rather than intended600s transport timeout. Explicit binding in `run_resolved.py` fixes the remaining cache resumes. The adapters differ only in transport waiting time; model request bodies/parser are identical. Historical intended-source fingerprints remain unchanged, and the amendment records actual prior runtime provenance. All requests, responses and failed attempts are retained.

On infrastructure resume the environment and deterministic delay/fault schedule are replayed from cached decisions. Final native outcomes remain tied to the original recorded planner decisions. Saved wait durations describe the final execution pass, including replayed prefixes; they are not original end-to-end episode latency or LLM-plus-WAN latency.

The120ms deadline is evaluated against the deterministic configured delay, not operating-system wall-clock elapsed time. This is an injected scheduled-time deadline scenario. It must not be described as a measured production timeout mechanism.

## Completed result

100/100 episodes passed state/reward reconstruction. Baseline successes37/50; prefix-shadow33/50. Paired difference -8.0 percentage points, customer interval[-23.9,6.5]. Each arm retains12 injected response timeouts and all terminal protocol failures. See live_analysis.json and verification.json. The recorded Windows GetTickCount64 clock resolves15.625ms; VALIDATION_CLOCK_NOTE.json preserves the corrected verifier tolerance without changing any observations.
