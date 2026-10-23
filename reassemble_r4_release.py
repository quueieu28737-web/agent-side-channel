"""Reassemble the complete R4 ZIP from checksum-verified GitHub-sized parts."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parent
index=json.loads((ROOT/'paper-review-revised-20261023.parts.json').read_text(encoding='utf-8'))
target=ROOT/index['archive']
if target.exists():
    assert hashlib.sha256(target.read_bytes()).hexdigest()==index['sha256'],'Existing target differs; preserve it before rebuilding'
else:
    with target.open('xb') as out:
        for part in index['parts']:
            content=(ROOT/part['file']).read_bytes()
            assert len(content)==part['bytes'] and hashlib.sha256(content).hexdigest()==part['sha256'],part['file']
            out.write(content)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==index['sha256']
print('REASSEMBLED_AND_VERIFIED',target)
