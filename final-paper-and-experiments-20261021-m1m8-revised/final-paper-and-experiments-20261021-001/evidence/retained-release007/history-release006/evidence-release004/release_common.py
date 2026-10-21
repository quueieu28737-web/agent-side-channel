"""Standard-library release structure checks. No network, fits or file writes."""
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def rows(path):
    return csv_rows(Path(path).read_bytes())


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))


def csv_bytes(records, names=None):
    if names is None:
        names = list(records[0]) if records else []
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=names, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue().encode("utf-8")


def inside(root, relative):
    rel = PurePosixPath(str(relative).replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or ":" in str(rel):
        raise ValueError("Unsafe relative path: " + str(relative))
    root = Path(root).resolve()
    target = root.joinpath(*rel.parts)
    if root not in target.resolve().parents or target.is_symlink():
        raise ValueError("Outside root or symlink: " + str(relative))
    return target


def active_tex_closure(root):
    found = set()

    def visit(name):
        if name in found:
            return
        found.add(name)
        text = inside(root, name).read_text(encoding="utf-8-sig")
        text = re.sub(r"(?<!\\)%[^\n]*", "", text)
        text = re.sub(r"\\iffalse\b.*?\\fi\b", "", text, flags=re.S)
        for relative in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", text):
            visit(relative if Path(relative).suffix else relative + ".tex")
        for bibliography in re.findall(r"\\bibliography\s*\{([^}]+)\}", text):
            for relative in bibliography.split(","):
                found.add(relative.strip() + ".bib")
        for graphic in re.findall(r"\\includegraphics(?:\[[^]]*\])?\s*\{([^}]+)\}", text):
            if Path(graphic).suffix:
                found.add(graphic)
            else:
                matches = [graphic + ext for ext in (".pdf", ".png", ".jpg", ".jpeg")
                           if inside(root, graphic + ext).is_file()]
                if len(matches) != 1:
                    raise ValueError("Unresolved graphic dependency: " + graphic)
                found.add(matches[0])

    visit("main.tex")
    for relative in found:
        if not inside(root, relative).is_file():
            raise FileNotFoundError(relative)
    return sorted(found)


def ids(value):
    if isinstance(value, list):
        return value
    return [v.strip() for v in re.split(r"[|;]", str(value or "")) if v.strip()]


def object_rows(value):
    if isinstance(value, list):
        return value
    for key in ("rows", "claims", "items"):
        if isinstance(value.get(key), list):
            return value[key]
    raise ValueError("No supported rows array")


def claim_locator(claim):
    if claim.get("manuscript_locator"):
        return claim["manuscript_locator"]
    return " | ".join(r["path"] + " :: " + r.get("semantic_anchor", "")
                      for r in claim.get("manuscript_anchors", []))


def field_link(row):
    claim_ids = row.get("claim_id", row.get("current_claim_ids", ""))
    role = row.get("support_role", row.get("current_role", ""))
    if not claim_ids and role == "BACKGROUND_ONLY":
        claim_ids = "BACKGROUND_ONLY"
    return {"unit_id": row.get("unit_id", row.get("canonical_unit_id")),
            "field": row["field"], "claim_id": claim_ids, "support_role": role}


def fact_link(row):
    relation = row.get("relation_kind", row.get("binding_relation", "")).lower()
    if relation == "source_mechanism_context":
        relation = "source_mechanism_fact"
    return {**row, "canonical_unit_id": row.get("canonical_unit_id", ""),
            "related_canonical_unit_id": row.get("related_canonical_unit_id", row.get("related_unit_id", "")),
            "relation_kind": relation,
            "subcondition_label": row.get("subcondition_label", row.get("condition_boundary", "")),
            "source_locator": row.get("source_locator", row.get("current_source_locator", ""))}


def exclusion_index(value):
    """Normalize coordinator metadata only; never synthesize individual records."""
    if "rows" in value and "source_bindings" in value:
        return value
    bindings = {r["path"]: r["sha256"] for r in value["sources"].values()}
    for record in value.get("old_readback_sources", []):
        assert record["path"] not in bindings or bindings[record["path"]] == record["sha256"]
        bindings[record["path"]] = record["sha256"]
    records = []
    for cohort in value["cohorts"]:
        membership = cohort["membership"]
        material = cohort["material_projection"]
        records.append({"queue_id": cohort["id"],
            "source_locator": value["sources"][membership["source"]]["path"] + "#" + membership["pointer"] +
                " ; material: " + value["sources"][material["source"]]["path"],
            "scope": "Source-bound cohort with " + str(membership["expected_unique_ids"]) +
                " memberships. Metadata-only queue scope; individual source materials are not bundled. "
                "Obtain actual material before coding; preserve missing/partial material. "
                "Cohorts may overlap and are not a summed unique-publication denominator."})
    return {"scope": value["scope"], "rows": records, "source_bindings": bindings,
            "packet_granularity": "cohort_metadata_only_not_individual_completed_records"}


def blind_locator(identifier, locator):
    if identifier in {"DANGOL-livebinding", "FACT:DANGOL-live-cover"}:
        return "Section 9.7, OHTTP paragraph after Table 5"
    return locator


def case_id(row):
    return row.get("case_fact_id") or row.get("result_id") or row.get("fact_id")


def source_version(url, fallback=""):
    match = re.search(r"(?:abs/|html/|pdf/)(\d{4}\.\d+(?:v\d+)?)", url or "")
    return match.group(1) if match else fallback or "Version bound by source SHA256 and locator"


def canonical_checks(families, units, fields, subset):
    family = {r["citation_key"]: r for r in families}
    unit = {r["unit_id"]: r for r in units}
    assert len(families) == len(family) == 60
    assert sum(r["classification"] == "core" for r in families) == 43
    assert sum(r["classification"] == "adjacent" for r in families) == 17
    assert len(units) == len(unit) == 33
    assert len({r["citation_key"] for r in units}) == 22
    assert all(r["citation_key"] in family for r in units), "Orphan result family"
    assert len(fields) == len({(r["unit_id"], r["field"]) for r in fields}) == 66
    assert {r["unit_id"] for r in fields} == set(unit)
    assert all(r["citation_key"] == unit[r["unit_id"]]["citation_key"] for r in fields)
    assert len(subset) == len({r["unit_id"] for r in subset}) == 26
    assert {r["unit_id"] for r in subset} <= set(unit)
    return family, unit
