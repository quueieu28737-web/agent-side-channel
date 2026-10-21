"""Read-only, standard-library checks of a saved release; no research execution."""
import collections
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import runpy
import sys

sys.dont_write_bytecode = True

from release_common import (active_tex_closure, blind_locator, canonical_checks, case_id, claim_locator,
                            digest, exclusion_index, fact_link, field_link, ids, inside, load,
                            object_rows, rows, source_version)

HERE = Path(__file__).resolve().parent


def sha(path):
    return digest(path.read_bytes())


def equal_cells(actual, expected):
    for key, value in expected.items():
        assert str(actual[key]) == str(value), (key, actual[key], value)


def saved_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, inside(HERE, relative))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    manifest = load(HERE / "SHA256SUMS.json")
    assert manifest["algorithm"] == "SHA256"
    files = manifest["files"]
    assert "SHA256SUMS.json" not in files
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    assert actual == set(files) | {"SHA256SUMS.json"}, "Exact release membership mismatch"
    for relative, expected in files.items():
        assert re.fullmatch(r"[0-9a-f]{64}", expected)
        assert sha(inside(HERE, relative)) == expected, "File hash mismatch: " + relative
    assert not any(p.is_symlink() for p in HERE.rglob("*"))
    assert not any(p.startswith("literature/claim-audit/") for p in files)
    assert "literature/field-audit/load-bearing-fields.csv" not in files

    corpus = rows(HERE / "literature/final-inclusion-ledger.csv")
    units = rows(HERE / "literature/interventions/intervention-result-units.csv")
    fields = rows(HERE / "literature/field-audit/utility-cost-dispositions.csv")
    subset = rows(HERE / "empirical/derived-001/mitigation-question-subset.csv")
    family, unit = canonical_checks(corpus, units, fields, subset)
    field_index = {(r["unit_id"], r["field"]): r for r in fields}
    assert {r["field"] for r in fields} == {"objective_task_utility", "performance_cost"}
    counts = load(HERE / "literature/counts.json")
    assert (counts["total"], counts["core"], counts["adjacent"]) == (60, 43, 17)
    core = [r for r in corpus if r["classification"] == "core"]
    assert sum(r["ring"] == "A" for r in core) == counts["A"] == 15
    assert sum(r["ring"] == "B" for r in core) == counts["B"] == 28
    states = rows(HERE / "literature/interventions/current-core-intervention-status.csv")
    assert {r["citation_key"] for r in states} == {r["citation_key"] for r in core}
    assert dict(collections.Counter(r["status"] for r in states)) == counts["intervention_statuses"]

    audit = load(HERE / "empirical/derived-001/deployment-subset-audit.json")
    assert (audit["all_units"], audit["all_fields"], audit["selected_units"], audit["context_units"]) == (33, 66, 26, 7)
    assert audit["new_fits"] == audit["new_model_requests"] == audit["network_requests"] == 0
    all33 = rows(HERE / "empirical/derived-001/all33-dispositions.csv")
    assert len(all33) == 33 and {r["unit_id"] for r in all33} == set(unit)
    for record in all33 + subset + audit["all_33_annotated_rows"]:
        equal_cells(record, unit[record["unit_id"]])
    all66 = rows(HERE / "empirical/derived-001/all66-utility-cost-fields.csv")
    assert len(all66) == len(audit["all_66_input_field_rows_unchanged"]) == 66
    for record in all66 + audit["all_66_input_field_rows_unchanged"]:
        equal_cells(record, field_index[(record["unit_id"], record["field"])])

    registry = object_rows(load(HERE / "claims/claim-registry.json"))
    claim = {r["claim_id"]: r for r in registry}
    assert len(claim) == len(registry) and claim
    for record in registry:
        assert record.get("statement", record.get("bounded_claim")) and claim_locator(record)
        for anchor in record.get("manuscript_anchors", []):
            assert sha(inside(HERE / "manuscript", anchor["path"])) == anchor["snapshot_sha256"]
    maps = [field_link(r) for r in rows(HERE / "claims/field-claim-map.csv")]
    mapping = {(r["unit_id"], r["field"]): r for r in maps}
    assert len(maps) == len(mapping) == 66 and set(mapping) == set(field_index)
    assert dict(collections.Counter(r["support_role"] for r in maps)) == {
        "DIRECT_SUPPORT": 14, "CLAIM_LIMIT": 13, "BACKGROUND_ONLY": 39}
    trace = rows(HERE / "traceability/family-result-field-claim.csv")
    assert len(trace) == 66
    assert {(r["canonical_unit_id"], r["field_id"]) for r in trace} == set(field_index)
    for record in trace:
        current = unit[record["canonical_unit_id"]]
        field = field_index[(record["canonical_unit_id"], record["field_id"])]
        link = mapping[(record["canonical_unit_id"], record["field_id"])]
        assert record["family_id"] == current["citation_key"] in family
        assert record["result_locator"] == current["scope"]
        assert record["result_source_sha256"] == current["source_sha256"]
        assert record["result_source_version"] == source_version(current["source_url"])
        assert record["field_source_scope_recorded"] == field["inspected_scope"]
        assert record["field_disposition_recorded"] == field["field_disposition"]
        assert record["current_extraction"] == field.get("current_extraction", field["original_extraction_unchanged"])
        assert record["claim_id"] == link["claim_id"]
        assert record["claim_support_role"] == link["support_role"]
        assert ids(record["claim_id"])
        assert all(c in claim or c == "BACKGROUND_ONLY" for c in ids(record["claim_id"]))
        assert record["claim_locator"] == " | ".join(claim_locator(claim[c]) for c in ids(record["claim_id"]) if c in claim)

    source_facts = {case_id(r): r for r in rows(HERE / "synthesis/source-evidence.csv")}
    fact_maps = {case_id(r): fact_link(r) for r in rows(HERE / "claims/case-fact-map.csv")}
    facts = rows(HERE / "synthesis/case-facts-index.csv")
    assert len(source_facts) == len(fact_maps) == len(facts) == 15
    assert set(source_facts) == set(fact_maps) == {r["source_fact_alias"] for r in facts}
    assert len({r["case_fact_id"] for r in facts}) == 15
    for record in facts:
        alias = record["source_fact_alias"]
        original, link = source_facts[alias], fact_maps[alias]
        assert record["case_fact_id"] == "FACT:" + alias
        assert original["current_case_fact_id"] == record["case_fact_id"]
        assert record["case_fact_id"] not in unit
        assert record["record_kind"] == "case_fact_not_canonical_result"
        assert record["family_id"] == original["citation_key"] in family
        bound, related = ids(record["canonical_unit_id"]), ids(record["related_canonical_unit_id"])
        assert bound == ids(link["canonical_unit_id"]) and related == ids(link["related_canonical_unit_id"])
        assert all(k in unit and unit[k]["citation_key"] == record["family_id"] for k in bound + related)
        assert record["source_locator"] == link["source_locator"]
        assert original["current_source_locator"] == record["source_locator"]
        assert original["current_canonical_unit_id"] == record["canonical_unit_id"]
        assert original["current_related_canonical_unit_id"] == record["related_canonical_unit_id"]
        assert original["current_relation_kind"] == record["relation_kind"]
        assert original["current_subcondition_label"] == record["subcondition_label"]
        assert record["source_version"] == link["source_version"]
        assert record["source_sha256"] == original["source_sha256"]
        assert record["historical_extraction_read_scope"] == original["read_scope"]
        assert ids(record["claim_id"]) and all(c in claim for c in ids(record["claim_id"]))
        if record["relation_kind"] == "additional_source_subcondition":
            assert not bound and related and record["subcondition_label"]
    no_fake = next(r for r in facts if r["source_fact_alias"] == "AHB-trip-history-long")
    assert no_fake["relation_kind"] == "additional_source_subcondition"
    assert no_fake["canonical_unit_id"] == "" and "0.7143" in no_fake["subcondition_label"]
    dangol = next(r for r in facts if r["source_fact_alias"] == "DANGOL-live-cover")
    assert re.search(r"after\s*Table\s*5", dangol["source_locator"], re.I)
    assert re.search(r"after\s*Table\s*5", unit["DANGOL-livebinding"]["scope"], re.I)
    assert "fresh" in unit["DANGOL-livebinding"]["intervention_condition"].lower()

    assertion_all = object_rows(load(HERE / "claims/assertion-queue.json"))
    assertions = [r for r in assertion_all if r["citation_key"] in audit["four_unbound_defense_assertions"]]
    assert len(assertions) == len({r["assertion_id"] for r in assertions}) == 4
    assert {r["citation_key"] for r in assertions} == set(audit["four_unbound_defense_assertions"])
    joined = load(HERE / "traceability/family-result-field-claim.json")
    assert set(joined["families"]) == set(family)
    assert len(joined["canonical_results"]) == 33 and joined["new_canonical_results"] == 0
    assert joined["field_claim_links"] == trace and joined["case_facts_separate_namespace"] == facts
    assert len(joined["unbound_assertions"]) == 4
    assert joined["additional_code_run_binding_records"] == [r for r in assertion_all if r not in assertions]

    correction_records = load(HERE / "revision/source-corrections-applied.json")
    assert len(correction_records) == 4
    for correction in correction_records:
        released = rows(inside(HERE, correction["target"]))
        matches = [r for r in released if all(r[k] == v for k, v in correction["key"].items())]
        assert len(matches) == 1
        expected = dict(correction["before"])
        expected.update(correction["set"])
        for key, text in correction["append"].items():
            expected[key] = expected.get(key, "") + "\n" + text
        assert matches[0] == expected
    proof = load(HERE / "traceability/source-hash-proof.json")
    assert not proof["source_authenticity_certified"]
    proofs = {r["source_path"]: r for r in proof["checks"]}
    assert len(proofs) == len(proof["checks"]) and proofs
    for record in proofs.values():
        inside(HERE, record["source_path"])  # Validate relative syntax, not omitted bytes.
        assert record["match"] is True
        assert record["expected_sha256"] == record["actual_sha256"]
        assert re.fullmatch("[0-9a-f]{64}", record["actual_sha256"])
        assert record["source_bytes_redistributed"] == any(
            files[target] == record["actual_sha256"] for target in record["packaged_copy_targets"])
    for record in units + list(source_facts.values()):
        assert proofs[record["source_path"]]["actual_sha256"] == record["source_sha256"]
    provenance = load(HERE / "source-copy-provenance.json")
    assert not provenance["source_files_modified"]
    assert len({r["target"] for r in provenance["files"]}) == len(provenance["files"])
    for record in provenance["files"]:
        assert files[record["target"]] == record["released_sha256"]
        if not record["transformations"]:
            assert record["original_source_sha256"] == record["released_sha256"]

    active = active_tex_closure(HERE / "manuscript")
    sources = load(HERE / "revision/active-source-hashes.json")
    binding = load(HERE / "revision/release-binding.json")
    qa = load(HERE / "revision/pdf-validation.json")
    assert set(active) == set(sources)
    assert len(active) == binding["active_source_count"]
    for relative, expected in sources.items():
        assert sha(inside(HERE / "manuscript", relative)) == expected
    assert sha(HERE / "paper.pdf") == qa["pdf_sha256"] == binding["pdf_sha256"]
    assert sha(HERE / "revision/active-source-hashes.json") == qa["source_hashes_sha256"] == binding["source_hashes_sha256"]
    assert qa["US_letter"] and qa["within_body13_appendix5"] and not qa["log_failures"]
    assert qa["body_pages"] <= 13 and qa["appendix_pages"] <= 5
    assert qa["pages"] == qa["body_pages"] + qa["appendix_pages"] + qa["reference_pages"]
    assert not any(binding[k] for k in ("new_network_requests", "new_fits", "new_Luna_runs",
               "old_release_modified", "uploaded", "submitted", "public_hosting_claimed",
               "anonymity_or_rights_certified"))
    for name in ("29-scope-comparison-boundary", "17-public-trace-details", "23-defense-comparison"):
        assert "supplement/expanded/sections/" + name + ".tex" in files
    assert "supplement/full-family-index.tex" in files
    assert "supplement/expanded/full-public-trace-protocol-003.tex" in files

    known = load(HERE / "selection/known24-offline-check-summary.json")
    assert known["seed_n"] == len(known["rows"]) == 24
    assert known["ieee_export_frame_unique_records"] == 2001
    assert known["acm_export_frame_publication_groups"] == 13201
    assert known["exact_export_presence_counts"] == {"IEEE": 1, "ACM": 0}
    assert sum(r["ieee_present"] for r in known["rows"]) == 1
    assert sum(r["acm_present"] for r in known["rows"]) == 0
    assert known["indexed_online_all_rows"] == "NR_NOT_QUERIED"
    assert known["native_field_eligibility_all_rows"] == "NR_NOT_EMULATED"
    selection_receipt = load(HERE / "selection/validation-receipt.json")
    released_bindings = {r["artifact"]: r for r in load(
        HERE / "selection/released-artifact-bindings.json")["rows"]}
    assert set(released_bindings) == set(selection_receipt["artifact_sha256"])
    for relative, expected in selection_receipt["artifact_sha256"].items():
        record = next(r for r in provenance["files"] if r["target"] == "selection/" + relative)
        binding_record = released_bindings[relative]
        assert record["original_source_sha256"] == expected, "Original selection receipt mismatch: " + relative
        assert binding_record["original_artifact_sha256"] == expected
        assert binding_record["released_artifact_sha256"] == record["released_sha256"]
        assert sha(inside(HERE / "selection", relative)) == record["released_sha256"]
        assert binding_record["transformations"] == record["transformations"]
    receipt_map = load(HERE / "selection/receipt-source-map.json")
    assert not receipt_map["raw_native_exports_bundled"]
    for receipt in receipt_map["rows"]:
        record = next(r for r in provenance["files"] if r["target"] == receipt["packaged_copy"])
        assert record["original_source_sha256"] == receipt["original_sha256"]
        assert proofs[receipt["private_audit_source"]]["actual_sha256"] == receipt["original_sha256"]

    exclusion = exclusion_index(load(HERE / "claims/exclusion-review-queue.json"))
    status = load(HERE / "independent-review/status.json")
    assert status["status"] == "BLANK_PACKETS_PREPARED_NOT_DISTRIBUTED"
    assert status["human_returns"] == 0 and not status["independent_researcher_validation"]
    assert not status["adjudication_completed"]
    expected_counts = {"families": 60, "results": 33, "fields": 66, "assertions": 4,
                       "central-facts": 15, "exclusion-queue": len(exclusion["rows"]),
                       "exclusion-metadata": 2629}
    assert status["item_counts_per_reviewer"] == expected_counts
    reviewer_ids = {}
    for kind, count in expected_counts.items():
        first = None
        for reviewer in ("reviewer-A", "reviewer-B"):
            packet = rows(HERE / "independent-review" / reviewer / (kind + "-BLANK.csv"))
            assert len(packet) == len({r["item_id"] for r in packet}) == count
            assert all(r[key] == "" for r in packet for key in status["answer_columns"])
            if kind in {"results", "fields"}:
                for record in packet:
                    identifier = record["item_id"].split("::")[0]
                    assert record["source_locator"] == blind_locator(identifier, unit[identifier]["scope"])
            if kind == "central-facts":
                for record in packet:
                    current = next(r for r in facts if r["case_fact_id"] == record["item_id"])
                    assert record["source_locator"] == blind_locator(record["item_id"], current["source_locator"])
            if kind == "exclusion-metadata":
                assert set(packet[0]) == set(status["answer_columns"]) | {
                    "item_id", "source_record_id", "title_variants", "doi", "source_locator",
                    "source_material_status", "original_export_material_gap", "review_question"}
                assert {r["item_id"] for r in packet} == {
                    prefix + str(i + 1).zfill(4) for prefix, count in (("E", 1555), ("F", 1074))
                    for i in range(count)}
                assert all(isinstance(json.loads(r["title_variants"]), list) and
                           isinstance(json.loads(r["doi"]), list) for r in packet)
                assert all(r["source_record_id"] for r in packet)
            if first is None:
                first = packet
            else:
                assert packet == first
        reviewer_ids[kind] = {r["item_id"] for r in first}
    assert reviewer_ids["families"] == set(family)
    assert reviewer_ids["results"] == set(unit)
    assert reviewer_ids["fields"] == {u + "::" + f for u, f in field_index}
    assert reviewer_ids["assertions"] == {r["assertion_id"] for r in assertions}
    assert reviewer_ids["central-facts"] == {r["case_fact_id"] for r in facts}
    projection = load(HERE / "revision/exclusion-metadata-projection.json")
    assert projection["cohort_memberships"] == {"old": 1555, "new": 1074}
    assert projection["memberships_not_deduplicated_publications"]
    assert not projection["abstracts_redistributed"] and not projection["new_semantic_screening"]
    adjudication = rows(HERE / "independent-review/adjudication-BLANK.csv")
    assert len(adjudication) == sum(expected_counts.values())
    assert {(r["item_kind"], r["item_id"]) for r in adjudication} == {
        (kind, identifier) for kind, identifiers in reviewer_ids.items() for identifier in identifiers}
    assert all(value == "" for row in adjudication for key, value in row.items()
               if key not in {"item_kind", "item_id"})
    assert load(HERE / "revision/path-scan.json")["hits"] == []
    for relative in files:
        if Path(relative).suffix.lower() in {".py", ".json", ".jsonl", ".txt", ".csv", ".md", ".tex", ".bib"}:
            text = inside(HERE, relative).read_text(encoding="utf-8-sig")
            # Construct the user-name token so the verifier does not flag its own pattern.
            assert not re.search(r"(?i)(?<![A-Z0-9])[A-Z]:[/\\]+(?:Users|2026)[/\\]|" +
                                 "Admin" + "istrator", text), relative

    # Only these own, inspected saved-data arithmetic verifiers are executed.
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        runpy.run_path(str(HERE / "h2-diagnostics/verify_saved.py"), run_name="__main__")
    h2 = json.loads(output.getvalue())
    workflow = saved_module("release004_workflow_saved", "workflow/verify.py").verify(HERE / "workflow/saved")
    prior = saved_module("release004_prior_saved", "prior_probability_verify.py").verify_probabilities(
        HERE / "prior-controls", bootstrap=False)
    # Recheck inventory/bytes after all read-only checks.
    assert actual == {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    assert all(sha(inside(HERE, relative)) == value for relative, value in files.items())
    print(json.dumps({"status": "LOCAL_RELEASE004_CHECKS_PASS", "manifest_files": len(files),
        "total_files": len(files) + 1, "families": 60, "core": 43, "adjacent": 17,
        "canonical_results": 33, "canonical_result_families": 22, "selected_results": 26,
        "fields": 66, "central_facts_separate_namespace": 15, "assertions": 4,
        "source_hash_proof_records": len(proofs), "active_source_files": len(active),
        "pdf_sha256": binding["pdf_sha256"], "blank_review_item_counts": expected_counts,
        "saved_h2": h2, "saved_workflow": workflow, "saved_prior_probability_points": prior,
        "fits": 0, "model_calls": 0, "network_requests": 0, "human_returns": 0,
        "scope": "Bytes, joins, recorded PDF/source binding and saved arithmetic only; "
                 "not independent scientific review, omitted-source revalidation, rights or anonymity certification."},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": repr(error)}, ensure_ascii=False), file=sys.stderr)
        raise
