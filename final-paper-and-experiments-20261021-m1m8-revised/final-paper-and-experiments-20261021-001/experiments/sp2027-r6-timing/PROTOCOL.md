# E13: timing attacks, live tool latency, and a complete fixed-rate tunnel

This is a new measurement experiment on the existing 690 real-agent trajectories,
not 690 new model generations or a new customer population. The original R4 data,
split, inference configuration, calibration, and statistical threshold are unchanged.

## Questions and falsifiable outcomes

1. Does adding observable arrival timing improve intent inference over direction,
   record size and order? Compare fixed suites under three feature projections,
   with paired customer-bootstrap differences. A non-positive difference does not
   establish immunity to all timing attackers.
2. Can a trained observer locate the end flush or distinguish real and cover
   requests? Learn only from training captures; test on disjoint customers. Train
   the intent attack on out-of-fold estimated flush-stripped traces, never an
   oracle test boundary.
3. What is the actual latency/resource trade-off of serial cover, two in-flight
   calls, and full traffic-flow shaping? Measure live RPC latency and state rather
   than infer delay from call multipliers.
4. At the passive client-to-gateway TLS boundary, does complete fixed-rate
   encapsulation offer protection without executing cover tools? A tunnel win is
   evidence that the appropriate intervention depends on the observer boundary,
   not a reason to omit the baseline.

## Inputs and scope

- 115 tasks, two prompt arms, three saved model repeats: 690 trajectories.
- Original customer-disjoint split: 414 training / 276 test trajectories.
- Six conditions per trajectory: raw, per-call constant framing, serial shadow
  cover, shadow cover with at most two outstanding RPCs, and tunnels with 2 ms
  and 5 ms target cell intervals. Total: 4,140 new measured TLS sessions.
- Each saved real action is submitted to a real running local tool RPC server.
  The driver waits for its response before releasing the next real action.
  Response text is checked against the saved observation. Actual tool functions
  mutate a live cloned benchmark database; cover mutates a separate clone.
- This is a feedback-synchronized **tool execution** loop. The next action is
  fixed by the saved model trajectory; there is no new LLM replanning or user
  generation. Clocks exclude those operations and WAN latency. No artificial
  read/write delays are inserted. These are measurements of the local prototype,
  not production latency estimates.

## Transport, scheduling, and trust boundary

All conditions share a byte-transparent ciphertext relay, TLS 1.2
ECDHE-RSA-AES128-GCM-SHA256, TCP_NODELAY, server implementation, and workload.
The relay timestamps received ciphertext chunks with `perf_counter_ns`; parsed
records inherit the timestamp of their final observed chunk. It also preserves
the original chunk log. Handshake and closure traffic are outside the application
record projection. Each session uses a fresh connection, and one session runs at
a time to avoid cross-session load confounding.

The full tunnel implements application-stream fragmentation, reassembly and dummy
traffic in **both** directions. Each slot sends 4,096 plaintext bytes, including an
encrypted four-byte useful-length field. Empty cells do not execute tools. Thus
data cells and dummy cells have the same ciphertext record length. Both directions
continue to the same fixed horizon even after the last tool response. This is a
TLS prototype of the fixed-size/constant-rate design principle, not an implementation
or benchmark of the IPsec wire format in RFC 9347.

The training-only slot budget is:

`max(128, ceil(1.5 * max_training sum(ceil(request_bytes/4092) + ceil(response_bytes/4092) + 4)) + 16)`.

It yields 133 slots: 266 ms at 2 ms and 665 ms at 5 ms. The rule uses only training
message sizes, not test messages or labels. It is a finite service horizon;
overflow/timeouts are retained as failures, not extended with secret-dependent
traffic. Per-call caps are frozen R4 caps plus 256 bytes for the RPC envelope,
with whole-cap overflow buckets. Neither threshold nor operating point is selected
using test outcomes.

The cover policy reuses the original training donors, template and random seed.
The scheduler sees the executed prefix; it flushes remaining counts only when
the driver declares the episode complete. Cover returns never reach the planner
projection. The gateway knows the encrypted real/cover marker; the passive link
observer does not. This study does not protect the gateway's own commit log.

Windows timers can wake early. `until()` rechecks the monotonic measurement clock
after every sleep. Actual lateness, catch-up bursts and queues are saved; no ideal
timestamps are substituted. Initial early-wakeup development captures are retained
under `development/` and excluded from the formal dataset. The corrected protocol
hash and collector sources are frozen before the formal train/test measurements.

## Attack fitting and statistical analysis

- Training captures precede all test captures. All classifiers and segmentation
  models are fit and hashed before starting test capture.
- Intent suites contain training majority, balanced logistic regression (C=1),
  100-tree gradient boosting, and 200-tree random forest (leaf minimum 2).
- Features are only observable direction, length, arrival gaps, duration, burst
  counts, quantiles, first/last 32 positions, and a largest-gap change point.
  Internal clocks, tool names, RPC IDs, real/cover flags and true flush boundaries
  are excluded from intent and detector features.
- The full adaptive suite is the union of all declared feature views. An observer
  can ignore time or choose the unstripped trace; the full suite never receives
  credit for a weaker feature-specific classifier. The suite maximum is selected
  again within every bootstrap draw.
- Flush and real/cover detectors: 80-tree forests, depth 8, leaf minimum 5.
  Flush training transformations use three customer-disjoint out-of-fold models;
  the frozen full-training detector transforms test traces. A maximum-likelihood
  single change point removes the estimated suffix before the fourth intent view.
- Intent results retain tasks and repeats inside their customer clusters. 2,000
  common bootstrap draws resample the suite maximum and paired differences.
  Intervals condition on fitted predictions. The original absolute criterion
  (BA upper bound < 0.60 and AUROC < 0.65) is reported without amendment.
- Detector BA uses customer-cluster uncertainty; AUROC is also reported.
- Latency: real-call, first response, last real response, whole traffic duration,
  service time, scheduler queue, cell lateness, p50/p95, observed timeout/failure,
  and a descriptive 100 ms per-call deadline count. The 100 ms value is a reporting
  reference, not a deployment SLA or a post hoc success criterion.
- Utility: exact real-response preservation and final database equality against
  unprotected execution of the same actions. Preserved original benchmark reward
  is inherited under these invariants, not a fresh model reward trial.

## Integrity gates

Every expected session is retained. Full results require 2,484 training and 1,656
test files; no silent retry or best-of-run replacement. Check exact model/input/
protocol hashes, original split, fixed tunnel record count and length, absence of
early slot sends, pending queues, response/state equality, and reproduction of
all reported numbers from saved predictions and measurements. Failures remain
visible even when a subsequent implementation revision is necessary.

No claim of independent human recoding, new population validation, or guaranteed
absolute security is supplied by this experiment.

## Version 2 correction and full recollection

The complete version-1 pass and its fitted results are preserved under the
development archive. A subsequent capture-integrity check found two of 1,380
tunnel captures missing trailing dummy records (265 and 230 rather than 266),
despite successful real responses and state preservation. Local send completion
had been incorrectly treated as remote receive completion. Version 2 explicitly
waits until both TLS endpoints have consumed all 133 cells before closing.
The **entire** 4,140-session cohort is recollected; the two cases are not selectively
replaced and version-1 results are not pooled into the final analysis.

The same correction phase restores the legacy request/response size histograms
and the E9-style training-only tool-size profiler (decoded histogram gradient
boosting and count-threshold attacks) for non-tunnel conditions. Profiling labels
come only from training RPCs; test decoding sees ciphertext sizes only. These
attacks join the size/order view and therefore the full adaptive suite. The
version-1 generic suite was weaker on raw transport, motivating this stronger
control; the chronology is disclosed rather than calling this a previously
unseen-population confirmatory analysis. The original absolute threshold, customer
split, six conditions, horizon rule and full sample size are unchanged. Final
attacker fitting is again completed before version-2 test measurement.
