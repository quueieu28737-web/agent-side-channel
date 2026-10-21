"""Write paper-ready text only after complete saved-result verification."""
import argparse
import datetime as dt
import json
from pathlib import Path


def main(out):
    summary = json.loads((out / "summary.json").read_bytes())
    check = json.loads((out / "verification.json").read_bytes())
    if check["status"] != "VERIFIED_SAVED_CENSUS_AND_NATIVE_RESCORING":
        raise ValueError("Verification required")
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    metrics = {(r["position"], r["arm"], r["metric"]): r for r in summary["metrics"]}
    effects = {(r["position"], r["arm"], r["metric"]): r for r in summary["paired_effects"]}
    conditioned = json.loads((out / "conditioned-summary.json").read_bytes())
    conditional = {(r["group"], r["position"], r["metric"]): r for r in conditioned["results"]}
    target = out.parent.parent / "deliverables"
    target.mkdir(exist_ok=False)
    def pct(value):
        return f"{100*value:.2f}"
    names = {"baseline": "No cover", "discard": "Discard", "shadow": "Shadow", "read_only": "Pure read", "live_mutation": "Live mutation"}
    table = []
    for arm, label in names.items():
        before = metrics["before", arm, "native_reward"]["mean"]
        after = metrics["after", arm, "native_reward"]["mean"]
        state_before = metrics["before", arm, "live_state_equal_baseline"]["mean"]
        state_after = metrics["after", arm, "live_state_equal_baseline"]["mean"]
        table.append(f"{label} & {pct(before)} & {pct(after)} & {pct(state_before)} & {pct(state_after)} " + chr(92) * 2)
    be = effects["before", "live_mutation", "native_reward"]
    af = effects["after", "live_mutation", "native_reward"]
    overlap_tasks = sorted({r["task_id"] for r in rows if r["arm"] == "live_mutation" and r["native_reward"] == 1 and r["unconfirmed_live_write_effect"]})
    result_text = (
        f"On the complete {summary['tasks']}-task test suite, {summary['eligible_tasks']} tasks have an eligible same-account pending-order cover. "
        f"All {summary['episodes']} task/seed/position/arm cells are retained. "
        f"The live-mutation paired change in native reward is {pct(be['paired_difference'])} percentage points "
        f"before the reference program (95% task-bootstrap interval [{pct(be['ci_low'])}, {pct(be['ci_high'])}]) and "
        f"{pct(af['paired_difference'])} points after it ([{pct(af['ci_low'])}, {pct(af['ci_high'])}]). "
        f"Unconfirmed live changes coexist with a passing native reward in {len(overlap_tasks)} distinct tasks in this fixed suite."
    )
    clean_before = conditional["reference_error_free", "before", "native_reward"]
    clean_after = conditional["reference_error_free", "after", "native_reward"]
    sensitivity = (f"Nineteen reference programs return at least one tool error; all remain in the census. "
        f"In the 96 error-free reference tasks, the live-mutation native reward is {pct(clean_before['mean'])}% "
        f"before insertion (95% interval [{pct(clean_before['ci_low'])}, {pct(clean_before['ci_high'])}]) and "
        f"{pct(clean_after['mean'])}% after insertion ([{pct(clean_after['ci_low'])}, {pct(clean_after['ci_high'])}]).")
    tex = r"""\section{A controlled bridge for executed cover}
\label{sec:tau-cover-bridge}
We test the execution boundary in the second deployment decision using the
original retail tools, data and task reward from a pinned release of
$\tau$-bench. We replay its 115 public test reference programs, hold each
program fixed, and insert the same additional cancellation intent through four
routes: discard, isolated shadow state, a pure order-details read, or live
business state. A no-cover arm supplies the paired control. Three fixed seeds
select a pending order belonging to the task user; the two insertion positions
are before and after the reference program. Tasks without an eligible order
remain in the denominator. This yields 3,450 paired cells; repetitions are
clustered within tasks.
Reference textual outputs hold the native output predicate fixed; the reward
therefore assesses the controlled execution, not a model's answer generation.

""" + result_text.replace("%", r"\%") + "\n\n" + sensitivity.replace("%", r"\%") + r"""

\begin{table}[t]
\centering\small
\caption{Native reward and equality to the no-cover business state (percent).
Before/after refer to the insertion position. The independent resampling unit
is the task, not one of its repeated cells.}
\label{tab:tau-cover-bridge}
\begin{tabular}{lrrrr}
\toprule
 & \multicolumn{2}{c}{Native reward} & \multicolumn{2}{c}{State equal} \\
Route & Before & After & Before & After \\
\midrule
""" + "\n".join(table) + r"""
\bottomrule
\end{tabular}
\end{table}

The intervention varies routing while preserving the original program and
native scoring. Its deployment use is concrete: validate cover against both
business-state preservation and the action's authorization context. The cover
intent is explicitly unconfirmed in this scripted experiment; write attempts
and writes that actually change state are recorded separately. Reference
programs control planning ability, so this is an execution experiment rather
than an autonomous-agent benchmark score. It measures task-state consequences;
an additional observer experiment would be needed to quantify privacy benefit.
Full arm-specific outcomes, task-cluster bootstrap intervals, source hashes,
raw tool observations and native reward verification accompany the code.
"""
    (target / "empirical-insertion.tex").write_text(tex, encoding="utf-8")
    report = {
        "status": "COMPLETED_AND_SAVED_RESULTS_VERIFIED", "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "tasks": summary["tasks"], "cells": summary["episodes"], "eligible_tasks": summary["eligible_tasks"],
        "reference_error_tasks": summary["reference_error_tasks"],
        "native_pass_with_unconfirmed_write_task_ids": overlap_tasks,
        "native_pass_with_unconfirmed_write_task_count": len(overlap_tasks),
        "live_reward_paired_before": be, "live_reward_paired_after": af,
        "conditioned_analysis": conditioned,
        "source": "tau-bench pinned 59a200c6d575d595120f1cb70fea53cef0632f6b",
        "verification": check, "main_manuscript_edited": False,
        "scope": "controlled fixed-reference-program cover execution; not a new privacy attack or an autonomous-agent performance result",
    }
    (target / "result-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (target / "RESULTS.md").write_text(
        "# T2(c) controlled executed-cover result\n\n" + result_text + "\n\n" + sensitivity + "\n\n"
        + "The four routes and no-cover baseline are retained. The full 115-task census includes no-eligible-cover and reference-tool-error cases. "
        + "See summary.csv for every endpoint and paired-effects.csv for all contrasts. A passing native reference score is not evidence of autonomous model competence.\n\n"
        + "## Scope and integration\n\n"
        + "The original main.tex and sealed anonymous releases are unchanged by this side conversation. empirical-insertion.tex is a ready-to-review section for integration. "
        + "No model is called. No privacy-inference improvement is claimed from task-state outcomes.\n\n"
        + "## Validation\n\n"
        + f"All {check['cells']} unique cells and all {check['unique_task_final_states_rescored']} distinct task/final-state combinations were checked with the original native reward. "
        + f"The first attempt's {check['carried_cells_unchanged']} rows remain exactly preserved.\n", encoding="utf-8")
    print(json.dumps({k: v for k,v in report.items() if k != "verification"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out)
