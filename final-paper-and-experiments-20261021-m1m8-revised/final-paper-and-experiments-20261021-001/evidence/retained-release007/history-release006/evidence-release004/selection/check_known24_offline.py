"""Read-only exact-export and literal-field check. Prints JSON; writes nothing.

This is not a database search, native search-engine emulation, recall estimate,
or index-eligibility determination. Run with Python -B.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).absolute().parents[3]
SEEDS = "evidence/unified-2026-10-08/screening/known-item-query-audit.json"
IEEE = "evidence/systematic-2026-10-08-r2/native-screening/all-native-plus-q6.json"
ACM = "evidence/acm-screening-20261009-side-003/frame.json"
QUERY = "evidence/closure-2026-10-08/native/query-receipts.json"
Q6 = "evidence/systematic-2026-10-08-r2/native/query-receipt.json"


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def norm(s):
    return " ".join(unicodedata.normalize("NFKC", s or "").casefold().split())


def title(s):
    return "".join(c for c in norm(s) if c.isalnum())


def doi(s):
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "",
                  unquote(norm(s))).strip()


def exact(seed, titles, dois):
    sd = doi(seed.get("doi"))
    ds = [doi(d) for d in dois if d]
    if sd and sd in ds:
        return "EXACT_DOI"
    if title(seed["title"]) in {title(t) for t in titles}:
        return "TITLE_WITHOUT_DOI_CONFLICT" if not (sd and ds) else "TITLE_DIFFERENT_DOI_REVIEW"
    return None


def literal_coverage(text, expression):
    # All stored expressions consist solely of OR groups connected by AND.
    groups = []
    for clause in expression.split(" AND "):
        terms = [t.strip(' ()"') for t in clause.split(" OR ")]
        hits = [t for t in terms if re.search(r"(?<!\w)" + re.escape(norm(t)) + r"(?!\w)", norm(text))]
        groups.append(hits)
    return {"literal_groups_satisfied": all(groups), "matched_terms_by_AND_group": groups}


def main():
    seeds = read(SEEDS)["rows"]
    ieee = read(IEEE)
    acm = read(ACM)
    queries = {q["id"]: q["query"] for q in read(QUERY)["native_queries"]}
    queries["Q6"] = read(Q6)["query"]
    # IEEE unified records carry pointers to original title/abstract records.
    cache = {}
    rows = []
    differing = []
    for seed in seeds:
        seed_title_check = {q: literal_coverage(seed["title"], text)["literal_groups_satisfied"]
                            for q, text in queries.items()}
        for db in ("IEEE", "ACM"):
            matches = []
            for record in (ieee["records"] if db == "IEEE" else acm["rows"]):
                titles = [record["title"]] if db == "IEEE" else record["title_variants"]
                dois = [record["doi_normalized"]] if db == "IEEE" else record["doi"]
                basis = exact(seed, titles, dois)
                if basis == "TITLE_DIFFERENT_DOI_REVIEW":
                    differing.append({"seed": seed["citation_key"], "database": db,
                                      "record": record.get("record_id", record.get("group_id")),
                                      "dois": dois})
                    continue
                if not basis:
                    continue
                if db == "IEEE":
                    pointer = record.get("original_screen_pointer")
                    if pointer:
                        path, suffix = pointer.split("#/records/")
                        cache.setdefault(path, read(path))
                        original = cache[path]["records"][int(suffix)]
                    else:
                        pointer = IEEE + "#record_id=" + record["record_id"]
                        original = record
                    fields = {"title": original.get("title", record["title"]),
                              "abstract": original.get("abstract", "")}
                    evidence_pointer = pointer
                    query_ids = [record["query"]]
                    identity = record["record_id"]
                else:
                    fields = {"title": "\n".join(titles),
                              "abstract": "\n".join(record["abstract_variants"])}
                    evidence_pointer = ACM + "#group_id=" + record["group_id"]
                    query_ids = record["queries"]
                    identity = record["group_id"]
                joined = " ".join(fields.values())
                field_test = {q: literal_coverage(joined, queries[q]) for q in query_ids}
                matches.append({"record": identity, "basis": basis, "queries": query_ids,
                                "evidence_pointer": evidence_pointer,
                                "available_fields": [k for k, v in fields.items() if v],
                                "field_text_sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
                                "literal_field_tests": field_test})
            rows.append({
                "seed": seed["citation_key"], "database": db,
                "indexed_online": "NR_NOT_QUERIED",
                "export_presence": "PRESENT_EXACT_IDENTITY" if matches else "NOT_FOUND_IN_SAVED_FRAME",
                "strict_match_occurrences_or_groups": len(matches),
                "seed_title_literal_satisfied_queries": [q for q, v in seed_title_check.items() if v],
                "lexical_field_eligibility": (
                    "SUPPLIED_EXPORTED_TITLE_ABSTRACT_LITERAL_CHECK_ONLY" if matches
                    else "NR_FOR_DATABASE_FIELDS;SEED_TITLE_ONLY_CHECK_AVAILABLE"),
                "native_query_engine_eligibility": "NR;stemming/indexed_fields/tokenization_not_emulated",
                "matches": matches})
    result = {
        "schema": "known24-offline-export-field-audit/v1",
        "date": "2026-10-20", "seed_n": len(seeds),
        "source_frames": {IEEE: ieee["counts"]["distinct_publication_records"],
                          ACM: acm["metadata"]["candidate_publication_groups"]},
        "input_hashes": {p: sha(p) for p in (SEEDS, IEEE, ACM, QUERY, Q6)},
        "counts": {db: sum(r["database"] == db and r["export_presence"] == "PRESENT_EXACT_IDENTITY"
                          for r in rows) for db in ("IEEE", "ACM")},
        "same_title_different_explicit_doi": differing,
        "limitations": [
            "Presence is exact normalized DOI or exact normalized title without conflicting explicit DOI; no fuzzy family matching.",
            "Absence from a saved export does not establish absence from the database index.",
            "Seed title is an actually stored title, but not necessarily a database-indexed title. Missing seed abstracts are not invented.",
            "Literal term coverage does not emulate database stemming, tokenization, full-text or metadata field selection.",
            "IEEE Q4 historical membership was not fully exported. ACM export count discrepancies remain.",
            "No network, model call, new screening decision, independent human coding, or recall estimate."
        ],
        "rows": rows}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
