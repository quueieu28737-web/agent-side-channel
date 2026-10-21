"""Generate the LaTeX tables for E5-E7 and the prediction outcomes directly from
the saved JSON results, so that manuscript numbers cannot drift from artifacts."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
TAB = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[1] / "manuscript/tables"
e5 = json.loads((HERE / "e5_streaming_results.json").read_text())
e6 = json.loads((HERE / "e6_dispatch_results.json").read_text())
e7 = json.loads((HERE / "e7_network_results.json").read_text())
pr = json.loads((HERE / "PREREGISTRATION_OUTCOMES.json").read_text())["outcomes"]

pct = lambda x: f"{100 * x:.1f}"
ba = lambda r: f"{100 * r['best_ba']:.1f}"
baci = lambda r: f"{100 * r['best_ba']:.1f} [{100 * r['best_ba_ci95'][0]:.0f},{100 * r['best_ba_ci95'][1]:.0f}]"


def g5(tls, tgt, pol):
    return next(r for r in e5 if r["tls"] == tls and r["target"] == tgt and r["policy"] == pol)


NAMES5 = [("buffered_raw", "Buffered, unpadded"), ("buffered_cap", "Buffered, training cap"),
          ("tok_raw", "Stream, per token"), ("tok_randpad", "+ random event pad"),
          ("tok_const", "+ constant event size"), ("batch8_const", "8-token batches, const."),
          ("tok_const_cap", "Const.\\ events + count cap")]
rows = []
for pol, nm in NAMES5:
    a, b = g5("1.3", "T1", pol), g5("1.3", "T3", pol)
    own = a["ratio_vs_buffered_unpadded"] if pol.startswith("buffered") else a["ratio_vs_token_stream"]
    rows.append(f"{nm} & {own:.2f} & {a['ttfb_token_intervals']:.0f} & {a['completion_token_intervals']:.0f} & "
                f"{pct(a['binary_accuracy']['D0_total_threshold'][0])} & {pct(a['best_D2_binary_accuracy'])} & "
                f"{pct(b['best_D2_binary_accuracy'])} & {pct(a['identification_top1'])}\\\\")
(TAB / "transfer-streaming.tex").write_text(r"""\begin{table}[t]\centering\footnotesize
\caption{E5: the same 48 saved responses emitted by a buffered or a token-streaming frontend (TLS~1.3 loopback captures). Bytes are relative to the unpadded emitter of the same kind. TTFB/Done: first and last delivered byte in token intervals (accounting proxy). Accuracies on 24 held-out outputs (12 topics); ID: closed-world top-1 identification among 48 responses (chance 2.1\%).}\label{tab:transfer-streaming}
\setlength{\tabcolsep}{1.6pt}
\begin{tabularx}{\columnwidth}{@{}Yrrrrrrr@{}}\toprule
 & & & & \multicolumn{2}{c}{T1 acc.} & T3 & \\\cmidrule(lr){5-6}\cmidrule(lr){7-7}
Emitter / framing & Bytes$\times$ & TTFB & Done & $D_0$ & $D_2$ & $D_2$ & ID\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabularx}
\par\smallskip\raggedright
$D_2$ is the best of total-byte threshold, record-count threshold and a logistic sequence model, each fitted on defended training outputs. Random padding: 10 socket-measured draws plus an independent profiling run. TLS~1.2 gives identical accuracies and byte ratios within 0.03. Tokens: o200k\_base proxy. Count cap: 208 (T1) and 88 (T3) events fitted on training outputs; 2/24 and 5/24 test outputs overflow it.
\end{table}
""")


def g6(tgt, cov):
    return next(r for r in e6 if r["target"] == tgt and r["cover"] == cov)


def g7(tgt, cov, fr):
    return next(r for r in e7["results"] if r["target"] == tgt and r["cover"] == cov and r["framing"] == fr)


NAMES6 = [("none", "No cover"), ("cancel_p50_shadow", "Cancel, $p{=}0.5$"), ("cancel_p100_shadow", "Cancel, $p{=}1$"),
          ("cancel_p100_live", "Cancel, $p{=}1$, live execution"), ("cancel_const2_shadow", "Cancel count $\\to 2$"),
          ("decoy1_shadow", "One decoy program"), ("decoy2_shadow", "Two decoy programs"),
          ("shape_eq_shadow", "Shape equalization")]
rows = []
for cov, nm in NAMES6:
    c, r = g6("cancel", cov), g6("return", cov)
    if cov in {x["cover"] for x in e7["results"]}:
        nr = " & ".join(f"{ba(g7('cancel', cov, fr))} & {ba(g7('return', cov, fr))}" for fr in ("raw", "bucket1024", "const"))
        nr += f" & {g7('cancel', cov, 'const')['wire_ratio']:.1f}"
    else:
        nr = " & ".join(["---"] * 7)
    rows.append(f"{nm} & {ba(c)} & {ba(r)} & {c['call_overhead']:.2f} & {pct(c['db_equality'])} & {nr}\\\\")
(TAB / "transfer-cover.tex").write_text(r"""\begin{table*}[t]\centering\footnotesize
\caption{E6/E7: randomized cover on 115 retail reference programs $\times$ 3 seeds. Entries are the best held-out balanced accuracy (\%) over all attackers for the cancellation (C, 18 positive tasks) and return (R, 32) targets. Dispatch view: tool names and response lengths. Network view: TLS~1.2 record lengths on the agent--tool link under raw, 1024-byte bucket or constant framing.}\label{tab:transfer-cover}
\setlength{\tabcolsep}{3.5pt}
\begin{tabularx}{\textwidth}{@{}Yrrrrrrrrrrr@{}}\toprule
 & \multicolumn{4}{c}{Dispatch view (E6)} & \multicolumn{7}{c}{Network view (E7)}\\\cmidrule(lr){2-5}\cmidrule(lr){6-12}
 & & & & & \multicolumn{2}{c}{Raw} & \multicolumn{2}{c}{Bucket} & \multicolumn{2}{c}{Constant} & \\\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}
Cover policy & C & R & Calls+ & DB eq. & C & R & C & R & C & R & Bytes$\times$\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabularx}
\par\smallskip\raggedright
Calls+: cover calls per real call. DB eq.: orders/users equal to reference. Cover is sampled from other users' reference programs and placed at random positions; all policies except ``live'' run cover in a per-session sandbox. Attackers: $D_0$/$D_2$ gradient boosting and logistic regression, a count rule and, on the network view, a size-profiling decoder; task-grouped 5-fold cross-validation. Bytes$\times$: constant framing relative to raw framing without cover. Intervals: Supplement S12.
\end{table*}
""")

LABEL = {"confirmed": "Confirmed", "partially_confirmed": "Partly", "refuted": "Refuted", "not_confirmed": "Not confirmed"}
TXT = {
    "P1": ("Buffered 2.18$\\times$ cap transfers to a token stream", "Unres.$\\to$Incomp. (C1, R9)",
           "Per-event padding: T1 100\\%; constant shape costs 2.42$\\times$ stream bytes and doubles completion"),
    "P2": ("Low $D_0$ under batching shows protection", "Unres.\\ (R5)", "Batch: $D_0$ 50\\%, $D_2$ 100\\%; cancel cover: $D_0$ 50\\%, $D_2$ 100\\%"),
    "P3": ("Per-event padding prevents response identification", "Unres.$\\to$Incomp. (C1, R7)", "Top-1 ID 58--62\\% vs.\\ 2.1\\% chance"),
    "P4": ("Equal cancel count hides cancellation", "Unres.$\\to$Incomp. (C3, R2)", "Count rule 50\\%; learned 76.9\\% [65, 88]"),
    "P5": ("Dispatch cover protects the tool link", "Unres.\\ (C1)", "Request size names the tool in 95.7\\% of calls; BA 72.7--95.7\\%"),
    "P6": ("Transport framing alone protects intent", "Unres.$\\to$Incomp. (C1, C2)", "Bucket/return 73.9\\% [65, 83]; other cells 53.6--60.1\\%, inconclusive"),
    "P7": ("Joint cover + framing protects, no DB damage", "Unres.; needs C1--C3", "Return 50.0\\%, cancel 54.4\\% [47, 62]; DB 100\\%; 26.3$\\times$ bytes, 7.7$\\times$ calls"),
}
rows = [f"{o['id']} & {TXT[o['id']][0]} & {TXT[o['id']][1]} & {LABEL[o['outcome']]}: {TXT[o['id']][2]}\\\\" for o in pr]
(TAB / "transfer-predictions.tex").write_text(r"""\begin{table*}[t]\centering\footnotesize
\caption{Audit judgments recorded before E5--E7 were run, and their outcomes under the pre-registered thresholds (protected: BA upper 95\% bound $<0.60$ and AUROC $<0.65$; not protected: lower bound $>0.60$).}\label{tab:transfer-predictions}
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\textwidth}{@{}lp{.25\textwidth}p{.2\textwidth}Y@{}}\toprule
ID & Transfer claim & Audit judgment (checks) & Outcome and evidence\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabularx}
\end{table*}
""")

# Supplement: full E5 and E7 tables with intervals.
rows = []
for tls in ("1.2", "1.3"):
    for tgt in ("T1", "T3"):
        for pol, nm in NAMES5:
            r = g5(tls, tgt, pol); b = r["binary_accuracy"]
            f = lambda k: f"{pct(b[k][0])} [{pct(b[k][1])},{pct(b[k][2])}]"
            rows.append(f"{tls} & {tgt} & {nm} & {r['mean_wire_bytes']:.0f} & {f('D0_total_threshold')} & {f('D2_total_threshold')} & "
                        f"{f('D2_count_threshold')} & {f('D2_sequence_logreg')} & {pct(r['identification_top1'])} & {r['mean_ambiguity_set']:.1f}\\\\")
s12 = r"""\section{Second-round transfer tests (E5--E7)}\label{app:transfer}
This section reports every cell behind Tables~10--12 of the main paper. Artifacts: \path{experiments/sp2027-r2/}. Predictions were committed before execution (\path{PREREGISTRATION.json}).
\begin{table*}[!ht]\centering\scriptsize
\caption{E5 per attacker with 95\% topic-bootstrap intervals (12 test topics). Wire: mean application-record bytes incl.\ 5-byte headers. Amb.: mean size of the nearest-sequence tie set.}
\begin{tabular}{@{}lllrrrrrrr@{}}\toprule
TLS & Target & Framing & Wire & $D_0$ total & $D_2$ total & $D_2$ count & $D_2$ sequence & ID & Amb.\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabular}\end{table*}
"""
rows = []
for tgt in ("cancel", "return"):
    for cov, nm in NAMES6:
        r = g6(tgt, cov); a = r["attackers"]
        f = lambda k: f"{pct(a[k]['ba'])} [{pct(a[k]['ba_ci95'][0])},{pct(a[k]['ba_ci95'][1])}]"
        rows.append(f"{tgt} & {nm} & {f('D0_gboost')} & {f('D2_logreg')} & {f('D2_gboost')} & {f('count_rule')} & {r['best_auroc']:.2f} & {pct(r['account_equality'])} & {pct(r['cover_error_rate'])}\\\\")
s12 += r"""\begin{table*}[!ht]\centering\scriptsize
\caption{E6 dispatch view: balanced accuracy (\%) with task-cluster bootstrap intervals (115 tasks, 3 seeds per task), best AUROC, active-account equality and cover-call error rate.}
\begin{tabular}{@{}llrrrrrrr@{}}\toprule
Target & Cover & $D_0$ GB & $D_2$ LR & $D_2$ GB & Count rule & AUROC & Acct.\ eq. & Cover err.\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabular}\end{table*}
"""
rows = []
for tgt in ("cancel", "return"):
    for fr in ("raw", "bucket1024", "const"):
        for cov, nm in NAMES6:
            if cov not in {x["cover"] for x in e7["results"]}:
                continue
            r = g7(tgt, cov, fr)
            rows.append(f"{tgt} & {fr} & {nm} & {baci(r)} & {r['best_attacker'].replace('_', ' ')} & {r['best_auroc']:.2f} & {pct(r['decoder_call_accuracy'])} & {r['wire_ratio']:.2f} & {r['round_trip_ratio']:.2f}\\\\")
ti = e7["tool_identification"]
s12 += r"""\begin{table*}[!ht]\centering\scriptsize
\caption{E7 network view on the agent--tool TLS~1.2 link (4,140 sessions). Best attacker over all attackers; Dec.: per-call accuracy of the size-profiling decoder. Framing caps: requests 512B, responses 3,072B (95th percentile of reference responses), larger responses padded to 1024B multiples.}
\begin{tabular}{@{}lllrlrrrr@{}}\toprule
Target & Framing & Cover & Best BA [95\% CI] & Best attacker & AUROC & Dec. & Bytes$\times$ & Calls$\times$\\\midrule
""" + "\n".join(rows) + r"""
\bottomrule\end{tabular}
\par\smallskip Request size alone identifies the tool in """ + f"{pct(ti['raw']['request_size_to_tool_accuracy'])}\\% of {ti['raw']['calls']} reference calls under raw framing ({ti['raw']['distinct_request_sizes']} distinct sizes; majority-tool baseline {pct(ti['raw']['majority_tool_baseline'])}\\%) and in {pct(ti['bucket1024']['request_size_to_tool_accuracy'])}\\% under either padded framing." + r"""
\end{table*}
"""
(TAB / "supp-transfer.tex").write_text(s12)
print("tables written")
