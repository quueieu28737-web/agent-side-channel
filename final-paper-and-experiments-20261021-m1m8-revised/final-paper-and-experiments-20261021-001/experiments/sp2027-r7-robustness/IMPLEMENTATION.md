# E14 implementation and limits

## Common observation and costs

Measured rows reuse E13 ciphertext record sizes, directions and monotonic completion timestamps. They retain actual last-real-response and traffic-finish clocks. Offline rows transform the **same undefended captures**. Cell adapters split each record's `ciphertext_length - 24` into up-to-512-byte fragments, then pad each cell to 512 plaintext bytes and charge 24 AEAD bytes and the five-byte TLS header. This is an RPC/TLS adaptation, not Tor's exact circuit framing. Each abstract fragment derived from input record sizes has a private integrity ID: adapters assert preserved size/order and no scheduling before release; these IDs never enter an attack feature. No application payload is decrypted or compared, and offline output is not executed. See `ERRATA.md` for this clarification and the post hoc power-grid extension to 400.

The WF controls do not call any backend, so their call ratio is 1. Actual shadow rows retain E13's extra tool calls. A record bucket control pads each input record to a 1024-byte plaintext multiple. Classical adapters do not inherit the original papers' accuracy or deployment guarantees. No claim is made that one fixed default is the globally optimal implementation of a defense.

## Classical mechanism adaptations

| Method | Mechanism retained | RPC adaptation / excluded claim | Source |
|---|---|---|---|
| Tamaraw | Fixed cells, asymmetric constant-direction rates, geometrically randomized total-length rounding in blocks of 50 | 40/12 ms and 4/1.2 ms; causal input-order replay propagates queued delay; no actual bandwidth contention or Tor implementation | Cai et al., CCS 2014; public `websitefingerprinting/WebsiteFingerprinting/defenses/tamaraw/tamaraw.py` |
| FRONT | Uniform dummy count; independent Rayleigh window per direction; cancel unsent padding when the real trace finishes | Budget and time window are scaled using training RPC captures; no fake claims of production zero-latency under contention | Gong and Wang, USENIX Security 2020, §4.2 |
| WTF-PAD | Send/receive-triggered adaptive padding, burst/gap/wait, histogram token removal/refill and infinity outcomes | Clean RPC mechanism adaptation: empirical training-IAT histogram, .1 burst infinity / .25 gap infinity, real events reset burst, at most 64 insertions per input gap; unlike the original simulator's fitted log-normal configurations; no tail padding | Juarez et al., ESORICS 2016; `wtfpad/wtfpad/src/adaptive.py` |
| Walkie-Talkie | Half-duplex burst maximum with a decoy burst sequence, plus decoy-only tail | Random training donor excluding the same customer, not sensitive/non-sensitive symmetric pair assignment; this cannot inherit WT's indistinguishability argument | Wang and Goldberg, USENIX Security 2017, §4.3 |

Sources inspected on 2026-10-24. Reference URLs: <https://github.com/websitefingerprinting/WebsiteFingerprinting/blob/master/defenses/tamaraw/tamaraw.py>, <https://www.usenix.org/system/files/sec20-gong.pdf>, <https://github.com/wtfpad/wtfpad/blob/master/src/adaptive.py>, <https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-wang-tao.pdf>.

The shifted FRONT calibration deliberately uses only customers in the lower half of training mean cell counts for its budget/window. All training customers remain in D2 attacker fitting and every test example remains in evaluation. This is a controlled in-population calibration mismatch, not a new environment or model transfer.

## Stronger attackers

Seven families, fixed before scoring: majority, logistic regression, gradient boosting, random forest, extra trees, forest-leaf nearest neighbors and a trainable 1D CNN. The leaf attack uses 200 random-forest leaves and Hamming-distance 3-nearest neighbors; it is **k-FP-style**, not a byte-identical reproduction of Hayes and Danezis' original feature extractor. Tabular inputs add cumulative signed sizes and directional-burst counts to E13's existing direction/size/timing features. CNN has two convolutional layers, 16/32 channels, mean/max pooling, weighted binary cross-entropy, Adam for 50 epochs and a fixed seed. Inputs are direction, log length, log interarrival and an occupancy mask. At most 512 cells are retained (first/last halves); the number truncated is saved. Tabular learners retain full-trace aggregate counts.

Training data are defended under the same public configuration as the evaluated data: D2 is the primary defense-aware threat model. It is finite empirical adversarial training, not an optimization over all possible attackers or unlimited queries. Existing E13 detector/profile attacks are unioned into each measured condition's suite, and the maximum is reselected in every bootstrap draw. All models, all scores and all configurations are retained, including negative outcomes.

## Distinct time semantics

Plot measured E13 tool-response latency separately from offline scheduled-packet latency. FRONT/WTF-PAD add no delay **in their trace transformation**, not in a real saturated link. Tamaraw/WT delays propagate input-order waits in an offline causal replay. Neither measures LLM thinking, replanning, WAN time or production quota contention. Do not rank deployment latency across these two panels as if measured under one live scheduler. Byte/attack comparisons use the same held-out trajectories and accounting; they locate only the evaluated operating points.
