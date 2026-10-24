# R7 crossfit complete extended union

Posthoc known 690-episode Sol cohort; customer 5-fold OOF; direction and length only; zero timing channel. 2,000 customer-cluster bootstrap draws, suite maximum reselected per draw.

|Target|Prompt|Condition|BA [95% CI]|Max AUROC [95% CI]|BA winner|Wire ×|Calls ×|Criterion|
|---|---|---|---|---|---|---|---|---|
|cancel|baseline|jointconstant|0.605001909 [0.529110220, 0.724099640]|0.594469899 [0.532863027, 0.768639628]|D2_logreg|19.757871379|5.035505430|inconclusive|
|return|baseline|jointconstant|0.554593373 [0.518314193, 0.641591955]|0.533216198 [0.507150582, 0.687472343]|ext_D2_kfp_style|19.757871379|5.035505430|inconclusive|
|cancel|rules|jointconstant|0.587533410 [0.521251323, 0.716052169]|0.580596920 [0.536542772, 0.763484266]|D2_logreg|19.884291254|5.038043478|inconclusive|
|return|rules|jointconstant|0.594001004 [0.542363316, 0.688091819]|0.581388052 [0.536393536, 0.698195375]|D2_logreg|19.884291254|5.038043478|inconclusive|
|cancel|baseline|undefended|0.916666667 [0.820512821, 1.000000000]|0.978967799 [0.949064616, 1.000000000]|network_decode_count_rule|1.000000000|1.000000000|above_threshold|
|return|baseline|undefended|0.854919679 [0.766722274, 0.934030428]|0.897130187 [0.849414690, 0.964622255]|network_decode_count_rule|1.000000000|1.000000000|above_threshold|
|cancel|rules|undefended|0.907407407 [0.815432423, 0.988906250]|0.978267787 [0.954246839, 0.999456357]|network_decode_count_rule|1.000000000|1.000000000|above_threshold|
|return|rules|undefended|0.854919679 [0.765844089, 0.935900673]|0.879748159 [0.804995806, 0.955316265]|network_decode_count_rule|1.000000000|1.000000000|above_threshold|
|cancel|baseline|jointbucket1024|0.570733104 [0.500000000, 0.715287990]|0.579260532 [0.514324296, 0.768238158]|ext_D2_cnn|12.362019175|5.035505430|inconclusive|
|return|baseline|jointbucket1024|0.527108434 [0.500000000, 0.617493544]|0.535998159 [0.500000000, 0.683365098]|network_decode_gboost|12.362019175|5.035505430|inconclusive|
|cancel|rules|jointbucket1024|0.569014891 [0.501560245, 0.712054646]|0.573151330 [0.521592448, 0.770515917]|ext_D2_cnn|12.445245696|5.038043478|inconclusive|
|return|rules|jointbucket1024|0.526669177 [0.500000000, 0.650045518]|0.564884538 [0.531378086, 0.716140097]|ext_D2_kfp_style|12.445245696|5.038043478|inconclusive|

|Target|Prompt|Paired contrast|BA difference [95% CI]|
|---|---|---|---|
|cancel|baseline|undefended minus jointconstant|0.311664758 [0.153149155, 0.410139512]|
|cancel|baseline|undefended minus jointbucket1024|0.345933562 [0.151283864, 0.464061426]|
|cancel|baseline|jointconstant minus jointbucket1024|0.034268805 [-0.010135017, 0.121541966]|
|cancel|rules|undefended minus jointconstant|0.319873998 [0.131408074, 0.442141529]|
|cancel|rules|undefended minus jointbucket1024|0.338392516 [0.141582153, 0.457688492]|
|cancel|rules|jointconstant minus jointbucket1024|0.018518519 [-0.055847597, 0.100892723]|
|return|baseline|undefended minus jointconstant|0.300326305 [0.147918024, 0.391713878]|
|return|baseline|undefended minus jointbucket1024|0.327811245 [0.207622563, 0.388708117]|
|return|baseline|jointconstant minus jointbucket1024|0.027484940 [-0.048972198, 0.124041471]|
|return|rules|undefended minus jointconstant|0.260918675 [0.111419718, 0.366096881]|
|return|rules|undefended minus jointbucket1024|0.328250502 [0.189721509, 0.397854091]|
|return|rules|jointconstant minus jointbucket1024|0.067331827 [-0.012002378, 0.147046813]|
