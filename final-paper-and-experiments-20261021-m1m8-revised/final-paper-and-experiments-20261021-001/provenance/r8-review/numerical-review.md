# R8 numerical review

PASS: make_tables --check; 13 control rows, 4 flush rows, exact supplementary generator match.

- E9: bytes 15.393631058426; calls 3.826653306613; raw BA [0.9722222222222222, 0.9402597402597402]; source sp2027-r4-full-20261023/results.json / utility baseline shape_const; results baseline raw network.
- E10: bytes 19.757871378773; calls 5.035505430242; raw BA [0.9166666666666667, 0.8549196787148594]; source sp2027-r7-crossfit/detailed_results.json / baseline jointconstant and undefended cells.
- E13/14: bytes 15.106016216696; calls 3.826653306613; raw BA [0.9166666666666667, 0.8636363636363636]; source sp2027-r6-timing/results.json / resources baseline shadow_serial; E14 union raw cells.

- No numerical column swaps or incorrect rounding found in requested tables.
- Cohort raw BA and byte ratio are distinct estimands, not a same-condition raw-cost pair: the caption correctly says byte ratios price joint constant shaping.
- E9 15.39 and E13 15.11 are not contradictory: different RPC serialization/envelope and each own undefended denominator.
- E10 19.76/5.04 uses fold-specific analytic calibration on 345 trajectories per prompt, not measured E13 timing or E9 pretest template.
- Cohort sample counts cover both prompts, but BA/byte/call values are standard prompt; positive customers are unique shared customers, not doubled with prompt.
- r8-controls upper BA is the full-union upper 95% bound; common-seven and full-union columns are correctly distinct.
- S simulated rows correctly omit RPC latency; M p95 is last real response, excluding planner/WAN and excluding tail drain.
- Flush table uses the 138-episode-per-prompt intent task after estimated removal, not 15278 record-level detector BA.
- 47 matches its generator exactly; cluster table uses 345 trajectories/53 customers, not 345 independent customers.

This numerical review does not rerun the science verifier or model fitting. It validates saved-result mappings, units and generated text.
