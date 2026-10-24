"""Verify the local benchmark/source dependencies used by the Luna public-ZIP audit.

Read-only with respect to the experiment package. Writes only this folder's closure and receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_SHA256 = "669b9df6f733631f7bd4bc918ef000d4cecad2bb16dfc1552e9949ca6fee4105"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def file_record(root, rel, expected, authority, key, role):
    p = root / Path(rel)
    assert p.is_file(), ("missing dependency", rel)
    digest = sha(p)
    assert digest == expected, ("dependency hash mismatch", rel, digest, expected)
    return {"relative_path": rel.replace("\\", "/"), "sha256": digest,
            "authority": authority, "authority_key": key, "role": role}

def verify(package):
    root = Path(package).resolve()
    exp = root / "experiments"
    a = exp / "sp2027-r7-agent-extension"
    r4 = exp / "sp2027-r4-snapshot-20261023"
    prior_path = root / "provenance/r7-review/prior-package-manifest.json"
    prior = read(prior_path)
    assert sha(prior_path) == PRIOR_SHA256, "prior package manifest changed"
    prior_files = prior["files"]

    runtime_rel = "experiments/sp2027-r4-snapshot-20261023/runtime_manifest.json"
    runtime_path = root / Path(runtime_rel)
    runtime_sha = sha(runtime_path)
    assert prior_files[runtime_rel] == runtime_sha, "R4 runtime manifest not bound by prior manifest"
    runtime = read(runtime_path)

    # This is the exact set opened or exec'd by reviewer-audit/retail_replay.py:load_tau().
    keys = [
        "reviewer-audit\\retail_replay.py",
        "tau-cover-bridge\\vendor\\tau_bench__types.py",
        "tau-cover-bridge\\vendor\\tau_bench__envs__tool.py",
        "tau-cover-bridge\\vendor\\tau_bench__envs__base.py",
        "tau-cover-bridge\\vendor\\tau_bench__envs__retail__tasks_test.py",
        "tau-cover-bridge\\vendor\\tau_bench__envs__retail__data__orders.json",
        "tau-cover-bridge\\vendor\\tau_bench__envs__retail__data__users.json",
        "tau-cover-bridge\\vendor\\tau_bench__envs__retail__data__products.json",
    ]
    tool_prefix = "tau-cover-bridge\\vendor\\tau_bench__envs__retail__tools__"
    tools = sorted(k for k in runtime["files"]
                   if k.startswith(tool_prefix) and k.endswith(".py") and not k.endswith("____init__.py"))
    assert len(tools) == 16, ("unexpected load_tau tool module set", tools)
    keys += tools
    assert len(keys) == 24 and len(set(keys)) == len(keys)

    deps = []
    for key in keys:
        rel = "experiments/" + key.replace("\\", "/")
        authority_key = key
        if key == "reviewer-audit\\retail_replay.py":
            # runtime_manifest uses the reviewer-audit key; prior manifest independently binds the file.
            pass
        expected = runtime["files"][key]
        assert prior_files[rel] == expected, ("prior/runtime manifest disagreement", rel)
        deps.append(file_record(root, rel, expected, runtime_rel, authority_key, "load_tau code/data"))

    # Freeze the path chain and both public validation call paths.
    app_freeze_path = a / "APPENDED_ANALYSIS_FREEZE.json"
    app_freeze = read(app_freeze_path)
    plan_path = a / "formal_plan.json"
    plan_sha = sha(plan_path)
    assert app_freeze["formal_plan_sha256"] == plan_sha
    plan = read(plan_path)
    assert plan["files"]["common.py"] == sha(a / "common.py")
    for name in ("verify_formal.py", "verify_public.py", "package_raw.py"):
        assert app_freeze["files"][name] == sha(a / name), ("analysis freeze mismatch", name)
    decision_add_path = a / "DECISION_ALIGNMENT_ADDITION.json"
    decision_add = read(decision_add_path)
    assert decision_add["formal_plan_sha256"] == plan_sha
    for name in ("verify_decisions.py", "verify_public_decisions.py"):
        assert decision_add["files"][name] == sha(a / name), ("decision addition mismatch", name)

    code_records = [
        file_record(root, "experiments/sp2027-r7-agent-extension/common.py", plan["files"]["common.py"],
                    "formal_plan.json (SHA anchored by APPENDED_ANALYSIS_FREEZE.json)", "files.common.py", "public audit loader"),
    ]
    for name in ("verify_formal.py", "verify_public.py", "package_raw.py"):
        code_records.append(file_record(root, f"experiments/sp2027-r7-agent-extension/{name}",
                         app_freeze["files"][name], "APPENDED_ANALYSIS_FREEZE.json", f"files.{name}", "public audit"))
    for name in ("verify_decisions.py", "verify_public_decisions.py"):
        code_records.append(file_record(root, f"experiments/sp2027-r7-agent-extension/{name}",
                         decision_add["files"][name], "DECISION_ALIGNMENT_ADDITION.json", f"files.{name}", "public decision alignment"))

    common_text = (a / "common.py").read_text(encoding="utf-8")
    replay_text = (exp / "reviewer-audit/retail_replay.py").read_text(encoding="utf-8")
    package_text = (a / "package_raw.py").read_text(encoding="utf-8")
    public_text = (a / "verify_public.py").read_text(encoding="utf-8")
    decisions_text = (a / "verify_decisions.py").read_text(encoding="utf-8")
    assert "sys.path.insert(0, str(path))" in common_text and "EXP/'reviewer-audit'" in common_text
    assert "import retail_replay as old" in common_text and "return old.load_tau()" in common_text
    assert "VENDOR = TAU_DIR / \"vendor\"" in replay_text and "def load_tau():" in replay_text
    assert "for file in sorted(VENDOR.glob(\"tau_bench__envs__retail__tools__*.py\"))" in replay_text
    assert "paths=sorted(p for sub in ['connectivity','pilot','formal']" in package_text
    assert "import verify_formal as vf" in public_text and "vf.HERE=target;vf.main()" in public_text
    assert "ns,tools,base,tasks=load()" in decisions_text

    closure = {
        "version": 1,
        "scope": "local checkout dependencies for public ZIP reward/decision recomputation; no experiment outputs modified",
        "chain": [
            "verify_public.py extracts public raw ZIP to a temp tree and calls verify_formal.py",
            "verify_public_decisions.py extracts public raw ZIP and calls verify_decisions.verify",
            "both verifier paths use common.load() -> old.load_tau()",
            "common.py adds experiments/reviewer-audit to sys.path and imports retail_replay as old",
            "retail_replay.py sets VENDOR to experiments/tau-cover-bridge/vendor and load_tau() execs vendor code, loads tasks_test.py, and reads orders/users/products JSON",
        ],
        "source_locators": {
            "common.py": {"path": "experiments/sp2027-r7-agent-extension/common.py", "lines": "11-14, 45-46"},
            "retail_replay.py": {"path": "experiments/reviewer-audit/retail_replay.py", "lines": "34-37, 495-520"},
            "verify_public.py": {"path": "experiments/sp2027-r7-agent-extension/verify_public.py", "lines": "7-25"},
            "verify_formal.py": {"path": "experiments/sp2027-r7-agent-extension/verify_formal.py", "lines": "6-31"},
            "verify_public_decisions.py": {"path": "experiments/sp2027-r7-agent-extension/verify_public_decisions.py", "lines": "5-15"},
            "verify_decisions.py": {"path": "experiments/sp2027-r7-agent-extension/verify_decisions.py", "lines": "7-13, 42-60"},
            "package_raw.py": {"path": "experiments/sp2027-r7-agent-extension/package_raw.py", "lines": "5-18"},
        },
        "authorities": {
            "prior_package_manifest": {"path": "provenance/r7-review/prior-package-manifest.json", "sha256": PRIOR_SHA256},
            "r4_runtime_manifest": {"path": runtime_rel, "sha256": runtime_sha, "bound_by_prior_manifest": True},
            "formal_plan": {"path": "experiments/sp2027-r7-agent-extension/formal_plan.json", "sha256": plan_sha, "bound_by": "APPENDED_ANALYSIS_FREEZE.json:formal_plan_sha256"},
            "appended_analysis_freeze": {"path": "experiments/sp2027-r7-agent-extension/APPENDED_ANALYSIS_FREEZE.json", "sha256": sha(app_freeze_path)},
            "decision_alignment_addition": {"path": "experiments/sp2027-r7-agent-extension/DECISION_ALIGNMENT_ADDITION.json", "sha256": sha(decision_add_path)},
        },
        "load_tau_dependencies": deps,
        "validation_code": code_records,
        "excluded": [
            {"path": "experiments/tau-cover-bridge/vendor/tau_bench__envs__retail__tools____init__.py", "reason": "retail_replay.load_tau explicitly skips files ending ____init__.py"},
            {"path": "experiments/tau-cover-bridge/vendor/tau_bench__envs__retail__wiki.md", "reason": "not read by load_tau or verify_public/verify_public_decisions reward/alignment recomputation"},
        ],
        "public_zip_scope": "package_raw.py archives connectivity/, pilot/, formal/ raw evidence only; it does not bundle the R4 vendored task/tool source or datasets. Public-ZIP validation therefore requires this hash-verified checkout/runtime and is not archive-self-contained.",
    }
    closure_path = HERE / "luna-dependency-closure.json"
    closure_path.write_text(json.dumps(closure, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "status": "PASS",
        "scope": "read-only dependency/source closure check; no model run; only O closure and receipt written",
        "load_tau_code_and_data_files": len(deps),
        "verification_code_files": len(code_records),
        "prior_manifest_sha256": PRIOR_SHA256,
        "r4_runtime_manifest_sha256": runtime_sha,
        "formal_plan_sha256": plan_sha,
        "public_zip_is_self_contained": False,
        "external_local_dependency": "hash-verified checkout R4 vendor/tasks at experiments/tau-cover-bridge/vendor",
        "closure_sha256": sha(closure_path),
        "checker_sha256": sha(Path(__file__).resolve()),
    }
    (HERE / "luna-dependency-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="package root containing experiments/ and provenance/")
    print(json.dumps(verify(parser.parse_args().package), indent=2))
