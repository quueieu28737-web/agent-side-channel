# R8 matched-seven saved-result tables

All values below are descriptive. CI in percent. Every row uses 138 episodes / 24 test customers per prompt. Measured and simulated latency must not be compared as a deployment ranking.

| Prompt | Condition | Cancel BA [CI] / AUC | Return BA [CI] / AUC | Bytes × | Calls × | Last-real p95 ms | Finish p95 ms | Evidence |
|---|---|---|---|---:|---:|---:|---:|---|
| baseline | raw | 84.3056 [72.6935, 97.4155] / 0.836343 | 76.8831 [62.1772, 90.3510] / 0.828283 | 1.00000000 | 1.00000000 | 15.44557000 | 15.46634000 | measured_E13 |
| baseline | padding | 53.1944 [50.0000, 69.4895] / 0.604167 | 59.0909 [50.0000, 73.8095] / 0.655988 | 3.92222229 | 1.00000000 | 16.64299000 | 16.67819000 | measured_E13 |
| baseline | walkie_talkie | 50.0000 [50.0000, 66.9754] / 0.525926 | 56.6667 [51.6663, 67.7924] / 0.606926 | 2.04038069 | 1.00000000 | 16.60948156 | 16.60948160 | offline_trace_transform |
| baseline | shadow_serial | 50.0000 [50.0000, 64.9962] / 0.547685 | 52.8571 [50.0000, 60.3390] / 0.526118 | 15.10601622 | 3.82665331 | 26.23059500 | 46.62123500 | measured_E13 |
| baseline | shadow_parallel2 | 50.0000 [50.0000, 59.7418] / 0.500000 | 57.3160 [54.9674, 69.2487] / 0.595960 | 15.10601622 | 3.82665331 | 20.84841500 | 37.40902000 | measured_E13 |
| baseline | tunnel_2ms | 59.8611 [54.5588, 67.2809] / 0.708333 | 55.1948 [50.1077, 60.9502] / 0.567100 | 125.70596259 | 1.00000000 | 56.40077500 | 270.43205500 | measured_E13 |
| baseline | tunnel_5ms | 54.5833 [50.0000, 70.4948] / 0.618056 | 53.6797 [51.2744, 61.1833] / 0.550649 | 125.70596259 | 1.00000000 | 112.30482500 | 666.64030000 | measured_E13 |
| rules | raw | 84.7222 [75.1632, 98.4848] / 0.851389 | 78.2684 [63.2878, 92.2244] / 0.817893 | 1.00000000 | 1.00000000 | 15.65964500 | 15.69509500 | measured_E13 |
| rules | padding | 59.4444 [50.0000, 77.5478] / 0.593750 | 61.8615 [50.0000, 77.3825] / 0.562771 | 3.95029489 | 1.00000000 | 15.49754000 | 15.53818000 | measured_E13 |
| rules | walkie_talkie | 51.3889 [50.0000, 68.7674] / 0.606481 | 56.2771 [50.0000, 66.5587] / 0.558153 | 2.23338019 | 1.00000000 | 15.77892687 | 15.77892695 | offline_trace_transform |
| rules | shadow_serial | 56.1111 [50.0000, 76.2411] / 0.589352 | 59.7835 [53.7631, 69.4444] / 0.625541 | 15.46845781 | 3.88211382 | 23.85970000 | 41.82594000 | measured_E13 |
| rules | shadow_parallel2 | 56.9444 [50.0000, 69.1662] / 0.566204 | 57.0563 [53.7926, 67.9177] / 0.638961 | 15.46845781 | 3.88211382 | 20.70062000 | 36.54818000 | measured_E13 |
| rules | tunnel_2ms | 52.7778 [51.1905, 61.6139] / 0.503704 | 55.2814 [51.6667, 66.2395] / 0.577201 | 128.38382074 | 1.00000000 | 48.84085000 | 267.91390500 | measured_E13 |
| rules | tunnel_5ms | 58.3333 [50.0000, 67.8694] / 0.538889 | 54.3290 [51.5624, 62.6019] / 0.594517 | 128.38382074 | 1.00000000 | 112.94829000 | 666.55638000 | measured_E13 |

## Existing estimated-flush-removal intent attacks

Three intent models plus majority; train segmentation is customer OOF. This is already executed, not a proposed result.

| Prompt / scheduler | Target | BA [95% CI] | AUROC | Valid draws |
|---|---|---|---:|---:|
| baseline / shadow_serial | cancel | 57.7778 [50.0000, 70.7346] | 0.583333 | 1988 |
| baseline / shadow_serial | return | 53.4199 [50.0000, 64.6465] | 0.529870 | 2000 |
| baseline / shadow_parallel2 | cancel | 50.0000 [50.0000, 64.0491] | 0.500000 | 1988 |
| baseline / shadow_parallel2 | return | 50.0000 [50.0000, 56.7266] | 0.500000 | 2000 |
| rules / shadow_serial | cancel | 50.1389 [50.0000, 55.5940] | 0.500000 | 1988 |
| rules / shadow_serial | return | 60.6926 [50.8333, 70.9478] | 0.621645 | 2000 |
| rules / shadow_parallel2 | cancel | 50.8333 [50.0000, 61.7052] | 0.541204 | 1988 |
| rules / shadow_parallel2 | return | 53.9827 [50.0000, 66.9903] | 0.527561 | 2000 |
