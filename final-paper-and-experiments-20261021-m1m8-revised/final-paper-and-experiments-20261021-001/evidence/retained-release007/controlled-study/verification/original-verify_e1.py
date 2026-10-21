"""Read-only independent E1 saved-receipt audit; no model, socket, fitting or RNG.

This does not import experiment modules. Saved prediction rules are evaluated,
not refitted. TLS records are parsed anew from saved ciphertext bytes.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics
import struct

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "experiments/controlled_defense_20261021"
RUN = STUDY / "runtime/E1-001"
COLLECTION = STUDY / "runtime/collection-001"
INPUT = STUDY / "runtime/replay-inputs-001"
PACK = STUDY / "inputs/study-v1"
ARMS = ("NONE", "UPSTREAM_PAD", "END_TO_END_PAD")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, name):
    if not condition:
        raise AssertionError(name)


def records(raw):
    parsed, offset = [], 0
    while offset < len(raw):
        check(len(raw) - offset >= 5, "TLS header completeness")
        kind, major, minor, length = struct.unpack("!BBBH", raw[offset:offset + 5])
        check(major == 3 and kind in (20, 21, 22, 23), "TLS header validity")
        check(offset + 5 + length <= len(raw), "TLS payload completeness")
        parsed.append({"offset": offset, "type": kind, "version": [major, minor],
                       "payload_bytes": length, "wire_bytes": length + 5})
        offset += 5 + length
    check(offset == len(raw), "TLS byte accounting")
    return parsed


def saved_predict(model, value):
    if model["kind"] == "constant":
        return model["label"]
    check(model["kind"] == "threshold", "saved classifier kind")
    return int(value > model["threshold"]) if model["direction"] == 1 else int(value < model["threshold"])


def audit():
    freeze, protocol, summary = load(PACK / "freeze.json"), load(RUN / "protocol.json"), load(RUN / "summary.json")
    source_hashes = freeze["sources_sha256"]
    for path, expected in source_hashes.items():
        check(digest(Path(path)) == expected, "frozen source: " + path)
    for filename, key in (("requests.json", "requests_sha256"), ("e1-metadata.json", "metadata_sha256"), ("e2-tasks.json", "tasks_sha256")):
        check(digest(PACK / filename) == freeze[key], "frozen input " + filename)
    check(digest(STUDY / "padding.py") == protocol["source_sha256"], "E1 protocol source binding")
    manifest = load(RUN / "manifest.json")
    for entry in manifest:
        path = RUN / entry["path"]
        check(path.resolve().is_relative_to(RUN.resolve()), "manifest confined path")
        check(digest(path) == entry["sha256"], "E1 manifest " + entry["path"])
    actual_paths = {str(p.relative_to(RUN)).replace("\\", "/") for p in RUN.rglob("*") if p.is_file() and p.name != "manifest.json"}
    check(actual_paths == {r["path"] for r in manifest}, "manifest complete file coverage")
    check(digest(INPUT / "e1.jsonl") == protocol["input_sha256"], "exported E1 input binding")
    check((INPUT / "e1.jsonl").read_bytes() == (RUN / "private/input.jsonl").read_bytes(), "exact E1 private copy")

    inputs = [json.loads(line) for line in (INPUT / "e1.jsonl").read_text(encoding="utf-8").splitlines()]
    check(len(inputs) == 48 and len({r["id"] for r in inputs}) == 48, "48 unique saved outputs")
    by_id = {r["id"]: r for r in inputs}
    meta = {r["id"]: r for r in load(PACK / "e1-metadata.json")}
    group_rows = defaultdict(list)
    for row in inputs:
        group_rows[row["group_id"]].append(row)
        check(all(row[key] == meta[row["id"]][key] for key in ("group_id", "topic", "label", "split")), "frozen label/split binding")
        check(row["status"] == "ok", "saved output status")
    check(len(group_rows) == 24, "24 groups")
    check(Counter(group[0]["split"] for group in group_rows.values()) == {"train": 12, "test": 12}, "12/12 disjoint topic split")
    check(all(len(g) == 2 and {r["label"] for r in g} == {0, 1} and len({r["split"] for r in g}) == 1 for g in group_rows.values()), "paired labels stay together")
    binding = load(INPUT / "raw-binding.json")
    check(digest(COLLECTION / "final.json") == binding["collection_sha256"], "collection final binding")
    check(digest(COLLECTION / "supervision.json") == binding["supervision_sha256"], "collection supervision binding")
    for item in binding["records"]:
        folder = COLLECTION / "requests" / item["id"]
        check(digest(folder / "final-answer.raw.txt") == item["raw_final_sha256"], "raw final binding")
        check(digest(folder / "response.json") == item["response_sha256"], "model response binding")
        response = load(folder / "response.json")
        check(response["status"] == "COMPLETE" and response["model"] == "gpt-6-luna" and response["effort"] == "low", "model response identity/status")
        check(response["application_admissions"] == 1 and response["application_retries"] == 0, "one admission/no retry")
        check(response["exit_code"] == 0 and response["stdout_eof"] and response["reader_closed"], "model transport closure")
        if item["id"] in by_id:
            check(json.loads((folder / "final-answer.raw.txt").read_text(encoding="utf-8")) == response["prediction"], "E1 raw final/parsed response")
            check(response["prediction"]["text"] == by_id[item["id"]]["text"], "exact generated text replay")

    receipts = load(RUN / "private/replay-receipts.json")
    check(len(receipts) == 144, "144 closed replays")
    check(Counter((r["id"], r["arm"]) for r in receipts) == Counter((r["id"], arm) for r in inputs for arm in ARMS), "complete matched arm coverage")
    features = list(csv.DictReader((RUN / "private/attack-release.csv").open(encoding="utf-8", newline="")))
    lookup = {(r["trace_id"], r["site"]): r for r in features}
    check(len(features) == len(lookup) == 288, "288 unique site observations")
    audit_counts = Counter()
    by_arm_site = defaultdict(list)
    for row in receipts:
        original = by_id[row["id"]]
        plaintext = original["text"].encode("utf-8")
        text_hash = hashlib.sha256(plaintext).hexdigest()
        check(row["status"] == "ok" and row["all_owned_threads_joined"], "successful replay/owned thread closure")
        check(row["source_sha256"] == row["terminal_sha256"] == text_hash, "endpoint receipt content identity")
        trial = RUN / "trials" / row["trace_id"]
        integrity = load(trial / "private/integrity.json")
        check(integrity["source_sha256"] == integrity["terminal_sha256"] == text_hash, "per-trial integrity receipt")
        for site in ("upstream", "terminal"):
            padded = row["arm"] != "NONE" if site == "upstream" else row["arm"] == "END_TO_END_PAD"
            chunk = 1024 if padded else 128
            application_bytes = 16384 if padded else 4 + len(plaintext)
            expected_sizes = [min(chunk, application_bytes - offset) + 24 for offset in range(0, application_bytes, chunk)]
            on_disk = load(trial / "observer" / (site + "-records.json"))
            for direction in ("s2c", "c2s"):
                raw = (trial / "observer" / (site + "-" + direction + ".bin")).read_bytes()
                parsed = records(raw)
                saved = row["sites"][site][direction]
                saved_records = [{k: v for k, v in r.items() if k != "tee_read_ns"} for r in saved["records"]]
                check(parsed == saved_records, "independent TLS record parse")
                check(saved == on_disk[direction], "private/public observed record consistency")
                check(hashlib.sha256(raw).hexdigest() == saved["sha256"], "ciphertext hash")
                check(len(raw) == saved["raw_bytes"], "raw byte count")
                app = [r for r in parsed if r["type"] == 23]
                check(sum(r["payload_bytes"] for r in app) == saved["application_payload_bytes"], "application payload byte total")
                check(sum(r["wire_bytes"] for r in app) == saved["application_wire_bytes"], "application wire byte total")
                if direction == "s2c":
                    check([r["payload_bytes"] for r in app] == expected_sizes, "actual framing/24-byte GCM overhead")
                    check(len(app) == saved["application_record_count"], "actual application record count")
                    audit_counts["s2c_streams"] += 1
                    audit_counts["s2c_application_records"] += len(app)
                else:
                    check(not app, "no application payload/request marker on client direction")
                audit_counts["direction_streams"] += 1
            feature = lookup[row["trace_id"], site]
            for field in ("id", "group_id", "label", "split", "arm", "status"):
                check(str(row[field]) == feature[field], "attack-release label/run binding")
            check(int(feature["feature"]) == sum(expected_sizes), "attack feature independently derived")
            by_arm_site[row["arm"], site].append({**feature, "value": int(feature["feature"]), "label_int": int(feature["label"]),
                                                    "wire": row["sites"][site]["s2c"]["application_wire_bytes"]})

    attacks = []
    for saved in summary["analysis"]["attacks"]:
        rows = by_arm_site[saved["arm"], saved["site"]]
        train, test = [[r for r in rows if r["split"] == part] for part in ("train", "test")]
        check(len(train) == len(test) == 24 and Counter(r["label_int"] for r in test) == {0: 12, 1: 12}, "balanced train/test observations")
        model = saved["model"]
        if model["kind"] == "threshold":
            # Verify the saved rule is certified by training only. No search,
            # fitting, selection, or alternative candidate evaluation occurs.
            threshold = model["threshold"]
            left = max(r["value"] for r in train if r["value"] < threshold)
            right = min(r["value"] for r in train if r["value"] > threshold)
            check(threshold == (left + right) / 2, "saved threshold is training adjacent-value midpoint")
            check(all(saved_predict(model, r["value"]) == r["label_int"] for r in train), "training-only perfect separation certificate")
        else:
            check(model == {"kind": "constant", "label": 0}, "constant tie rule")
            check(len({r["value"] for r in train}) == 1, "constant training feature")
        predictions = {r["id"]: r for r in saved["predictions"]}
        correct, cluster_correct = 0, defaultdict(list)
        for row in test:
            prediction = saved_predict(model, row["value"])
            outcome = int(prediction == row["label_int"])
            expected = {"id": row["id"], "group_id": row["group_id"], "label": row["label_int"], "prediction": prediction, "correct": outcome}
            check(predictions[row["id"]] == expected, "saved test prediction arithmetic")
            correct += outcome
            cluster_correct[row["group_id"]].append(outcome)
        check(correct / 24 == saved["test_accuracy"], "saved accuracy")
        cluster_values = [statistics.mean(v) for v in cluster_correct.values()]
        check(len(set(cluster_values)) == 1 and saved["cluster_percentile_95ci"] == [cluster_values[0]] * 2, "degenerate finite-cluster bootstrap arithmetic")
        attacks.append({"arm": saved["arm"], "site": saved["site"], "saved_rule": model, "test_correct": correct,
                        "test_total": 24, "test_topic_clusters": 12, "distinct_test_size_values": len({r["value"] for r in test}),
                        "test_sizes_min_max": [min(r["value"] for r in test), max(r["value"] for r in test)],
                        "saved_cluster_ci": saved["cluster_percentile_95ci"]})

    costs = []
    for saved in summary["costs"]:
        rows = by_arm_site[saved["arm"], saved["site"]]
        total = sum(r["wire"] for r in rows)
        check(total == saved["application_wire_bytes_total"] and total / 48 == saved["mean_application_wire_bytes"], "actual saved application wire cost")
        costs.append({"arm": saved["arm"], "site": saved["site"], "application_s2c_wire_bytes_total": total,
                      "application_s2c_wire_bytes_mean": total / 48, "n": 48,
                      "median_both_link_elapsed_ms": saved["median_end_to_end_ms"]})
    baseline_wire = next(r["application_s2c_wire_bytes_mean"] for r in costs if r["arm"] == "NONE" and r["site"] == "upstream")
    check(summary["status"] == "complete" and summary["closed_replays"] == summary["content_integrity_passes"] == 144 and summary["failed_replays"] == 0, "saved final totals")
    return {"status": "PASS", "operation": "read-only saved ciphertext/lineage/arithmetic verification",
        "new_model_calls": 0, "new_TLS_replays": 0, "refits": 0, "frozen_sources_verified": len(source_hashes),
        "manifest_files_verified": len(manifest), "source_outputs": 48, "topic_groups": 24,
        "train_groups": 12, "test_groups": 12, "replays": 144, "failures": 0, "endpoint_hash_receipts_matching": 144,
        "stream_counts": dict(audit_counts), "attacks": attacks, "costs": costs,
        "padded_feature_payload_bytes": 16768, "padded_application_wire_bytes": 16848,
        "baseline_mean_application_wire_bytes": baseline_wire,
        "padded_to_baseline_ratio_of_aggregate_application_wire_bytes": 16848 / baseline_wire,
        "interpretation": [
            "Upstream-only padding equalized all 48 upstream size features; the new frontend re-emitted a distinguishable size downstream (24/24 held-out labels correct).",
            "Extending fixed padding to the final TLS link equalized that same recorded size feature; the prespecified constant tie rule scored12/24.",
            "Saved bootstrap intervals remain unchanged. All 12 test topic clusters share the same per-cluster score, so intervals degenerate algebraically. They are not population certainty or a general privacy bound.",
            "Size is the sole attacker feature. Timing is not tested for privacy; loopback elapsed time is descriptive replay cost and excludes model generation.",
            "Bandwidth object is S2C application TLS records including5-byte headers and24-byte GCM overhead; handshake/TCP/IP overhead is excluded from the ratio.",
            "Content preservation is independently checked against saved endpoint hashes and exact collected text. Ciphertext alone does not authenticate the endpoint's reported plaintext hash.",
            "This is a controlled buffer/de-pad/re-chunk frontend with one replay per content/arm. It establishes the constructed mechanism and its final-link size control, not field prevalence."
        ],
        "bindings": {"freeze_sha256": digest(PACK / "freeze.json"), "protocol_sha256": digest(RUN / "protocol.json"),
                     "summary_sha256": digest(RUN / "summary.json"), "manifest_sha256": digest(RUN / "manifest.json"),
                     "export_binding_sha256": digest(INPUT / "raw-binding.json")}}


if __name__ == "__main__":
    result = audit()
    destination = Path(__file__).resolve().parent
    (destination / "E1-VERIFICATION.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["E1 saved-result verification: PASS", "48 saved Luna outputs; 24 paired topics,12 train/12 held-out test.",
             "144/144 completed matched replays;0 failures;144 source/terminal hash receipts match.",
             f"{result['stream_counts']['s2c_streams']} S2C and{result['stream_counts']['direction_streams']} total ciphertext direction streams parsed independently.",
             "Saved size-only rules, test correct/24:"]
    lines += [f"  {r['arm']} / {r['site']}: {r['test_correct']}/24; sizes{r['test_sizes_min_max']}; rule{r['saved_rule']}" for r in result["attacks"]]
    lines += ["Padded application payload16768 bytes; application wire16848 bytes per link/response. Baseline mean{baseline:.6f}; ratio{ratio:.6f}.".format(
        baseline=result["baseline_mean_application_wire_bytes"], ratio=result["padded_to_baseline_ratio_of_aggregate_application_wire_bytes"])]
    lines += result["interpretation"]
    lines += ["No new model calls, TLS replay, bootstrap simulation, model fit, or experiment-source edits occurred in this verification."]
    (destination / "E1-VERIFICATION.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "s2c_streams": result["stream_counts"]["s2c_streams"], "frozen_sources": result["frozen_sources_verified"], "manifest_files": result["manifest_files_verified"], "ratio": result["padded_to_baseline_ratio_of_aggregate_application_wire_bytes"]}))
