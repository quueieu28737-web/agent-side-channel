"""Generate current manuscript tables from post-review results (UTF-8/LF)."""
import json
import re
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
TAB=HERE.parents[1]/"manuscript/tables"
def load(name): return json.loads((HERE/name).read_text(encoding="utf-8"))
def interval(r):
    a,b=r["best_ba_ci95"]
    return f'{100*r["best_ba"]:.1f} [{100*a:.1f},{100*b:.1f}]'
NAMES={"none":"No cover","cancel_p50_shadow":r"Cancel, $p{=}0.5$",
       "cancel_p100_shadow":r"Cancel, $p{=}1$","cancel_p100_live":r"Cancel, $p{=}1$, live",
       "cancel_const2_shadow":r"Cancel count $\to2$","decoy1_shadow":"One decoy",
       "decoy2_shadow":"Two decoys","shape_eq_shadow":"Shape"}
STATUS={"above_threshold":"Above","inconclusive":"Inconcl.","meets_evaluated_suite_criterion":"Meets"}
def tables():
    e6=load("e6_dispatch_results.json")
    e7=load("e7_network_results.json")["results"]
    identity=load("identity_and_calibration.json")
    cover=(TAB/"transfer-cover.tex").read_text(encoding="utf-8")
    cover=cover.replace("Intervals: Supplement S12.","Suite-maximum intervals: Supplement S12. Defense templates/pools/caps use all 115 tasks; attacker fitting uses training folds. No network configuration meets the criterion for both targets.")
    # Historical per-attacker E6 intervals remain valid for individual attackers;
    # replace its E7 selected-attacker summary with current suite intervals.
    supp=(TAB/"supp-transfer.tex").read_text(encoding="utf-8")
    stop=supp.index(r"\begin{table*}",supp.index(r"\caption{E6"))
    supp=supp[:stop]
    supp=supp.replace(r"This section reports every cell behind Tables~10--12 of the main paper. Artifacts: \path{experiments/sp2027-r2/}. Predictions were committed before execution (\path{PREREGISTRATION.json}).",
        r"E5 and individual-attacker E6 results below retain the R2 measurements. Current E6/E7 suite summaries use post-review reanalysis in \path{experiments/sp2027-r3/}; historical registration and outputs remain in \path{experiments/sp2027-r2/}. A suite maximum is recomputed in each of 2,000 common task-bootstrap draws. Intervals condition on fixed out-of-fold predictions and omit retraining/search uncertainty. Meets: upper BA bound $<0.60$ and maximum point AUROC $<0.65$; Above: lower BA bound $>0.60$; otherwise inconclusive. This is a finite-suite criterion, not a security guarantee.")
    supp+=r"""
\begin{table*}[!ht]\centering\scriptsize
\caption{Corrected E6 suite maxima and task-bootstrap intervals. Individual-attacker results above are unchanged. AUROC is also maximized over the evaluated suite.}
\begin{tabular}{@{}llrrl@{}}\toprule
Target & Cover & Max BA [95\% CI] & Max AUROC & Criterion\\\midrule
"""
    for r in e6:
        supp+=f'{r["target"]} & {NAMES[r["cover"]]} & {interval(r)} & {r["best_auroc"]:.2f} & {STATUS[r["criterion"]]}'+r"\\"+"\n"
    supp+=r"\bottomrule\end{tabular}\end{table*}"+"\n"
    supp+=r"""
\begin{table*}[!ht]\centering\scriptsize
\caption{Corrected E7 suite maxima (4,140 saved TLS sessions). Decoder: held-out request/response size-to-tool accuracy; it differs from request-only identification. Costs use raw/no-cover as denominator. Defense calibration uses the full public task population.}
\begin{tabular}{@{}lllrrlrrr@{}}\toprule
Target & Framing & Cover & Max BA [95\% CI] & AUROC & Criterion & Decoder & Bytes$\times$ & Calls$\times$\\\midrule
"""
    for r in e7:
        supp+=f'{r["target"]} & {r["framing"]} & {NAMES[r["cover"]]} & {interval(r)} & {r["best_auroc"]:.2f} & {STATUS[r["criterion"]]} & {100*r["decoder_call_accuracy"]:.1f} & {r["wire_ratio"]:.2f} & {r["round_trip_ratio"]:.2f}'+r"\\"+"\n"
    supp+=r"\bottomrule\end{tabular}\end{table*}"+"\n"
    supp+=r"""
\begin{table*}[!ht]\centering\footnotesize
\caption{Request-only tool identification: training-fold size table, unseen-size fallback to the training majority. Each of 582 reference calls is tested once. The 95.7\% raw in-sample purity is excluded from held-out accuracy.}
\begin{tabular}{@{}llrr@{}}\toprule
Task stratification & Framing & Held-out accuracy (\%) & Training-majority baseline (\%)\\\midrule
"""
    for r in identity["request_only_grouped_oof"]:
        supp+=f'{r["target_stratification"]} & {r["framing"]} & {100*r["accuracy"]:.1f} & {100*r["training_majority_accuracy"]:.1f}'+r"\\"+"\n"
    supp+=r"""\bottomrule\end{tabular}
\par\smallskip Training-only tool-count maxima overflow on five distinct held-out tasks (22, 28, 40, 67, 87) under either target split. This is a feasibility audit, not a rerun of defense efficacy. Full fold membership and overflow records are released. No tested network configuration meets the criterion for both targets.
\end{table*}
"""
    p=r"""\begin{table*}[t]\centering\footnotesize
\caption{Current reassessment of the seven author-written judgments recorded before E5--E7. Historical outcome labels are preserved in the artifact, not counted as audit accuracy.}\label{tab:transfer-predictions}
\begin{tabularx}{\textwidth}{@{}lp{.27\textwidth}Y@{}}\toprule
ID & Claim under examination & Current evidence and qualification\\\midrule
P1 & Buffered cost transfers to a stream & Emitter mismatch supported: per-event padding leaves T1 at 100\%; constant-shape stream costs 2.42$\times$.\\
P2 & Low $D_0$ establishes protection & Counterexample supported: batching and cancellation cover give $D_0$ 50\%, $D_2$ 100\%.\\
P3 & Per-event padding prevents identification & Counterexample supported: top-1 58--62\% versus 2.1\% chance in the closed candidate set.\\
P4 & Equal cancellation count hides cancellation & Residual leakage supported: count rule 50\%; maximum BA 76.9\%.\\
P5 & Dispatch protection transfers to the tool link & Protected-source premise unmet: count/decoy policies already leak at dispatch. Network BA 72.7--95.7\% shows persistence.\\
P6 & Framing alone protects intent & Bucketed return remains above threshold; remaining framing-only cells inconclusive.\\
P7 & Joint cover/framing protects both targets & Not established: no configuration meets both target criteria. Joint constant framing: 50.0--54.4\% BA; 26.3$\times$ bytes, 7.7$\times$ calls.\\
\bottomrule\end{tabularx}
\end{table*}
"""
    e8=(TAB/"supp-e8.tex").read_text(encoding="utf-8")
    e8=e8.replace("Autonomous-agent pipeline (E8)", "Stand-in planner pipeline (E8)")
    e8=e8.replace("stand-in planners and validate the pipeline", "stand-in planners and exercise the pipeline")
    e8=re.sub(r"\s*\[\d+(?:\.\d+)?,\s*\d+(?:\.\d+)?\]", "", e8)
    e8=e8.replace(r"[95\% task-cluster interval]", "point estimates")
    e8=e8.replace(r"\caption{", r"\caption{E8 diagnostics report point estimates only; no suite-maximum interval was recomputed for online runs. Current offline E6/E7 intervals are in S12. ", 1)
    return {"r3-transfer-cover.tex":cover,"r3-transfer-predictions.tex":p,"r3-supp-transfer.tex":supp,"r3-supp-e8.tex":e8}
def main(destination=TAB):
    destination.mkdir(parents=True,exist_ok=True)
    for name,content in tables().items():
        (destination/name).write_text(content,encoding="utf-8",newline="\n")
if __name__=="__main__": main(Path(sys.argv[1]) if len(sys.argv)>1 else TAB)
