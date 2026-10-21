"""Explicit original-byte versus released-byte bindings for anonymous copies."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def actual_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def projections():
    return json.loads((ROOT / "controlled-study/projections.json").read_text(encoding="utf-8"))


def origin_digest(path):
    """Check released bytes, then return the separately recorded origin hash.

    This deliberately does not call the original bytes identical when a path
    projection was made. The builder checked originals locally; the top-level
    manifest binds the projection table and the released files.
    """
    path = Path(path).resolve()
    relative = path.relative_to(ROOT).as_posix()
    entry = projections()["files"].get(relative)
    current = actual_sha(path)
    if entry is None:
        return current
    if current != entry["released_sha256"]:
        raise AssertionError("Released-byte mismatch: " + relative)
    return entry["original_sha256"]


def check_frozen_source_hashes(freeze):
    mapping = projections()["frozen_source_paths"]
    checks = {}
    for original_path, expected in freeze["sources_sha256"].items():
        relative = mapping[original_path]
        entry = projections()["files"][relative]
        checks[original_path] = (actual_sha(ROOT / relative) == entry["released_sha256"] and
                                 entry["original_sha256"] == expected)
    if not all(checks.values()):
        raise AssertionError("Frozen source projection mismatch")
    return checks
