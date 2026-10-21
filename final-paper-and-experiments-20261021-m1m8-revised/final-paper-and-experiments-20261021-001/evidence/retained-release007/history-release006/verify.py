"""Read-only release006 verifier: two documents, unchanged004, derived audit."""
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PRIOR_MANIFEST_SHA256 = "acbb96faf83851a83a17b904cb938148af04fa16614819b2a8ff47035879357e"
DOCUMENTS = {"main": ("main.tex", "paper.pdf"),
             "supplement": ("supplement.tex", "supplement.pdf")}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def inside(root, relative):
    rel = PurePosixPath(str(relative).replace("\\", "/"))
    assert not rel.is_absolute() and ".." not in rel.parts and ":" not in str(rel)
    root = Path(root).resolve()
    path = root.joinpath(*rel.parts)
    assert root in path.resolve().parents and not path.is_symlink()
    return path


def check_manifest(root):
    root = Path(root).resolve()
    manifest = load(root / "SHA256SUMS.json")
    assert manifest["algorithm"] == "SHA256"
    files = manifest["files"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert "SHA256SUMS.json" not in files
    assert actual == set(files) | {"SHA256SUMS.json"}, "Exact file membership"
    assert not any(p.is_symlink() for p in root.rglob("*"))
    for name, digest in files.items():
        assert re.fullmatch("[0-9a-f]{64}", digest) and sha(inside(root, name)) == digest, name
    return manifest


def active_tex_closure(root, entry):
    """Explicit per-document entry, preserving ordinary TeX input/figure closure."""
    found = set()

    def visit(relative):
        if relative in found:
            return
        found.add(relative)
        text = inside(root, relative).read_text(encoding="utf-8-sig")
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        text = re.sub(r"\\iffalse\b.*?\\fi\b", "", text, flags=re.S)
        for name in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            visit(name if Path(name).suffix else name + ".tex")
        for names in re.findall(r"\\bibliography\s*\{([^}]+)\}", text):
            found.update(n.strip() + ".bib" for n in names.split(","))
        for name in re.findall(r"\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}", text):
            if Path(name).suffix:
                found.add(name)
            else:
                matches = [name + ext for ext in (".pdf", ".png", ".jpg", ".jpeg")
                           if inside(root, name + ext).is_file()]
                assert len(matches) == 1, "Unresolved figure " + name
                found.add(matches[0])

    visit(entry)
    assert all(inside(root, p).is_file() for p in found)
    return sorted(found)


def prior_common(prior):
    spec = importlib.util.spec_from_file_location("historical_release_common", prior / "release_common.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_documents(root, prior):
    binding = load(root / "current/release-binding.json")
    sources = load(root / "current/source-hashes.json")
    closures = load(root / "current/document-closures.json")
    qa = load(root / "current/pdf-validation.json")
    assert set(closures) == set(DOCUMENTS)
    union = set()
    for document, (entry, pdf) in DOCUMENTS.items():
        actual = active_tex_closure(root / "manuscript", entry)
        assert closures[document] == actual
        union.update(actual)
        check = qa[document]
        assert sha(root / pdf) == check["pdf_sha256"] == binding["documents"][document]["pdf_sha256"]
        assert check["pages"] > 0 and check["US_letter"] and not check["log_failures"]
        assert not check.get("bib_warnings", []) and check["author"] in ("", None)
        assert len(actual) == binding["documents"][document]["active_source_count"]
    assert set(sources) == union
    for relative, digest in sources.items():
        assert sha(inside(root / "manuscript", relative)) == digest
    assert sha(root / "current/source-hashes.json") == binding["source_hashes_sha256"]
    assert sha(root / "current/document-closures.json") == binding["document_closures_sha256"]
    assert qa["main"]["body_pages"] <= 13 and qa["main"]["appendix_pages"] <= 5
    assert qa["main"]["pages"] == sum(qa["main"][k] for k in
                                      ("body_pages", "appendix_pages", "reference_pages"))
    registry = load(prior / "claims/claim-registry.json")
    old = {r["claim_id"]: r for r in registry["claims"]}
    locator_record = load(root / "current/claim-locators.json")
    claims = {r["claim_id"]: r for r in locator_record["claims"]}
    assert len(claims) == len(locator_record["claims"]) == len(old)
    assert set(claims) == set(old)
    for identifier, claim in claims.items():
        assert claim["historical_bounded_claim"] == old[identifier]["bounded_claim"]
        assert claim["historical_registry"] == "evidence-release004/claims/claim-registry.json"
        assert claim["anchors"]
        for anchor in claim["anchors"]:
            assert anchor["document"] in DOCUMENTS
            assert anchor["path"] in closures[anchor["document"]]
            text = inside(root / "manuscript", anchor["path"]).read_text(encoding="utf-8-sig")
            assert sources[anchor["path"]] == anchor["source_sha256"]
            matches = list(re.finditer(anchor["pattern"], text))
            assert len(matches) == 1, (identifier, anchor["path"], len(matches))
            match = matches[0]
            assert match.group() == anchor["matched_text"]
            assert text.count("\n", 0, match.start()) + 1 == anchor["line"]
    assert binding["prior_manifest_sha256"] == PRIOR_MANIFEST_SHA256
    assert binding["original_scientific_evidence_copied_unchanged"] is True
    for field in ("new_model_requests", "new_fits", "new_Luna_runs", "new_network_requests", "human_returns"):
        assert binding[field] == 0
    for field in ("old_release_modified", "uploaded", "submitted", "public_hosting_claimed",
                  "anonymity_or_rights_certified"):
        assert binding[field] is False
    return binding, qa, claims


def check_additions(root, prior):
    materials = load(root / "current/additional-materials.json")
    assert materials["source_files_modified"] is False
    targets = [r["target"] for r in materials["rows"]]
    assert len(targets) == len(set(targets))
    for row in materials["rows"]:
        assert sha(inside(root, row["target"])) == row["released_sha256"]
        assert re.fullmatch("[0-9a-f]{64}", row["original_sha256"])
        if row["target"].startswith("decision-audit/"):
            assert row["original_sha256"] == row["released_sha256"]
    declared_audit = {p.removeprefix("decision-audit/") for p in targets if p.startswith("decision-audit/")}
    actual_audit = {p.relative_to(root / "decision-audit").as_posix()
                    for p in (root / "decision-audit").rglob("*") if p.is_file()}
    assert declared_audit and actual_audit == declared_audit
    # Ownership inventory carries source identities, never source full texts.
    ownership = load(root / "current/external-source-ownership.json")
    registry = load(prior / "claims/claim-registry.json")
    units = {r["canonical_unit_id"]: r for r in registry["canonical_unit_index"]}
    expected = registry["verified_primary_source_hashes"]
    assert ownership["source_hashes"] == expected
    assert ownership["raw_full_text_redistributed"] is False
    assert ownership["local_byte_checks_at_build"] is True
    assert {r["unit_id"] for r in ownership["result_ownership"]} == set(units)
    for row in ownership["result_ownership"]:
        old = units[row["unit_id"]]
        assert row["family_id"] == old["family_id"]
        assert row["source_path"] == old["source_path"]
        assert row["source_sha256"] == expected[row["source_path"]] == old["source_sha256"]
    query = load(root / "discovery-history/novelty-2026-10-08-queries.json")
    assert query["raw_search_results_redistributed"] is False
    assert query["query_count"] == sum(len(r["queries"]) for r in query["records"])
    return materials


def run_saved_checkers(root, prior):
    historical = subprocess.run([sys.executable, "-B", str(prior / "verify.py")], cwd=prior,
                                capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert historical.returncode == 0, historical.stdout + historical.stderr
    result = json.loads(historical.stdout)
    assert result["status"] == "LOCAL_RELEASE004_CHECKS_PASS"
    assert (result["fits"], result["model_calls"], result["network_requests"]) == (0, 0, 0)
    # The exact no-write audit CLI is frozen by the builder only after its owner
    # supplies the implementation. Never auto-select or run an executable from data.
    checker = load(root / "current/decision-audit-checker.json")
    assert checker["mode"] == "read-only-check"
    assert checker["script"] == "decision-audit/audit.py"
    assert sha(root / checker["script"]) == checker["script_sha256"]
    assert checker["arguments"] == ["--check", "--release-root", "evidence-release004"]
    audit = subprocess.run([sys.executable, "-B", str(root / checker["script"]),
                            "--check", "--release-root", str(prior)], cwd=root,
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert audit.returncode == 0, audit.stdout + audit.stderr
    return result, audit.stdout.strip()


def main():
    manifest = check_manifest(HERE)
    prior = HERE / "evidence-release004"
    assert sha(prior / "SHA256SUMS.json") == PRIOR_MANIFEST_SHA256
    check_manifest(prior)
    binding, qa, claims = check_documents(HERE, prior)
    materials = check_additions(HERE, prior)
    scientific, audit = run_saved_checkers(HERE, prior)
    check_manifest(HERE)
    print(json.dumps({
        "status": "LOCAL_RELEASE006_CHECKS_PASS", "manifest_files": len(manifest["files"]),
        "document_pages": {k: qa[k]["pages"] for k in DOCUMENTS},
        "fixed_claim_ids": sorted(claims), "derived_material_files": len(materials["rows"]),
        "historical_evidence_manifest_sha256": PRIOR_MANIFEST_SHA256,
        "inherited_scientific_verifier": scientific, "decision_audit_checker": audit,
        "new_model_requests": 0, "new_fits": 0, "new_Luna_runs": 0, "network_requests": 0,
        "scope": "Current bytes/navigation and saved derived arithmetic; no semantic certification or human independence."
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
