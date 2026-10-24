"""Check R7-D's supplemental dependency closure without modifying frozen inputs."""
import argparse, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SPEC = HERE / "robustness-extra-dependencies.json"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def bounded(root, rel):
    p = pathlib.Path(rel)
    assert not p.is_absolute() and ".." not in p.parts and p.parts[0] == "experiments", rel
    q = (root / p).resolve()
    assert q.is_relative_to(root) and q.is_file(), ("missing/out-of-root dependency", rel)
    return q

def check(package):
    root = pathlib.Path(package).resolve()
    d = root / "experiments/sp2027-r7-robustness"
    l = root / "experiments/sp2027-r7-localization"
    spec = read(SPEC)
    closure = read(d / "dependency-closure.json")
    assert sha(SPEC) == closure["closure_source_sha256"]
    assert closure["shared_localization_closure"]["closure_sha256"] == sha(l / "dependency-closure.json")

    # Reuse the official, unfrozen L closure checker; it validates all 36 path/hash/authority bindings.
    sys.path.insert(0, str(l))
    import dependency_check
    l_receipt = dependency_check.check(l)
    assert l_receipt["passed"] and l_receipt["dependencies"] == 36
    assert l_receipt["closure_sha256"] == closure["shared_localization_closure"]["closure_sha256"]

    # Check the R6 authority files and explicit hash chain.
    authority_hashes = {}
    for item in spec["authority_files"]:
        p = bounded(root, item["relative_path"])
        assert sha(p) == item["sha256"], ("authority SHA mismatch", item["relative_path"])
        authority_hashes[item["relative_path"]] = read(p)
    freeze_rel = "experiments/sp2027-r7-robustness/freeze.json"
    freeze = read(bounded(root, freeze_rel))
    data = {e["relative_path"]: e for e in spec["direct_r6_data_dependencies"]}
    for rel, e in data.items():
        p = bounded(root, rel)
        assert sha(p) == e["sha256"] == e["copied_sha256"], ("data SHA mismatch", rel)
        if rel.endswith("captures.zip"):
            assert freeze["r6_captures_sha256"] == e["sha256"]
        elif rel.endswith(("predictions.json", "results.json")):
            auth = authority_hashes["experiments/sp2027-r6-timing/reproduction_validation.json"]
            assert auth["outputs"][pathlib.Path(rel).name] == e["sha256"]
    attack_rel = "experiments/sp2027-r6-timing/attacker_freeze.json"
    frozen_rel = "experiments/sp2027-r6-timing/frozen.json"
    reproduction_rel = "experiments/sp2027-r6-timing/reproduction_validation.json"
    assert authority_hashes[attack_rel]["frozen_sha256"] == sha(bounded(root, frozen_rel))
    assert authority_hashes[reproduction_rel]["attacker_freeze_sha256"] == sha(bounded(root, attack_rel))

    # Shared imported helpers must be members of the common 36-item closure.
    shared = {x["relative_path"]: x["sha256"] for x in closure["shared_localization_closure"]["dependencies"]}
    for e in spec["direct_import_source_dependencies"]:
        assert shared.get(e["relative_path"]) == e["sha256"]
        assert sha(bounded(root, e["relative_path"])) == e["sha256"]

    receipt = {
        "status": "PASS",
        "scope": "supplemental portable dependency closure; no model training or frozen artifact changes",
        "shared_dependencies": 36,
        "shared_closure_sha256": sha(l / "dependency-closure.json"),
        "r6_import_helpers": len(spec["direct_import_source_dependencies"]),
        "r6_data_files": len(data),
        "r6_authority_files": len(spec["authority_files"]),
        "r6_captures_bound_by": "sp2027-r7-robustness/freeze.json:r6_captures_sha256",
        "r6_predictions_results_bound_by": "sp2027-r6-timing/reproduction_validation.json:outputs",
        "authority_chain": ["attacker_freeze.json:frozen_sha256 -> frozen.json SHA", "reproduction_validation.json:attacker_freeze_sha256 -> attacker_freeze.json SHA"],
        "d_freeze_sha256": sha(d / "freeze.json"),
        "d_protocol_sha256": sha(d / "PROTOCOL.md"),
        "d_verification_sha256": sha(d / "validation.json"),
        "closure_sha256": sha(d / "dependency-closure.json"),
        "source_spec_sha256": sha(SPEC),
    }
    (d / "dependency-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("package", help="root of relocated package tree")
    print(json.dumps(check(ap.parse_args().package), indent=2))
