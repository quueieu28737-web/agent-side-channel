"""Read-only delivery verification; standard library, no experimental reruns."""
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parent


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def safe(root, relative):
    relative = PurePosixPath(relative)
    assert not relative.is_absolute() and ".." not in relative.parts
    assert ":" not in str(relative)
    result = root.joinpath(*relative.parts)
    assert result.is_file() and not result.is_symlink(), str(result)
    return result


def closure(root, entry):
    found = set()

    def visit(name):
        if name in found:
            return
        found.add(name)
        text = safe(root, name).read_text(encoding="utf-8-sig")
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        text = re.sub(r"\\iffalse\b.*?\\fi\b", "", text, flags=re.S)
        for child in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            visit(child if Path(child).suffix else child + ".tex")
        for items in re.findall(r"\\bibliography\s*\{([^}]+)\}", text):
            for item in items.split(","):
                item = item.strip() + ".bib"
                safe(root, item)
                found.add(item)
        for item in re.findall(r"\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}", text):
            options = [item] if Path(item).suffix else [
                item + ext for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps")
                if (root / (item + ext)).is_file()]
            assert len(options) == 1, item
            safe(root, options[0])
            found.add(options[0])

    visit(entry)
    return sorted(found)


def check_manifest(root, manifest_name):
    manifest = load(root / manifest_name)
    expected = manifest["files"]
    local_only = manifest.get("local_only_directories", [])
    assert not local_only or (root == ROOT and local_only == ["experiments/sp2027-r4"])
    # The continuing collector is not part of the immutable publication package.
    # The committed snapshot has its own complete manifest membership.
    paths = []
    def walk(folder):
        for path in folder.iterdir():
            rel = path.relative_to(root).as_posix()
            if rel in local_only or path.name == "__pycache__":
                continue
            paths.append(path)
            if path.is_dir() and not path.is_symlink():
                walk(path)
    walk(root)
    assert not any(path.is_symlink() for path in paths)
    actual = {path.relative_to(root).as_posix() for path in paths if path.is_file()}
    assert actual == set(expected) | {manifest_name}, "Manifest membership differs"
    for name, value in expected.items():
        assert digest(safe(root, name)) == value, name
    return len(expected)


def main():
    count = check_manifest(ROOT, "SHA256SUMS.json")
    snapshot = load(ROOT / "provenance/snapshot.json")
    for name, doc in snapshot["documents"].items():
        assert closure(ROOT / "manuscript", doc["entry"]) == doc["closure"], name
        assert digest(safe(ROOT, doc["pdf"])) == doc["pdf_sha256"], name
    for name, value in snapshot["source_hashes"].items():
        assert digest(safe(ROOT / "manuscript", name)) == value, name
    prior = ROOT / "evidence/retained-release007"
    assert digest(prior / "SHA256SUMS.json") == snapshot["retained_manifest_sha256"]
    retained_count = check_manifest(prior, "SHA256SUMS.json")

    tau = ROOT / "experiments/tau-cover-bridge"
    run = tau / "runs/continuation-002"
    rows = [json.loads(line) for line in (run / "episodes.jsonl").read_bytes().splitlines() if line.strip()]
    keys = lambda row: (row["task_id"], row["seed"], row["position"], row["arm"])
    index = {keys(row): row for row in rows}
    arms = ["baseline", "discard", "shadow", "read_only", "live_mutation"]
    expected = {(task, seed, pos, arm) for task in range(115)
                for seed in (20261021, 20261022, 20261023)
                for pos in ("before", "after") for arm in arms}
    assert len(rows) == len(index) == 3450 and set(index) == expected
    assert Counter(row["arm"] for row in rows) == {arm: 690 for arm in arms}
    carried = [json.loads(line) for line in (tau / "runs/frozen-001/episodes.jsonl").read_bytes().splitlines() if line.strip()]
    assert len(carried) == 851 and all(index[keys(row)] == row for row in carried)
    receipt = load(run / "verification.json")
    assert receipt["status"] == "VERIFIED_SAVED_CENSUS_AND_NATIVE_RESCORING"
    assert receipt["cells"] == 3450 and receipt["tasks"] == 115
    assert receipt["unique_task_final_states_rescored"] == 244
    assert len({(row["task_id"], row["final_state_hash"]) for row in rows}) == 244
    assert receipt["carried_cells_unchanged"] == 851

    # Verify M1-M8 revision suite artifacts
    rev = ROOT / "experiments/revision-m1-m8"
    m1_val = load(rev / "m1_validity_summary.json")
    assert m1_val["benchmark_cases"] == 24
    assert round(m1_val["inter_annotator_agreement"]["cohen_kappa"], 3) == 0.795
    m3_m4 = load(rev / "m3_m4_exact_breakdown.json")
    assert m3_m4["before"]["eligible_97_tasks"]["tasks"] == 97
    assert m3_m4["after"]["eligible_97_tasks"]["cover_call_error_count"] == 120
    assert m3_m4["pre_insertion_coinciding_reward1_tasks"]["task_count"] == 12
    m6_rec = load(rev / "m6_corpus_reconciliation.json")
    assert m6_rec["final_merged_82_family_accounting"]["final_total_families"] == 82
    assert m6_rec["final_merged_82_family_accounting"]["final_core"] == 58
    assert m6_rec["final_merged_82_family_accounting"]["final_adjacent"] == 24
    m7_dc = load(rev / "m7_dual_coding_summary.json")
    assert m7_dc["screening_100_subsample"]["three_class_routing"]["n"] == 100
    assert m7_dc["split_check_audit_144_cells"]["n"] == 144
    assert m7_dc["pairwise_comparability_50_pairs_150_judgments"]["n"] == 150

    print(json.dumps({"status": "PACKAGE_BYTES_CLOSURES_SAVED_CENSUS_AND_M1_M8_REVISION_PASS",
                      "manifest_files": count, "preserved_release_files": retained_count,
                      "tau_tasks": 115, "tau_eligible_tasks": 97, "tau_units": 3450,
                      "prior_rows_preserved": 851, "distinct_saved_task_states": 244,
                      "m1_retrospective_cases": 24, "m1_kappa": round(m1_val["inter_annotator_agreement"]["cohen_kappa"], 3),
                      "m7_dual_coding_kappas": {
                          "screening_100": round(m7_dc["screening_100_subsample"]["three_class_routing"]["cohen_kappa"], 3),
                          "audit_144": round(m7_dc["split_check_audit_144_cells"]["cohen_kappa"], 3),
                          "pairs_150": round(m7_dc["pairwise_comparability_50_pairs_150_judgments"]["cohen_kappa"], 3),
                      },
                      "historical_revision_model_calls": 0,
                      "fourth_round": snapshot.get("fourth_round"),
                      "uploads": 0}, indent=2))


if __name__ == "__main__":
    main()
