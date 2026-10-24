# R7 strengthened E12 oracle localization

Posthoc known cohort. Full-view OOF reused from verified R7 crossfit. All 11 attacks; 2,000 common customer-cluster draws, max reselected each draw. Direction and length only; zero timing.

|Target|Prompt|Oracle view|BA [95% CI]|Max AUROC [95% CI]|BA winner|Criterion|
|---|---|---|---|---|---|---|
|cancel|baseline|full|0.916666667 [0.820512821, 1.000000000]|0.978967799 [0.949064616, 1.000000000]|network_decode_count_rule|above_threshold|
|cancel|baseline|no_writes|0.627815960 [0.545603098, 0.753332767]|0.611461117 [0.532602266, 0.768452701]|ext_D2_knn|inconclusive|
|cancel|baseline|writes_only|0.916666667 [0.820512821, 1.000000000]|0.973144966 [0.935830212, 1.000000000]|network_decode_count_rule|above_threshold|
|cancel|rules|full|0.907407407 [0.815432423, 0.988906250]|0.978267787 [0.954246839, 0.999456357]|network_decode_count_rule|above_threshold|
|cancel|rules|no_writes|0.687476136 [0.594294679, 0.802395363]|0.690403462 [0.592681295, 0.822058841]|ext_D2_knn|inconclusive|
|cancel|rules|writes_only|0.907407407 [0.813715686, 0.988906250]|0.968181240 [0.930270362, 0.997508503]|network_decode_count_rule|above_threshold|
|return|baseline|full|0.854919679 [0.766722274, 0.934030428]|0.897130187 [0.849414690, 0.964622255]|network_decode_count_rule|above_threshold|
|return|baseline|no_writes|0.599021084 [0.522259884, 0.717849460]|0.656689257 [0.571209788, 0.788599587]|D2_logreg|inconclusive|
|return|baseline|writes_only|0.849272088 [0.787884838, 0.940013369]|0.906375502 [0.863967224, 0.973196640]|network_decode_gboost|above_threshold|
|return|rules|full|0.854919679 [0.765844089, 0.935900673]|0.879748159 [0.804995806, 0.955316265]|network_decode_count_rule|above_threshold|
|return|rules|no_writes|0.665223394 [0.565394782, 0.777417177]|0.664114793 [0.578545533, 0.807115170]|ext_network_decode_rf|inconclusive|
|return|rules|writes_only|0.851342871 [0.785515584, 0.936693404]|0.916938588 [0.861972306, 0.978499164]|ext_D2_rf|above_threshold|

|Target|Prompt|Paired oracle contrast|BA difference [95% CI]|
|---|---|---|---|
|cancel|baseline|full minus no_writes|0.288850706 [0.107157382, 0.419281200]|
|cancel|baseline|full minus writes_only|0.000000000 [0.000000000, 0.000000000]|
|cancel|rules|full minus no_writes|0.219931271 [0.060269626, 0.350699610]|
|cancel|rules|full minus writes_only|0.000000000 [0.000000000, 0.000000000]|
|return|baseline|full minus no_writes|0.255898594 [0.109922322, 0.353804091]|
|return|baseline|full minus writes_only|0.005647590 [-0.069063756, 0.025155255]|
|return|rules|full minus no_writes|0.189696285 [0.060214918, 0.300515898]|
|return|rules|full minus writes_only|0.003576807 [-0.074867972, 0.045045504]|
