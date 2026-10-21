"""B2: anonymity scan and anonymous release archive for the artifact package.

The script never uploads anything. It (1) scans every text file and PDF metadata in
the package for identifying strings, (2) writes a report, and (3) if the scan has no
unresolved hits, writes a deterministic zip (sorted entries, fixed timestamps,
without VCS metadata or caches) plus its SHA-256 for an anonymous host such as
anonymous.4open.science or a Zenodo draft. The upload is a manual author step.

  python -B anonymize_package.py --names "First Last" "handle" --out /tmp/release
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

PKG = Path(__file__).resolve().parents[3]
DEFAULT_PATTERNS = {
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    "home_path": r"(/Users/[^/\s]+|/home/[^/\s]+|[A-Za-z]:\\\\Users\\\\[^\\\s]+)",
    "github_user_url": r"github\.com/[A-Za-z0-9-]+",
}
# Synthetic benchmark identities and public bibliographic material are not author identities.
ALLOW_EMAIL_DOMAINS = {"example.com"}
ALLOW_FILES = re.compile(r"(\.bib$|\.bbl$|tau_bench__envs__retail__data__|/vendor/|\.blg$|release/anonymize_package\.py$|search/frame2_)")
# Code repositories of the *studied* papers are cited evidence, not author identities.
CITED_REPO_DIRS = ("evidence/",)
CITED_REPO_OWNERS = {"sierra-research", "dangoldbj"}  # tau-bench; Dangol's cited artifact
SKIP_DIRS = {".git", "__pycache__", "runs", "llm_cache"}
TEXT_EXT = {".py", ".md", ".txt", ".tex", ".json", ".jsonl", ".csv", ".log", ".bib", ".bbl", ".blg", ".patch", ".html", ".raw"}


def files():
    for p in sorted(PKG.rglob("*")):
        if p.is_file() and not (set(p.relative_to(PKG).parts) & SKIP_DIRS):
            yield p


def scan(names):
    pats = dict(DEFAULT_PATTERNS)
    for n in names:
        pats[f"name:{n}"] = re.escape(n)
    hits = []
    for p in files():
        rel = p.relative_to(PKG).as_posix()
        if p.suffix == ".pdf":
            raw = p.read_bytes()
            for key in (b"/Author", b"/Creator"):
                for m in re.finditer(re.escape(key) + rb"\s*\(([^)]*)\)", raw):
                    v = m.group(1).decode("latin-1")
                    if v and key == b"/Author":
                        hits.append({"file": rel, "kind": "pdf_author", "match": v})
            for n in names:
                if n.encode() in raw:
                    hits.append({"file": rel, "kind": f"pdf_bytes:{n}", "match": n})
            continue
        if p.suffix not in TEXT_EXT or p.stat().st_size > 20_000_000:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for kind, pat in pats.items():
            for m in re.finditer(pat, text, flags=re.I if kind.startswith("name:") else 0):
                s = m.group(0)
                if kind == "email" and s.split("@")[-1].lower() in ALLOW_EMAIL_DOMAINS:
                    continue
                if not kind.startswith("name:") and ALLOW_FILES.search(rel):
                    continue
                if kind == "github_user_url" and (rel.startswith(CITED_REPO_DIRS) or s.split("/")[-1] in CITED_REPO_OWNERS):
                    continue
                line = text.count("\n", 0, m.start()) + 1
                hits.append({"file": rel, "line": line, "kind": kind, "match": s})
    return hits


def build_zip(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    z = out / "artifact-anonymous.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files():
            info = zipfile.ZipInfo("artifact/" + p.relative_to(PKG).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, p.read_bytes())
    h = hashlib.sha256(z.read_bytes()).hexdigest()
    (out / "artifact-anonymous.zip.sha256").write_text(f"{h}  artifact-anonymous.zip\n")
    return z, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", nargs="*", default=[], help="author names, handles and affiliations to search for")
    ap.add_argument("--out", default="/tmp/anonymous-release")
    ap.add_argument("--force", action="store_true", help="write the zip even with hits (not for submission)")
    a = ap.parse_args()
    hits = scan(a.names)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "anonymity_report.json").write_text(json.dumps({"names_checked": a.names, "hits": hits}, indent=1))
    by = {}
    for h in hits:
        by.setdefault(h["kind"], set()).add(h["file"])
    print(f"{len(hits)} hits in {len({h['file'] for h in hits})} files")
    for k, v in sorted(by.items()):
        print(f"  {k}: {len(v)} files, e.g. {sorted(v)[:3]}")
    if hits and not a.force:
        print("resolve or allow-list every hit before building the release; report:", out / "anonymity_report.json")
        return 1
    z, h = build_zip(out)
    print("wrote", z, h)


if __name__ == "__main__":
    raise SystemExit(main())
