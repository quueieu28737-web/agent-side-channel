"""Acquire only pinned upstream source files; preserve local originals."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "native_tau_dev"
COMMIT = "59a200c6d575d595120f1cb70fea53cef0632f6b"
BASE = f"https://raw.githubusercontent.com/sierra-research/tau-bench/{COMMIT}/"


def main():
    vendor = ROOT / "vendor"
    vendor.mkdir(exist_ok=True)
    records = []
    def acquire(name):
        dest = vendor / name.replace("/", "__")
        if dest.exists():
            return dest.read_bytes()
        original = OLD / "vendor" / name.replace("/", "__")
        if original.exists():
            raw = original.read_bytes()
            manifest = json.loads((OLD / "sources.json").read_bytes())
            expected = manifest["sha256"].get(original.name)
            if not expected or hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("Original pin failed: " + name)
            origin = "local pinned copy, commit verified against original manifest"
        else:
            with urllib.request.urlopen(BASE + name, timeout=30) as response:
                raw = response.read(8_000_000)
            origin = BASE + name
        dest.write_bytes(raw)
        records.append({"path": name, "origin": origin, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return raw
    init = acquire("tau_bench/envs/retail/tools/__init__.py").decode()
    for name in re.findall(r"from \.(\w+) import", init):
        acquire("tau_bench/envs/retail/tools/" + name + ".py")
    for path in ["LICENSE", "tau_bench/types.py", "tau_bench/envs/tool.py",
                 "tau_bench/envs/base.py", "tau_bench/envs/retail/tasks_test.py",
                 "tau_bench/envs/retail/wiki.md"]:
        acquire(path)
    for name in ["orders", "users", "products"]:
        acquire(f"tau_bench/envs/retail/data/{name}.json")
    files = [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size} for path in sorted(vendor.iterdir()) if path.is_file()]
    (ROOT / "sources.json").write_text(json.dumps({"repository": "https://github.com/sierra-research/tau-bench", "commit": COMMIT,
        "acquired_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "acquisitions": records, "files": files}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PINNED_SOURCES_ACQUIRED", "files": len(files)}))


if __name__ == "__main__":
    main()
