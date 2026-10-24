# Exp 4 WAN Extension: Live Tool Timing, Flush Detection, and Constant-Rate Tunnels Under Netem Latency and Jitter

This experiment evaluates the timing side-channel claims of Exp~4 (archived E13) under realistic Wide Area Network (WAN) latency and jitter conditions.

## Motivation and Reviewer Feedback

In the original E13 evaluation, tool execution and ciphertext encapsulation were measured across local loopback (`127.0.0.1`), where transit latency is minimal (< 0.5 ms) and network jitter is negligible. Academic reviewers correctly note that loopback evaluation yields an optimistic view of timing-channel attackers and defense overheads:
1. Local execution gaps are cleanly preserved, allowing timing-aware detectors to isolate flush phases and request boundaries with high precision.
2. The fixed-rate tunnel slot horizon (133 slots at 2 ms = 266 ms) was calibrated under loopback execution times, ignoring propagation delays.

To resolve this limitation, we implement real network emulation directly matching Linux `tc netem` parameters:
- **WAN Mild**: 20 ms one-way delay, 5 ms uniform jitter (`tc netem delay 20ms 5ms`). Round-trip network latency is ~40 ms ± 7 ms.
- **WAN Realistic**: 50 ms one-way delay, 10 ms uniform jitter (`tc netem delay 50ms 10ms`). Round-trip network latency is ~100 ms ± 14 ms.

## Questions and Falsifiable Outcomes

1. **Flush Detection Robustness**: Does the trained random forest flush detector maintain its high detection accuracy (90.4% BA, 0.967 AUROC in loopback) when packet inter-arrival times are perturbed by 5–10 ms jitter?
   - *Outcome A (Maintained)*: High AUROC / BA confirms that macroscopic call structure (e.g. cumulative volume, relative duration, inter-call density) suffices even under WAN noise.
   - *Outcome B (Degraded)*: Drop in AUROC / BA identifies an honest empirical boundary, proving that fine-grained local timing features do not survive WAN transmission.

2. **Intent Inference (BA)**: Do size/order, timing/direction, and joint intent classifiers maintain their inference advantage over defended traffic?
   - Size/order features are packet-timing invariant and should remain completely stable.
   - Timing/direction features should reflect WAN perturbation.
   - Joint and flush-stripped joint attacks reveal whether flush stripping remains viable under WAN conditions.

3. **Tunnel Operational Feasibility**: Does a 2 ms fixed-rate constant tunnel (133 slots = 266 ms horizon) continue to provide full state-preserving execution under WAN latency?
   - In serial multi-turn tool interaction, sequential requests cannot be dispatched until previous responses arrive over the WAN.
   - If round-trip latency exceeds the available slot window, the finite horizon is exhausted before episode completion, exposing the operational limits of loopback-sized tunnels.

## Protocol and Evaluation Grid

- **Evaluated Defenses**:
  - `raw`: Undefended baseline
  - `padding`: Per-call constant framing (caps + 256 bytes)
  - `shadow_serial`: Serial prefix-only cover policy with post-episode flush
  - `tunnel_2ms`: RFC-style fixed-cell bidirectional encapsulation (4,096 bytes per cell, 2 ms cadence, 133 slots)
- **Workload**: All 276 test episodes from the pinned disjoint customer split (46 test tasks x 3 repeats x 2 prompt arms = 276 episodes).
- **Execution Invariant**: Real tool executions mutate an in-memory database; real response strings must match saved model observations; final database state must match expected ground truth.
