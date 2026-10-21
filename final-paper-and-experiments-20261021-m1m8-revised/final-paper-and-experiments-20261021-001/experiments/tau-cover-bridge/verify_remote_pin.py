"""Cross-check the three copied data tables against their immutable upstream pin."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
COMMIT = "59a200c6d575d595120f1cb70fea53cef0632f6b"


def main():
    rows = []
    for name in ["orders", "products", "users"]:
        relative = f"tau_bench/envs/retail/data/{name}.json"
        url = f"https://raw.githubusercontent.com/sierra-research/tau-bench/{COMMIT}/{relative}"
        local = (ROOT / "vendor" / relative.replace("/", "__")).read_bytes()
        row = {"file": relative, "url": url, "local_sha256": hashlib.sha256(local).hexdigest()}
        try:
            with urllib.request.urlopen(url, timeout=25) as response:
                remote = response.read(8_000_000)
            row["remote_sha256"] = hashlib.sha256(remote).hexdigest()
            row["status"] = "MATCH" if remote == local else "MISMATCH"
        except Exception as exc:
            row.update(status="UNRESOLVED", error=type(exc).__name__ + ": " + str(exc))
        rows.append(row)
    (ROOT / "remote-data-pin-check.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    if any(row["status"] != "MATCH" for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
