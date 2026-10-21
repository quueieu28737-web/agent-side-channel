"""Supplement table for the E8 pipeline runs (online cover, stand-in planners).

  python -B make_e8_table.py [out_dir]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R2 = HERE.parent
TAB = Path(sys.argv[1]) if len(sys.argv) > 1 else R2.parents[1] / "manuscript/tables"


def load(d):
    e6 = json.loads((d / "e6_dispatch_results.json").read_text())
    e7 = json.loads((d / "e7_network_results.json").read_text())["results"]
    return e6, e7


def cell(rows, tgt, cov, fr=None):
    r = next(x for x in rows if x["target"] == tgt and x["cover"] == cov and (fr is None or x["framing"] == fr))
    return f"{100 * r['best_ba']:.1f} [{100 * r['best_ba_ci95'][0]:.0f},{100 * r['best_ba_ci95'][1]:.0f}]"


runs = [("Offline (E6/E7)", R2, {"cancel_const2": "cancel_const2_shadow", "decoy1": "decoy1_shadow", "shape_eq": "shape_eq_shadow"}, None),
        ("Online, scripted", HERE / "runs/scripted", {}, HERE / "runs/scripted/e8_summary.json"),
        ("Online, noisy scripted", HERE / "runs/noisy-scripted", {}, HERE / "runs/noisy-scripted/e8_summary.json")]
lines = []
for name, d, alias, summ in runs:
    e6, e7 = load(d)
    s = json.loads(summ.read_text()) if summ else None
    for cov in ("cancel_const2", "decoy1", "shape_eq"):
        c = alias.get(cov, cov)
        ovf = f"{100 * s['covers'][cov]['template_overflow_rate']:.1f}" if s else "0.0"
        ovh = next(x for x in e6 if x["target"] == "cancel" and x["cover"] == c)["call_overhead"]
        lines.append(f"{name} & {cov.replace('_', ' ')} & {cell(e6, 'cancel', c)} & {cell(e6, 'return', c)} & "
                     f"{cell(e7, 'cancel', c, 'const')} & {cell(e7, 'return', c, 'const')} & {ovh:.2f} & {ovf}\\\\")
    lines.append("\\midrule")
lines = lines[:-1]
s_s = json.loads((HERE / "runs/scripted/e8_summary.json").read_text())
s_n = json.loads((HERE / "runs/noisy-scripted/e8_summary.json").read_text())
tex = r"""\section{Autonomous-agent pipeline (E8) and online cover}\label{app:e8}
\path{experiments/sp2027-r2/agent/} runs tool-calling agents and a user simulator on the 115 retail tasks, applies \emph{online} cover (decided before each real call from the history only, with a final flush) and replays every session over TLS. Because sandboxed cover and framing never reach the agent, one trajectory per task and seed serves all policies. No LLM was available for this revision; the rows below use stand-in planners and validate the pipeline. The scripted planner replays reference programs (native reward """ + f"{s_s['native_reward']:.2f}" + r"""); the noisy planner inserts extra reads before each reference call with probability 0.3 (""" + f"{s_n['mean_real_calls']:.1f}" + r""" versus """ + f"{s_s['mean_real_calls']:.1f}" + r""" real calls per session). These are synthetic results, not agent measurements.
\begin{table*}[!ht]\centering\scriptsize
\caption{Best held-out balanced accuracy (\%) [95\% task-cluster interval] for offline versus online cover. Const.: constant framing on the agent--tool link. Calls+: cover calls per real call. Overflow: sessions whose real calls exceed the shape template or the cancellation target.}
\begin{tabular}{@{}llrrrrrr@{}}\toprule
Planner / cover timing & Cover & Dispatch C & Dispatch R & Const.\ C & Const.\ R & Calls+ & Overflow (\%)\\\midrule
""" + "\n".join(lines) + r"""
\bottomrule\end{tabular}\end{table*}
"""
(TAB / "supp-e8.tex").write_text(tex)
print("wrote", TAB / "supp-e8.tex")
