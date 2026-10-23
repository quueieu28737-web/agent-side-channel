"""Cache repeated reads of immutable verifier inputs; recheck each at exit.

No inference or analysis computation changes. This avoids thousands of redundant
filesystem reads when checking fingerprints on Windows/cloud-synced directories.
"""
from pathlib import Path
import common

original_sha=common.sha
digests={}

def cached_sha(path):
    path=Path(path).absolute()
    if path not in digests:digests[path]=original_sha(path)
    return digests[path]

def install():
    common.sha=cached_sha

def verify_unchanged():
    for path,digest in digests.items():
        assert original_sha(path)==digest,('Verifier input changed while running',str(path))
