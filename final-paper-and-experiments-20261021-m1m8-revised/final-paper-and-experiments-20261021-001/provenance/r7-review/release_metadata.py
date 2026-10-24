"""Finalize current release metadata; preserve prior experimental records."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, shutil, sys
from pypdf import PdfReader

O = Path(__file__).resolve().parent
P = O.parents[1]
R = P.parents[1]
M = P / 'manuscript'
sys.path.insert(0, str(P))
from verify_package import closure

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')

def metadata():
    av = read(P / 'experiments/sp2027-r7-agent-extension/formal_validation.json')
    assert av['complete'] and av['runs'] == av['reward_recomputed_runs'] == 150
    for file, archive in [('artifact-index.json', 'prior-artifact-index.json'), ('provenance/snapshot.json', 'prior-snapshot.json')]:
        if not (O / archive).exists():
            shutil.copyfile(P / file, O / archive)
    idx = read(P / 'artifact-index.json')
    idx['purpose'] = 'Resolve current logical evidence modules to immutable historical archives and separately frozen R7 extensions.'
    additions = {
        'expanded_timing_and_wf_controls': ('sp2027-r7-robustness', ['README.md','PROTOCOL.md','freeze.json','results.json','common-suite.json','predictions.json','models.zip','validation.json','retraining_validation.json','dependency-closure.json','dependency-verification.json']),
        'expanded_customer_crossfit': ('sp2027-r7-crossfit', ['README.md','protocol.json','detailed_results.json','verification.json','dependency-closure.json','dependency-verification.json','verify.py']),
        'expanded_oracle_write_localization': ('sp2027-r7-localization', ['README.md','protocol.json','detailed_results.json','verification.json','dependency-closure.json','dependency-verification.json','verify.py']),
        'additional_luna_real_agent_study': ('sp2027-r7-agent-extension', ['README.md','formal_plan.json','APPENDED_ANALYSIS_FREEZE.json','formal_validation.json','formal_validation_corrected.json','compact_manifest.json','decision_alignment.json','public_decision_alignment.json','public_validation_corrected.json','public_network_validation.json','public_d2_validation.json','PACKAGING_AMENDMENT.json','raw-evidence-public.zip','PUBLIC_REDACTION.json','verify_public.py'])
    }
    for key, (directory, files) in additions.items():
        paths = ['experiments/' + directory + '/' + f for f in files]
        # Fail on an invented or stale entry rather than silently dropping it.
        for path in paths:
            assert (P / path).is_file(), path
        idx['modules'][key] = {'paths': paths}
    idx['modules']['source-ledger-and-family-audit']['paths'].extend([
        'provenance/r7-review/audit-corrections.json',
        'provenance/r7-review/nrv-current-summary.md'
    ])
    idx['modules']['source-ledger-and-family-audit']['paths'] = list(dict.fromkeys(idx['modules']['source-ledger-and-family-audit']['paths']))
    idx['historical_document_verifiers'] = [
        'provenance/review-closure/verify_manuscript.py',
        'provenance/timing/verify_publication.py'
    ]
    idx['current_verification'] = 'provenance/r7-review/verify_publication.py'
    idx['current_publication'] = [
        'manuscript/main.tex', 'manuscript/supplement.tex', 'pdf/main.pdf', 'pdf/supplement.pdf',
        'provenance/snapshot.json', 'SHA256SUMS.json',
        'provenance/r7-review/verify_publication.py', 'provenance/r7-review/validation.json',
        'provenance/r7-review/checklist-coverage.json', 'provenance/r7-review/visual_qa.json'
    ]
    save(P / 'artifact-index.json', idx)
    snapshot = read(P / 'provenance/snapshot.json')
    snapshot['updated_utc'] = datetime.now(timezone.utc).isoformat()
    snapshot['purpose'] = 'Current R7 manuscript and auditable results, with prior experimental data and version-specific receipts preserved.'
    snapshot['documents'] = {}
    hashes = {}
    counts = {}
    for name in ('main', 'supplement'):
        files = closure(M, name + '.tex')
        hashes.update({f: sha(M / f) for f in files})
        doc = PdfReader(P / 'pdf' / (name + '.pdf'))
        counts[name] = len(doc.pages)
        snapshot['documents'][name] = {'entry': name + '.tex', 'closure': files,
            'pdf': 'pdf/' + name + '.pdf', 'pdf_sha256': sha(P / 'pdf' / (name + '.pdf'))}
    snapshot['source_hashes'] = dict(sorted(hashes.items()))
    snapshot['current_manuscript'] = {
        'revision': 'R7 source audit, expanded D2 attacks, WF controls, cross-fitting, oracle localization and separate Luna study',
        'previous_manuscript_commit': 'ad7ec5f445f7d5f5ab010eee36b98e6e8ab6a7f9',
        'current_verification': 'provenance/r7-review/validation.json',
        'original_sol_runs': 690, 'additional_formal_luna_runs': 150,
        'pdf_pages': counts,
        'history_manifest': 'provenance/r7-review/prior-package-manifest.json'
    }
    save(P / 'provenance/snapshot.json', snapshot)
    dest = O / 'docs'
    dest.mkdir(exist_ok=True)
    for source in sorted((R / 'docs').glob('R7-*.md')):
        shutil.copyfile(source, dest / source.name)
    print('CURRENT_METADATA_AND_DOCUMENTATION_UPDATED')

def manifest():
    assert not (P / 'revision-preview').exists(), 'Move temporary environments outside publication package first'
    for raw in ('connectivity','pilot','formal'):
        assert not (P/'experiments/sp2027-r7-agent-extension'/raw).exists(), 'Preserve original Luna raw evidence outside publication package; publish only its reviewed public archive'
    for suffix in ('aux','blg','log','out','toc'):
        assert not list(M.glob('*.' + suffix)), 'Clean transient LaTeX files through build_pdfs --publish-copies'
    paths = []
    def walk(folder):
        for path in folder.iterdir():
            rel = path.relative_to(P).as_posix()
            if rel == 'experiments/sp2027-r4' or path.name == '__pycache__':
                continue
            assert not path.is_symlink(), path
            if path.is_dir():
                walk(path)
            elif rel != 'SHA256SUMS.json':
                assert path.stat().st_size < 100 * 1024**2, ('GitHub file limit', rel)
                paths.append(path)
    walk(P)
    paths.sort()
    with ThreadPoolExecutor(max_workers=10) as pool:
        files = {p.relative_to(P).as_posix(): h for p, h in zip(paths, pool.map(sha, paths))}
    save(P / 'SHA256SUMS.json', {'algorithm':'SHA-256', 'local_only_directories':['experiments/sp2027-r4'], 'files':files})
    print('CURRENT_MANIFEST_WRITTEN', len(files))

if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('--metadata','--manifest')
    metadata() if sys.argv[1] == '--metadata' else manifest()
