"""Refresh package provenance after the R5 manuscript build (no experimental reruns).

Updates provenance/snapshot.json (TeX closures, PDF hashes, source hashes and a
fifth_round block) and regenerates SHA256SUMS.json with the same membership
rules that verify_package.py enforces. Run from anywhere after building PDFs.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = importlib.util.spec_from_file_location('verify_package', ROOT / 'verify_package.py')
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    snap_p = ROOT / 'provenance/snapshot.json'
    snap = json.loads(snap_p.read_text(encoding='utf-8'))
    names = set()
    for name, doc in snap['documents'].items():
        doc['closure'] = vp.closure(ROOT / 'manuscript', doc['entry'])
        doc['pdf_sha256'] = digest(ROOT / doc['pdf'])
        names.update(doc['closure'])
    snap['source_hashes'] = {n: digest(ROOT / 'manuscript' / n) for n in sorted(names | set(snap['source_hashes']))
                             if (ROOT / 'manuscript' / n).is_file()}
    receipt = json.loads((HERE / 'validation_r5.json').read_text(encoding='utf-8'))
    snap['fifth_round'] = {'directory': 'experiments/sp2027-r5-crossfit',
                           'scope': 'Offline reanalysis of the immutable R4 snapshot: cross-fitting (E10), '
                                    'training-only operating-point selection (E11), leakage localization (E12). No model calls.',
                           'validation_status': receipt['status'],
                           'outputs': receipt['output_hashes']}
    snap_p.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    sums_p = ROOT / 'SHA256SUMS.json'
    sums = json.loads(sums_p.read_text(encoding='utf-8-sig'))
    local_only = sums.get('local_only_directories', [])
    files = {}
    def walk(folder):
        for p in sorted(folder.iterdir()):
            rel = p.relative_to(ROOT).as_posix()
            if rel in local_only or p.name == '__pycache__':
                continue
            if p.is_dir():
                walk(p)
            elif rel != 'SHA256SUMS.json':
                files[rel] = digest(p)
    walk(ROOT)
    sums['files'] = files
    sums_p.write_text(json.dumps(sums, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print('manifest files', len(files))


if __name__ == '__main__':
    main()
