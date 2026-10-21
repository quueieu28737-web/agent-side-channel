"""Read-only allowlist projection for the coordinator's source-bound queue.

Prints reviewer-safe title/abstract material with blank A/B fields. No original
classification, reason, risk stratum or AI return is emitted. Does not write files.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
QUEUE = ROOT / "evidence/reviewer-deployment-cases-20261020-001/claims/exclusion-review-queue.json"


def checked(source, lines=False):
    data = (ROOT / source["path"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise ValueError("Source hash mismatch: " + source["path"])
    text = data.decode("utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip()] if lines else json.loads(text)


def strings(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [x for x in value if isinstance(x, str) and x.strip()]


def material(record, cohort, position):
    blank = {k: None for k in ("C1", "C2", "C3", "C4", "C5", "route",
                               "source_locator", "reason", "material_needed")}
    abstracts = strings(record.get("abstract_variants")) or strings(record.get("abstract"))
    return {
        "blind_id": ("E" if cohort == "old" else "F") + str(position + 1).zfill(4),
        "source_record_id": record.get("group_id", record.get("id")),
        "title_variants": strings(record.get("title_variants")) or strings(record.get("title")),
        "doi": strings(record.get("dois")) or strings(record.get("doi")),
        "abstract_variants": abstracts,
        "material_scope": "Supplied exported title/abstract only; not full text or independently verified abstract completeness",
        "material_gap": "MISSING_OR_PARTIAL" if record.get("abstract_status") == "MISSING_OR_PARTIAL" or not abstracts else "NO_EMPTY_FIELD_DETECTED;COMPLETENESS_UNVERIFIED",
        "researcher_A": dict(blank),
        "researcher_B": dict(blank)
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("old", "new"), required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.offset < 0 or (args.limit is not None and args.limit < 0):
        raise ValueError("Negative slice")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    if args.cohort == "old":
        rows = checked(queue["sources"]["old_frame"])["rows"]
        expected = 1555
    else:
        ids = checked(queue["sources"]["new_sample"])["high_risk_ids"]
        frame = checked(queue["sources"]["new_public_metadata"], lines=True)
        lookup = {r["id"]: r for r in frame}
        if len(lookup) != len(frame) or len(ids) != len(set(ids)):
            raise ValueError("Duplicate source identities")
        rows = [lookup[x] for x in ids]
        expected = 1074
    if len(rows) != expected:
        raise ValueError("Unexpected cohort membership count")
    projected = [material(r, args.cohort, i) for i, r in enumerate(rows)]
    allowed = set(queue["blind_export_contract"]["fields"])
    if any(set(row) != allowed for row in projected):
        raise ValueError("Unsafe output fields")
    if args.check_only:
        print(json.dumps({"cohort": args.cohort, "rows": len(projected),
                          "allowlist_fields_only": True,
                          "human_filled_responses": 0,
                          "missing_or_partial_material": sum(r["material_gap"] == "MISSING_OR_PARTIAL" for r in projected),
                          "writes": 0, "network_calls": 0}))
    else:
        end = None if args.limit is None else args.offset + args.limit
        print(json.dumps({"schema": "blank-human-exclusion-review-packet/v1",
                          "human_review_status": "PENDING",
                          "records": projected[args.offset:end]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
