"""Print standalone proposed LaTeX table; does not alter manuscript."""
import json
from pathlib import Path
H=Path(__file__).resolve().parent
r=json.loads((H/"results.json").read_text());d=json.loads((H/"descriptive_metrics.json").read_text())
lookup={(x["prompt"],x["condition"]):x for x in d["reports"]}
print(r"\begin{tabular}{llrr}\toprule")
print(r"Condition & Learner & BA (95\% CI) & AUROC (95\% CI)\\\midrule")
for x in r:
 if x["prompt"]!="baseline":continue
 for name,v in x["learners"].items():
  a=lookup[x["prompt"],x["condition"]]["learners"][name]
  fmt=lambda p,ci:f"{100*p:.1f} [{100*ci[0]:.1f}, {100*ci[1]:.1f}]"
  label=x["condition"].replace("_",r"\_")
  print(f"{label} & {name} & {fmt(v['ba'],v['ci95'])} & {fmt(a['auroc'],a['auroc_ci95'])}"+r"\\")
print(r"\bottomrule\end{tabular}")
print("% Both prompts have exactly identical 20 aggregate feature vectors and results; not independent replications. 15 customers, 9 positive/11 negative instances. Fixed-prediction customer bootstrap, no refit. Single fixed label shuffle is not a permutation p-value. Original score orientation; no flipping.")
