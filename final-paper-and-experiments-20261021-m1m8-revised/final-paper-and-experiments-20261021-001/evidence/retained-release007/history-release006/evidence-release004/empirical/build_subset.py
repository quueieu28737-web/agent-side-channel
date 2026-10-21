"""Read-only source-bound selection for deployment QUESTIONS, not a ranking.

Writes a new derived directory only. No model, fitting, network, third-party
code execution, interval re-estimation, or modification of the 33/66 inputs.
The semantic selection is an explicit internal audit, not human validation.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
UNITS = ROOT / "evidence/reviewer-five-fixes-20261020-001/current-evidence/interventions/intervention-result-units.csv"
FIELDS = ROOT / "evidence/reviewer-five-fixes-20261020-001/current-evidence/field-audit/utility-cost-dispositions.csv"
EXPECTED = {
    UNITS: "268321180f42e686f10f32f59839b235592a167503c8ce21e9f2a735cabb5dec",
    FIELDS: "edd41bf0a44a52d745357234131231f4851c465858e7c4db03f049e4f81d6cd9",
}

# Each row is selected by stated mechanism/goal and measured object, NOT its
# result magnitude, significance, utility availability or whether it succeeded.
# E=executed inference condition; P=component prototype/cost; O=offline/simulated
# or estimated planning evidence; U=live-placement binding unresolved.
SELECT = {
    "UI-delay-offline": ("O", "Reduce action-timing fingerprintability", "Would delayed action metadata still support prediction?", "Clean/delayed-trained predictors on stored timestamp-transformed action traces.", "Live action execution, task/policy outcomes, and executed delay cost are unmeasured.", "Do not deploy an action-delay budget from an offline trace score."),
    "WRA-decoy-execution": ("E", "Cover private prompt/trait inference with decoy agents", "Can concurrent cover-agent activity reduce the specified observer's private-goal inference?", "Source-scoped inference scores under destination/URL visibility and LLM-judged report usefulness.", "Objective terminal/policy outcome and same-run latency/wire cost; observer-specific applicability.", "A judged useful report does not establish operational goal preservation or acceptable cover cost."),
    "NET-upstream-local": ("E", "Obscure streaming length/group signals", "Does upstream protection cover the content-aware downstream receiver?", "Protected deployment scenarios and a separate local vLLM setting; TraceA/TraceB topic classification, not one homogeneous trial.", "Same-session final-hop protection/utility/cost bridge; exact paired adaptation binding.", "Do not transfer an upstream envelope to a renderer that can emit a fresh view."),
    "NET-dummy-padding-simulation": ("O", "Suppress token/group features using padding/dummies", "Which inferred packet representation survives a synthetic transform?", "Offline dummy/padding transforms; count versus length representations react differently.", "Executed placement, live incremental overhead, objective utility, exact refit binding.", "Transform sensitivity cannot price a live defended deployment."),
    "EARLY-K-calibration-oracle": ("O", "Reduce prefix-cache leakage by sharing granularity", "What recovery/query behavior remains under a stated K-granularity oracle?", "K-specific timing calibration followed by a stochastic oracle and adjusted next-K predictor.", "Live changed-K protection trial, applicable latency/reuse loss, objective task outcome, paired D2.", "Do not price K-granularity KV protection using a semantic-cache prototype."),
    "EARLY-semantic-deidentification": ("P", "Remove PII from semantic-cache matching", "What component cost does this semantic-cache de-identification prototype incur?", "Approximately 6ms/4% for the GPTCache semantic component.", "Same-mechanism end-to-end utility and applicable whole workload/attack outcome.", "Use this cost only for the measured semantic component, not prefix-cache K tuning."),
    "WHISPER-randompadding-capture": ("E", "Obscure streaming packet sizes", "Does the measured provider obfuscation condition erase the tested topic classifier?", "New padding-on/off captures; source median AUPRC97.5% versus92.9%, five trials.", "Exact defended-fit/pairing lineage, objective task utility, same-run incremental cost.", "Retain the source condition; do not infer broad protection or zero live overhead."),
    "WHISPER-batching-replay": ("O", "Reduce packet-level topic inference by batching", "What inference survives grouping recorded packets?", "Offline batch grouping and model-dependent AUPRC.", "Executed buffering/latency, live task outcomes and exact protected refit lineage.", "Do not interpret replayed batches as a measured live buffering frontier."),
    "WHISPER-injection-replay": ("O", "Mask topic inference with generated packet noise", "What inference survives this synthetic injection model?", "Offline stochastic packet generation; source traffic-volume estimate.", "Live placement, full wire/latency cost, objective task outcome and paired adaptation.", "Synthetic packet placement does not prove a live zero-latency mechanism."),
    "SPLICE-CTBF-signal": ("E", "Hide cache-boundary timing signal", "Does the serving prototype suppress this attack signal under its tested load?", "CTBF signal experiment on15 tasks/75 steps with generated background load.", "Whole-task utility and combined CTBF+QCP applicable cost under the same condition.", "Do not attach QCP-only overhead to the combined timing defense."),
    "SPLICE-QCP-cost": ("P", "Quantize observable chunks", "What cost is measured for the QCP component alone?", "Mean7.5 padding tokens, <5ms/<1% QCP-only component measurements.", "Combined CTBF+QCP effect/cost and objective defended task utility.", "A component benchmark cannot price a multi-component serving deployment."),
    "TIME-length-instruction": ("E", "Reduce token-count inference through output-length instructions", "Does a fixed-length instruction reduce the tested attack for each source model?", "Model-specific token-count attack comparison; the tested Gemma2 case is not improved.", "Objective task quality, measured live byte/latency cost and target-specific transfer.", "No universal protection follows from a request to produce fixed-length output."),
    "TIME-padding-estimate": ("O", "Equalize output-length observations", "What would the stated plaintext padding rule add?", "67%/108% plaintext-padding estimates.", "Execution point, actual wire bytes/delay, defended inference and task outcome.", "Do not convert a plaintext estimate into a measured live network budget."),
    "SPEC-padding-REST": ("U", "Mask speculative-decoding length structure", "What does the evaluated REST padding condition establish?", "Source random-padding accuracy34.4% and8.7x token payload, excluding metadata.", "Live placement binding, total wire cost, objective task quality and broader attack scope.", "Retain the scoped result but withhold a live wire/utility frontier."),
    "DANGOL-capture": ("O", "Obscure workflow-level encrypted traffic", "What survives the specified transformed six-class capture condition?", "Protected-data evaluation: accuracy0.17 at16.2x capture bytes for the stated combined transform.", "Same live population, actual protocol deployment and objective task/latency outcomes.", "Do not subtract capture0.17 from live0.30 as a deployment treatment effect."),
    "DANGOL-livebinding": ("E", "Obscure workflow metadata in a live binding", "What trade-off does the tested OHTTP/A2A binding show?", "Live accuracy0.30; approximately13x bytes/11x latency;0.167 is a feature ablation, not a timing masker.", "Objective terminal task/policy outcome; exact live clean/protected-training pairing.", "Use its live measured operating point only; do not borrow capture adaptation or task utility."),
    "SAFE-post-trigger": ("E", "Stop post-trigger KV-sharing inference", "Does the triggered serving condition suppress the measured probe?", "Post-trigger TTFT ROC-AUC near0.5; asynchronous detector timings are separate.", "Exact probe windows/denominators, added serving TTFT, objective application outcome.", "Do not equate detector latency or near-chance scoped probes with complete service safety."),
    "AHB-online-executed": ("E", "Reduce agent detectability using executed humanization", "Are the executed fake actions compatible with the protected task goal?", "Source TripPlanning success RAW0.75 versus combined online0.15; separately reported detector accuracy.", "Matched duration/action overhead, publication detector-run binding and same-test D2; goal/policy transfer.", "Task-state effects require executed goal scoring, not a borrowed transport-overhead number."),
    "AHB-offline": ("O", "Reduce gesture detectability through trajectory edits", "How does postprocessed behavior look to the source detector?", "Offline touch-trajectory detectability under duration/interval/motion edits.", "Real task execution, terminal outcome/cost and historical detector-fit binding.", "Do not attribute online fake-action damage or safety to offline transformations."),
    "KVGOV-partialflush-sim": ("O", "Reduce cross-principal prefix-cache leakage", "What does a specified simulated flush/keying model predict?", "Seeded simulation ASR19.5%/9.8%; analytic extremes are controls, not live protection measurements.", "Live protected inference, workload reuse/latency cost and objective outcome.", "A simulation does not supply a deployment ASR or workload-cost point."),
    "KVGOV-HMAC-cost": ("P", "Partition cache keys by principal", "What incremental key-derivation cost is measured?", "HMAC1.3us median/1.6us p99 component microbenchmark.", "Lost cross-principal reuse, live end-to-end overhead and protected inference on the same workload.", "Do not let key-computation time stand in for workload-dependent reuse loss."),
    "TRAFFIC-prompt-reformulation": ("E", "Weaken model fingerprints with semantics-preserving reformulation", "How do the source's prompt changes affect a fixed-configuration fingerprint?", "V-C1 accuracy93.2% to69.5%; source identifies this as a lightweight countermeasure.", "Objective terminal correctness, same-run cost, exact adaptive-fit and attacker-data/budget binding.", "Semantic-preservation intent and a lower source classifier score do not establish a deployable frontier."),
    "TRAFFIC-temperature": ("E", "Weaken model fingerprints by decoding variation", "How does the tested temperature variation change identification?", "At0.3/0.5/1.5, accuracy75.0/88.8/80.0% versus93.2%; response is nonmonotonic.", "Objective task quality/cost, defended-training lineage and attainable attacker calibration.", "Do not assume monotonic privacy improvement or transfer the tested temperatures to another generator."),
    "CARLINI-fixed-rate": ("O", "Suppress variable token-release timing", "What cost curve follows from a fixed release schedule on the measured timings?", "Per-token latency/bandwidth curve at specified release rates.", "Live placement/run binding, same-condition defended inference and objective utility.", "The curve is useful planning evidence, not a complete live protection or total-request-delay point."),
    "GAO-zero-copy-off": ("P", "Remove the shared-memory channel component", "What loading/memory cost does disabling zero-copy incur?", "Source loading latency+17% and memory+32% for the stated multi-instance configuration.", "Matched defended attack measurement, end-to-end serving TTFT and application utility.", "Do not relabel model-loading overhead as inference/serving overhead."),
    "TDXRAY-oblivious-map": ("P", "Hide token-map lookup access patterns", "What overhead belongs to the tested oblivious lookup component?", "Isolated lookup slowdown52.52--369.15x in its microbenchmark.", "Same-workload protected inference, total inference cost and task correctness.", "Do not multiply total LLM latency by a lookup-only slowdown."),
}

EXCLUDE = {
    "SIG-common-guardrail": "Fixed common instruction, no guardrail-on/off intervention contrast; retain residual procedural inference as context.",
    "AGENTTELL-fixed-instruction": "Loaded/cold contrasts secret context, not installing/removing the common privacy instruction.",
    "FP-CLOUDFLARE": "Website access-control goal is blocking agents, not protecting the surveyed observer's hidden target from inference.",
    "BAR-co-running-noise": "Covert-channel robustness to co-running noise is not the evaluated deployment of a privacy mitigation.",
    "RHYTHM-VPN": "Generic route robustness condition, not a purpose-built or claimed evaluated mitigation mechanism in this question set.",
    "DEB-filter-origin": "Privacy filter creates the attacked observable; not a mitigation evaluation of that new channel.",
    "KVGOV-hardware-gap": "Hardware hit/miss calibration establishes a channel, not a protected inference or mitigation-cost condition.",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    out = HERE / "derived-001"
    if out.exists():
        raise FileExistsError("Never overwrite a derived checkpoint")
    checked = {}
    for path, digest in EXPECTED.items():
        assert sha(path) == digest, path
        checked[path.relative_to(ROOT).as_posix()] = digest
    units, fields = read_csv(UNITS), read_csv(FIELDS)
    lookup = {r["unit_id"]: r for r in units}
    assert len(units) == len(lookup) == 33
    assert len(fields) == len({(r["unit_id"], r["field"]) for r in fields}) == 66
    assert set(SELECT).isdisjoint(EXCLUDE)
    assert set(SELECT) | set(EXCLUDE) == set(lookup)
    for row in units:
        path = ROOT / row["source_path"]
        assert sha(path) == row["source_sha256"], path
        checked[row["source_path"]] = row["source_sha256"]
    for row in fields:
        unit = lookup[row["unit_id"]]
        assert row["citation_key"] == unit["citation_key"]
        assert row["source_sha256"] == unit["source_sha256"]
        assert row["current_extraction"] == unit[row["field"]]
    annotated = []
    for row in units:
        item = dict(row)
        uid = row["unit_id"]
        item["selected_for_mitigation_question"] = uid in SELECT
        if uid in SELECT:
            tier, goal, question, measured, missing, blocked = SELECT[uid]
            item.update(dict(evidence_stratum=tier, stated_mitigation_goal=goal,
                             specific_deployment_question=question, measured_object=measured,
                             missing_for_this_question=missing, judgment_not_licensed=blocked,
                             selection_rule_reason="Explicit reduction/evasion mechanism plus evaluated inference property or mechanism-specific cost; retain nonlive/unknown cases with their mode."))
        else:
            item.update(dict(evidence_stratum="CONTEXT_NOT_SELECTED", stated_mitigation_goal="",
                             specific_deployment_question="Not a mitigation-effect question for this result unit.",
                             measured_object=row["inference_or_measurement_target"],
                             missing_for_this_question="Not a missing-value classification; different experimental objective.",
                             judgment_not_licensed="Do not add this contextual unit to a defense-inadequacy denominator.",
                             selection_rule_reason=EXCLUDE[uid]))
        item["new_measurement_or_fit"] = False
        item["independent_researcher_validation"] = False
        annotated.append(item)
    subset = [r for r in annotated if r["selected_for_mitigation_question"]]
    assert len(subset) == 26 and len(annotated) == 33
    for path, digest in list(checked.items()):
        assert sha(ROOT / path) == digest, "Read input changed"
    summary = {
        "scope": "Source-applicable deployment QUESTIONS; not a common defense benchmark, efficacy rank, failure rate or field-wide prevalence denominator.",
        "selection_rule": [
            "The unit concerns a stated mechanism intended to suppress the target side-channel inference or hide agent detectability; humanization is separately labeled, not relabeled confidentiality.",
            "The unit evaluates a mitigation-relevant inference/detection property or the stated mechanism's cost, including offline/simulation/estimate results with their actual evidence stratum.",
            "No selection threshold uses result sign, accuracy, significance, completeness of utility/cost or successful task status. Unknown live placement is retained, not excluded.",
            "Common guardrails without installation contrasts, access blocking, generic route/noise robustness, signal-origin privacy filters and bare channel calibration are contextual, not this mitigation-effect subset.",
        ],
        "selection_timing": "Retrospective rule declaration after sources/results are known; not preregistered or outcome-blind validation.",
        "all_units": len(units), "all_fields": len(fields),
        "selected_units": len(subset), "context_units": len(EXCLUDE),
        "strata": dict(collections.Counter(r["evidence_stratum"] for r in subset)),
        "stratum_meaning": {"E": "Source reports an executed/collected inference condition, not necessarily a paired causal effect or authenticated original run.", "P": "Mechanism-specific executed component/prototype cost; not a whole-service frontier.", "O": "Offline/simulated/estimated planning evidence; not a live intervention trial.", "U": "Evaluated property exists but live placement/run binding remains unverified."},
        "no_aggregate_inadequacy_fraction": True,
        "four_unbound_defense_assertions": {"agentprint2025": "NR-V referenced supplement result/run", "weiss2024prompt": "NR-V quantitative vendor-defense binding", "gu2025promptcaching": "NR-V provider-change before/after binding", "prompt_echo2026": "NR-V padding-method/population/defended-outcome binding"},
        "unbound_queue_not_silently_dropped": "These four are outside the 33 extracted result units because their quantitative result binding is not established; they remain in the corpus and a separate unresolved assertion queue, not measured failures or absent mitigation.",
        "AHB": {"D1_code": "Verified static condition-wise refits", "D1_run": "NR-V", "D2_same_defended_test": "NR-V", "source_reported_task_utility": "RAW0.75 versus combined online0.15", "utility_does_not_require_authenticating_detector_run": True},
        "source_and_input_hashes_verified": checked,
        "all_33_annotated_rows": annotated,
        "all_66_input_field_rows_unchanged": fields,
        "new_fits": 0, "new_model_requests": 0, "network_requests": 0,
        "independent_researcher_validation": False,
    }
    out.mkdir(exist_ok=False)
    for name, values in [("mitigation-question-subset.csv", subset), ("all33-dispositions.csv", annotated)]:
        with (out / name).open("x", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(annotated[0]))
            w.writeheader()
            w.writerows(values)
    with (out / "deployment-subset-audit.json").open("x", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"all_units_preserved": 33, "all_field_positions_preserved": 66,
                      "selected_question_units": len(subset), "context": len(EXCLUDE),
                      "strata": summary["strata"], "checked_hashes": len(checked),
                      "new_fits": 0, "new_model_requests": 0}))


if __name__ == "__main__":
    main()
