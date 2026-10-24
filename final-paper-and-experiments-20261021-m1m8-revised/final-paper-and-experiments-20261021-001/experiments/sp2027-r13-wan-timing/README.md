# Exp 4 WAN Network Emulation Extension (`sp2027-r13-wan-timing`)

## 1. Motivation and Reviewer Comment
In prior evaluations of Exp 4 (`sp2027-r6-timing`), tool RPC timings were collected over a local loopback link ($0\text{ ms}$ delay, $0\text{ ms}$ jitter). Reviewers raised the concern that a loopback environment presents an overly optimistic timing attack scenario. Specifically:
> "回环链路让时序结论偏乐观，审稿人一定会问。用 tc netem 在同一流程加 20/50 ms 延迟和 5–10 ms 抖动，重跑 serial shadow、per-call constant、2 ms tunnel，看 flush 检测和 BA 是否保持。无论结果如何都能写：保持，则稳健；下降，则是诚实的边界。"

This experiment directly addresses this concern by executing all 276 customer-held-out test episodes across two prompt arms (`baseline` and `rules`) under high-fidelity wide-area network emulation.

---

## 2. Emulation Methodology
We implemented `NetemRelay` in `transport.py`, which provides a bidirectional transparent TLS 1.2 proxy emulating Linux `tc netem` with packet delay and jitter:
* **Mild WAN (`wan_20ms`)**: $20\text{ ms}$ one-way delay, $5\text{ ms}$ normal jitter ($\sigma = 5\text{ ms}$), $40\text{ ms}$ nominal RTT.
* **Realistic WAN (`wan_50ms`)**: $50\text{ ms}$ one-way delay, $10\text{ ms}$ normal jitter ($\sigma = 10\text{ ms}$), $100\text{ ms}$ nominal RTT.
* **FIFO Guarantee**: Monotonically non-decreasing wire delivery times to prevent synthetic out-of-order packet reordering in stream sockets.
* **Feedback-Gated Execution**: For each agent episode, the client waits for the true decrypted tool response across the WAN link before releasing the subsequent planned action, faithfully mirroring multi-step agent execution over wide-area networks against live backend database clones.

---

## 3. Scale of Evaluation
* **Episodes**: 276 test episodes (138 standard baseline, 138 system-prompt rules) across 24 customers (5 cancel-positive, 7 return-positive).
* **Conditions Evaluated**:
  1. `raw`: Raw TLS transport.
  2. `padding`: Per-call constant framing.
  3. `shadow_serial`: Serial shadow cover with constant framing.
  4. `tunnel_2ms`: Complete 4096-byte fixed-rate tunnel at $2\text{ ms}$ cell intervals with a training-sized 133-slot horizon ($266\text{ ms}$).
* **Total Measured Sessions**:
  * `wan_20ms`: $276 \times 4 = 1,104$ sessions.
  * `wan_50ms`: $276 \times 4 = 1,104$ sessions.
  * Grand total: **2,208 new TLS sessions** collected and archived under `captures/`.

---

## 4. Key Findings

### 4.1 Flush Detection Holds Robustly Across WAN Conditions
Flush detection classifies whether a ciphertext record belongs to the active tool execution phase or the trailing dummy cover flush phase (15,278 records tested).

| Network Condition | Evaluated Detector | Flush Point BA | 95% CI | AUROC |
| :--- | :--- | :---: | :---: | :---: |
| **Loopback (E13)** | Frozen $D_{\text{loop}}$ | 90.4% | [88.3%, 92.5%] | 0.967 |
| **WAN 20ms / 5ms jitter** | Direct Transfer $D_{\text{loop}}$ | 89.4% | [87.2%, 91.7%] | 0.962 |
| | Adapted $D_{\text{WAN}}$ (5-fold CV) | 89.2% | [86.6%, 91.5%] | 0.958 |
| **WAN 50ms / 10ms jitter** | Direct Transfer $D_{\text{loop}}$ | 89.4% | [87.3%, 91.7%] | 0.963 |
| | Adapted $D_{\text{WAN}}$ (5-fold CV) | 89.0% | [86.5%, 91.3%] | 0.958 |

**Insight**: The flush detector is remarkably robust, dropping by only $\sim 1.0$ percentage point even under direct zero-shot transfer without WAN retraining. This is because the shift from feedback-gated real tool execution to un-gated cover flushes creates macroscopic density and inter-request timing transitions that easily survive $5\text{--}10\text{ ms}$ jitter.

### 4.2 Intent BA Degrades on Serial Shadow (Natural Jitter Obfuscation)
| Defense Condition | Metric | Loopback (0ms, 0ms) | WAN Mild (20ms, 5ms) | WAN Realistic (50ms, 10ms) |
| :--- | :--- | :---: | :---: | :---: |
| **Raw transport** | Full-Suite BA (Cancel / Return) | 91.7% / 86.4% | 91.7% / 86.4% | 91.7% / 86.4% |
| **Per-call constant** | Full-Suite BA (Cancel / Return) | 68.6% / 62.7% | 68.6% / 54.8% | 68.6% / 54.8% |
| **Serial shadow** | Full-Suite BA (Cancel / Return) | **61.4%** / 53.4% | **50.0%** / 50.7% | **54.0%** / 54.6% |
| **Full tunnel (2ms)**| Full-Suite BA (Cancel / Return) | 62.5% / 52.9% | 54.4% / 56.8% | 55.0% / 52.6% |

**Insight**: On loopback, sub-millisecond variations in database execution leaked intent, enabling the full attack suite to push cancellation BA to 61.4%. Over WAN, network jitter acts as natural timing noise that obscures fine-grained execution differences, bringing serial shadow cancellation BA down to chance ($50.0\%$) under 20ms/5ms and $54.0\%$ under 50ms/10ms.

### 4.3 Operational Boundaries: Tunnel Horizon Exhaustion
| Defense Condition | Metric | Loopback (0ms, 0ms) | WAN Mild (20ms, 5ms) | WAN Realistic (50ms, 10ms) |
| :--- | :--- | :---: | :---: | :---: |
| **Raw transport** | Status (Completed / Total) | 276 / 276 (100%) | 276 / 276 (100%) | 276 / 276 (100%) |
| | Real Chain p95 Latency | 15.4 ms | 506.4 ms | 1178.8 ms |
| **Per-call constant** | Status (Completed / Total) | 276 / 276 (100%) | 276 / 276 (100%) | 276 / 276 (100%) |
| | Real Chain p95 Latency | 16.6 ms | 504.8 ms | 1172.6 ms |
| **Serial shadow** | Status (Completed / Total) | 276 / 276 (100%) | 276 / 276 (100%) | 276 / 276 (100%) |
| | Real Chain p95 Latency | 26.2 ms | 855.4 ms | 1999.5 ms |
| **Full tunnel (2ms)**| Status (Completed / Total) | **276 / 276 (100%)** | **85 / 276 (30.8%)** | **5 / 276 (1.8%)** |
| | Horizon Exhausted Failures | 0 | 191 | 271 |

**Insight (The Honest Boundary)**:
A 133-slot tunnel ($266\text{ ms}$) sized on local loopback execution cannot accommodate multi-call agent workflows once network RTT adds $40\text{--}100\text{ ms}$ per tool round-trip. Multi-step trajectories run out of slots before backend tool responses can be received, leading to catastrophic failure ($69.2\%$ and $98.2\%$ horizon exhaustion). In contrast, serial shadow cover and per-call framing maintain $100\%$ task completion, zero response errors, and $100\%$ database state fidelity across all network conditions, scaling latency gracefully with network round trips.

---

## 5. Artifacts and Reproduction
* `experiment.py`: Collects live TLS sessions under WAN profiles (`--profile wan_20ms`, `--profile wan_50ms`, `--profile all`).
* `analyze.py`: Computes flush transfer/adapted CV metrics, intent Balanced Accuracy, and latency statistics (`--profile all`).
* `make_tables.py`: Generates formatted LaTeX tables (`tab_wan_flush.tex` and `tab_wan_controls.tex`).
* `manuscript/tables/r13-wan-flush.tex`: Integrated into Supplementary Evidence \S\ref{sec:wan-netem-eval}.
* `manuscript/tables/r13-wan-controls.tex`: Integrated into Supplementary Evidence \S\ref{sec:wan-netem-eval}.
* `manuscript/sections/42-live-timing-main.tex`: Updated with WAN robustness subsection.
* `manuscript/sections/41-live-timing.tex`: Updated with comprehensive WAN analysis and discussion.
