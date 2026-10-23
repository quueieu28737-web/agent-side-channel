"""Check this revision against frozen data, generated tables and rendered PDFs.

Requires pypdf. No model calls, fitting or edits unless --save is supplied.
Reproduce the extra paired contrasts separately with analyze_paired.py.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import subprocess
import sys
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
M = P / 'manuscript'
F = P / 'experiments/sp2027-r4-full-20261023'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    for script in ('build_sok_tables.py', 'build_e9_tables.py', 'build_null_table.py', 'verify_r5_tables.py'):
        subprocess.run([sys.executable, '-B', str(HERE / script), '--check'], check=True)
    prior = read(HERE / 'prior-package-manifest.json')['files']
    kept = [n for n in prior if n.startswith(('evidence/', 'experiments/', 'provenance/main-690/'))
            or n.endswith('.bib') or n == 'pdf/full-cohort-supplement.pdf']
    with ThreadPoolExecutor(max_workers=12) as pool:
        for name, value in zip(kept, pool.map(lambda n: sha(P / n), kept)):
            assert value == prior[name], ('Preserved file changed', name)
    full = read(F / 'validation.json')
    assert full['status'] == 'VERIFIED' and full['episodes'] == 690
    assert read(F / 'extension_validation.json')['status'] == 'FULL_COHORT_EXTENSION_VERIFIED'
    assert read(F / 'reproduction_validation.json')['status'] == 'FROZEN_FULL_VERIFIER_REPRODUCED'
    upstream = read(HERE / 'upstream-r5.json')
    for name, value in upstream['files'].items():
        assert sha(P / name) == value, ('Upstream R5 data changed', name)
    renewed = read(HERE / 'r5-reverification.json')
    assert renewed == read(P / 'experiments/sp2027-r5-crossfit/validation_r5.json')
    assert renewed['fresh_socket_captures_match_model'] == 120
    null = read(HERE / 'conditional_null_results.json')
    assert null['status'] == 'CONDITIONAL_TASK_PERMUTATION_REFERENCE_PASS'
    assert len(null['cells']) == 32 and null['permutations'] == 2000
    assert null['source_predictions_sha256'] == sha(F / 'predictions.json')
    paired = read(HERE / 'paired_program_results.json')
    assert paired['status'] == 'PAIRED_PROGRAM_CONTRAST_AND_PROJECTION_CHECK_PASS'
    assert paired['projection_check']['episodes'] == 690
    assert paired['projection_check']['sessions'] == 2760
    for name, value in paired['inputs'].items():
        assert sha(F / name) == value
    assert sha(P / 'experiments/sp2027-r3/reanalyze.py') == paired['frozen_statistics_sha256']
    assert sha(P / 'experiments/sp2027-r4-snapshot-20261023/pretest-source/defense.py') == paired['frozen_dispatcher_sha256']
    expected = {('baseline', 'cancel'): [-47.2, -50.0, -33.3],
                ('baseline', 'return'): [-44.0, -48.9, -27.8],
                ('rules', 'cancel'): [-47.2, -50.0, -26.0],
                ('rules', 'return'): [-33.0, -44.3, -18.9]}
    for row in paired['contrasts']:
        assert [round(100 * x, 1) for x in [row['difference'], *row['ci95']]] == expected[row['prompt'], row['target']]
        assert row['valid_bootstrap_draws'] == (1994 if row['target'] == 'cancel' else 2000)
    tables = read(HERE / 'table_sources.json')
    assert len(tables['families']) == 58 and len(tables['audit_rows']) == 180
    keys = {r['citation_key'] for r in tables['families']}
    map_tex = (M / 'tables/core-family-map.tex').read_text()
    assert set(re.findall(r'\\cite\{([^}]+)\}', map_tex)) == keys
    assert len(re.findall(r'\\cite\{', map_tex)) == 58
    assert len(re.findall(r'\\cite\{', (M / 'tables/family-audit-matrix.tex').read_text())) == 20
    main_tex = (M / 'main.tex').read_text()
    assert main_tex.index(r'\bibliography{') < main_tex.index(r'\appendices')
    assert 'tables/corpus-citations' not in main_tex
    assert 'tables/scenario-confusions' not in (M / 'sections/04-scope.tex').read_text()
    assert 'tables/scenario-confusions' in (M / 'sections/29-scope-comparison-boundary.tex').read_text()
    assert 'tables/search-reconciliation' in (M / 'supplement.tex').read_text()
    appendix = (M / 'sections/30-reproducibility-guide.tex').read_text()
    for old in ('experiments/', 'revision-m1-m8', 'sp2027-r2', 'sp2027-r3', 'r4-snapshot'):
        assert old not in appendix
    e9 = (M / 'sections/37-transfer-tests.tex').read_text().split(r'\subsection{E9:')[1]
    for token in ('690', '414', '276', '24', '2,760', '110/138', '105/138',
                  r'97.2\%', r'94.0\%', r'97.1\%', r'86.2\%', r'50.0\%',
                  r'60.6\%', r'65.5\%', '47.2', '44.0', '33.3', '48.9', '27.8',
                  'Post hoc', 'prefix-only', 'five', 'seven', 'Planner-visible equivalence'):
        assert token in e9, token
    index = read(P / 'artifact-index.json')
    paths = [n for module in index['modules'].values() for n in module['paths']]
    paths += index['current_publication']
    for name in paths:
        parts = PurePosixPath(name)
        assert not parts.is_absolute() and '..' not in parts.parts and ':' not in name
        # The verifier's own receipt is created on the first --save invocation.
        if name == 'provenance/sok-restructure/validation.json' and '--save' in sys.argv:
            continue
        assert (P / name).is_file(), name
    pages = {}
    hashes = {}
    for name in ('main', 'supplement'):
        pdf = P / 'pdf' / (name + '.pdf')
        data = pdf.read_bytes()
        assert data == (M / (name + '.pdf')).read_bytes()
        # Repository root copies are optional for a package-only extraction.
        root_pdf = P.parents[1] / (name + '.pdf')
        if (P.parents[1] / '.git').exists():
            assert data == root_pdf.read_bytes()
        doc = PdfReader(pdf)
        pages[name] = len(doc.pages)
        hashes[name] = sha(pdf)
        for page in doc.pages:
            assert abs(float(page.mediabox.width) - 612) < 1
            assert abs(float(page.mediabox.height) - 792) < 1
        texts = [p.extract_text() for p in doc.pages]
        searchable = (str(doc.metadata) + '\n'.join(texts)).lower()
        for identity in ('quueieu28737', 'administrator', 'c:/users/', 'c:\\users\\', '@gmail.com'):
            assert identity not in searchable, ('Local identity string in PDF', name, identity)
        if name == 'main':
            refs = next(i + 1 for i, t in enumerate(texts) if re.search(r'(?m)^References\s*$', t))
            app = next(i + 1 for i, t in enumerate(texts) if 'Appendix A.' in t)
            assert refs <= 13 and app > refs and len(doc.pages) <= 18
            assert '10. Conclusion' in texts[refs - 1]
            assert '690' in texts[0] and '97.2%' in texts[0] and '94.0%' in texts[0]
            pages.update(main_body=refs, references_start=refs, appendix_start=app)
        else:
            start = next(i for i, t in enumerate(texts) if 'S14. Complete Real-Agent' in t)
            assert 'All 690 episodes' in texts[start]
            pages['supplement_s14_first_page'] = start + 1
        for folder in ('provenance/build-logs', 'pdf/build-logs'):
            log = (P / folder / (name + '.log')).read_text(errors='replace')
            for bad in ('undefined references', 'undefined on input line', 'multiply defined', 'Overfull', 'Float too large'):
                assert bad not in log, (name, bad)
    assert pages['main'] == 16 and pages['supplement'] == 27
    visual = read(HERE / 'visual_qa.json')
    assert visual['status'] == 'RENDERED_PAGES_INSPECTED'
    assert visual['pdf_sha256'] == hashes
    receipt = {
        'status': 'SOK_STRUCTURE_TABLES_PAIRED_STATISTICS_AND_PDF_PASS',
        'base_commit': 'f0fb3d229a9d76debf20a45bb6d0e503aa1980c7',
        'source_results_sha256': sha(F / 'results.json'),
        'original_validation_sha256': sha(F / 'validation.json'),
        'prior_verified_reproduction_sha256': sha(F / 'reproduction_validation.json'),
        'paired_program_analysis_sha256': sha(HERE / 'paired_program_results.json'),
        'merged_upstream_commit': upstream['remote_commit'],
        'upstream_r5_files_preserved': len(upstream['files']),
        'upstream_r5_reverification_sha256': sha(HERE / 'r5-reverification.json'),
        'conditional_reference_cells': 32,
        'pdf_known_local_identity_scan': 'No configured local identity strings in extracted text or PDF metadata; this is not an audit of public repository history.',
        'preserved_data_bibliography_and_previous_provenance_files': len(kept),
        'core_families': 58, 'audit_families': 20, 'audit_cells': 180,
        'resolved_artifact_paths': len(paths),
        'cohort': {'training': 414, 'test': 276, 'total': 690},
        'pdf_pages': pages, 'pdf_sha256': hashes, 'new_model_calls': 0,
        'scope': 'Revised presentation and post hoc paired contrasts of previously verified data. Original absolute criterion, predictions and frozen experimental bytes unchanged.'
    }
    if '--save' in sys.argv:
        (HERE / 'validation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
