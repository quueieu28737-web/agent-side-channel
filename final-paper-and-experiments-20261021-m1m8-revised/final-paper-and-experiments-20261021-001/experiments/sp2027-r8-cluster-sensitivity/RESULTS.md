# R8 cluster sensitivity

Post hoc deterministic sensitivity conditional on saved fitted OOF predictions; no new customers or retraining uncertainty

Customer-equal BA weights each customer equally within each true class; mixed-label customers contribute separately to both class rates. Deletions remove the entire positive customer, including its negative tasks. Ranges are influence ranges, not confidence intervals.

| Prompt / condition | Target | Episodes / customers | Positive episodes / customers | Mixed customers | Episode suite BA % | Customer-equal suite BA % | LOO-positive episode BA range % | LOO-positive customer-equal BA range % | Valid deletions |
|---|---|---|---|---:|---:|---:|---|---|---:|
| baseline / undefended | cancel | 345 / 53 | 54 / 14 | 4 | 91.6667 | 94.0476 | 90.6250–96.6667 | 93.5897–96.1538 | 14 |
| baseline / undefended | return | 345 / 53 | 96 / 18 | 8 | 85.4920 | 85.7558 | 84.1744–87.6471 | 84.9790–87.9617 | 18 |
| baseline / jointbucket1024 | cancel | 345 / 53 | 54 / 14 | 4 | 57.0733 | 54.8034 | 54.2955–61.5872 | 53.7045–57.5507 | 14 |
| baseline / jointbucket1024 | return | 345 / 53 | 96 / 18 | 8 | 52.7108 | 56.4779 | 51.0442–54.7223 | 55.1072–58.0483 | 18 |
| baseline / jointconstant | cancel | 345 / 53 | 54 / 14 | 4 | 60.5002 | 58.9572 | 57.2595–61.9817 | 56.8967–60.7429 | 14 |
| baseline / jointconstant | return | 345 / 53 | 96 / 18 | 8 | 55.4593 | 53.1546 | 53.3682–56.7165 | 51.3680–54.2712 | 18 |
| rules / undefended | cancel | 345 / 53 | 54 / 14 | 4 | 90.7407 | 92.8571 | 89.5833–95.5556 | 92.3077–94.8718 | 14 |
| rules / undefended | return | 345 / 53 | 96 / 18 | 8 | 85.4920 | 85.8527 | 84.1744–87.6471 | 85.0782–88.0586 | 18 |
| rules / jointbucket1024 | cancel | 345 / 53 | 54 / 14 | 4 | 56.9015 | 54.7065 | 54.1237–61.4154 | 53.6076–57.4538 | 14 |
| rules / jointbucket1024 | return | 345 / 53 | 96 / 18 | 8 | 52.6669 | 53.4238 | 51.6600–54.2247 | 52.4434–53.9140 | 18 |
| rules / jointconstant | cancel | 345 / 53 | 54 / 14 | 4 | 58.7533 | 56.6002 | 55.1654–60.8570 | 54.1582–58.1237 | 14 |
| rules / jointconstant | return | 345 / 53 | 96 / 18 | 8 | 59.4001 | 60.3987 | 57.5929–62.1659 | 59.2776–62.2257 | 18 |
