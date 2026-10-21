"""Refresh provenance/snapshot.json and SHA256SUMS.json after a manuscript rebuild.

Run from anywhere after copying the rebuilt PDFs into pdf/ and manuscript/ and the
build logs into pdf/build-logs/ and provenance/build-logs/. The closure walk is the
one used by verify_package.py, so the verifier and this script cannot disagree.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import verify_package as vp  # noqa: E402


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    snap_p = ROOT / "provenance/snapshot.json"
    snap = json.loads(snap_p.read_text(encoding="utf-8"))
    files = set()
    for name, doc in snap["documents"].items():
        doc["closure"] = vp.closure(ROOT / "manuscript", doc["entry"])
        doc["pdf_sha256"] = digest(ROOT / doc["pdf"])
        files |= set(doc["closure"])
    snap["source_hashes"] = {f: digest(ROOT / "manuscript" / f) for f in sorted(files)}
    snap["second_round"] = {
        "directory": "experiments/sp2027-r2",
        "preregistration_commit": "16f6254",
        "experiments": ["E5 streaming emitter", "E6 randomized cover", "E7 agent-tool TLS link"],
        "model_calls": 0, "production_services": 0,
    }
    snap_p.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    skip = {"SHA256SUMS.json"}
    entries = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(ROOT.rglob("*"))
               if p.is_file() and p.relative_to(ROOT).as_posix() not in skip
               and "__pycache__" not in p.parts}
    (ROOT / "SHA256SUMS.json").write_text(json.dumps({"algorithm": "SHA-256", "files": entries}, indent=2), encoding="utf-8")
    print("snapshot and manifest refreshed:", len(entries), "files")


if __name__ == "__main__":
    main()
