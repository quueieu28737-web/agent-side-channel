"""Verify R9 publication and provenance. Read-only unless --save is explicit."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, re, sys, zipfile
from pypdf import PdfReader

O = Path(__file__).resolve().parent
P = O.parents[1]
R = P.parents[1]
M = P / 'manuscript'
sys.path.insert(0, str(P))
from verify_package import closure

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def txt(p):
    return p.read_text(encoding='utf-8-sig')

checks = {}
def require(name, condition, detail=True):
    if not condition:
        raise AssertionError(name)
    checks[name] = detail

# The original experiment/evidence/earlier provenance bytes remain immutable.
prior = read(O / 'prior-release/SHA256SUMS.json')['files']
old = {k: v for k, v in prior.items() if k.startswith(('experiments/', 'evidence/', 'provenance/')) and k != 'provenance/snapshot.json'}
receipt = read(O / 'prior-release.json')
for rel, expected in receipt['files'].items():
    f = O / ('prior-manuscript/' + rel[len('manuscript/'):] if rel.startswith('manuscript/') else 'prior-release/' + rel)
    require('retained_' + rel, sha(f) == expected)

# Current source closure and final PDF geometry.
snap = read(P / 'provenance/snapshot.json')
for rel, expected in snap['source_hashes'].items():
    require('current_source_' + rel, sha(M / rel) == expected)
pages = {}
texts = {}
for name, expected_pages in [('main', 18), ('supplement', 52)]:
    f = P / 'pdf' / (name + '.pdf')
    d = PdfReader(f)
    pages[name] = len(d.pages)
    texts[name] = [p.extract_text() or '' for p in d.pages]
    require(name + '_pages', len(d.pages) == expected_pages, len(d.pages))
    require(name + '_letter', all(abs(float(p.mediabox.width)-612)<.1 and abs(float(p.mediabox.height)-792)<.1 for p in d.pages))
    require(name + '_published_copies', sha(f) == sha(M / (name+'.pdf')) == sha(R / (name+'.pdf')) == snap['documents'][name]['pdf_sha256'])
    log = txt(P / 'pdf/build-logs' / (name+'.log'))
    require(name + '_compiler_diagnostics', not re.search(r'Overfull|undefined|multiply defined|Float too large|^! ', log, re.M|re.I))
refpage = next(i+1 for i,t in enumerate(texts['main']) if re.search(r'^References\s*$',t,re.M))
apppage = next(i+1 for i,t in enumerate(texts['main']) if re.search(r'Appendix A\.',t))
require('body_and_appendix_order', refpage <= 13 and apppage > refpage, {'references_start':refpage,'appendix_start':apppage})
require('no_scientific_floats_after_references', not any(re.search(r'TABLE\s+(?:[1-9]|1[0-8])\.', t) for t in texts['main'][refpage:]))
main = txt(M/'main.tex')
require('standard_IEEEtran', r'\documentclass[conference,compsoc]{IEEEtran}' in main and not re.search(r'\\(?:geometry|IEEEaftertitletext|textheight|topmargin)',main))

def expand(s):
    return re.sub(r'\\input\{([^}]+)\}', lambda m: expand(txt(M / (m[1]+'.tex'))), s)
body = expand(main.split(r'\bibliographystyle')[0])
require('no_external_S_or_legacy_E_refs_in_body', not re.search(r'(?<!\\)\b[SE][1-9][0-9]*\b',body))
require('four_experimental_modules', len(re.findall(r'\\subsection\{Exp [1-4]:',body)) == 4)
rules = txt(M/'tables/r9-audit-rules.tex')
require('nine_operational_rules', all('R'+str(i)+' ' in rules for i in range(1,10)))
require('shared_status_macros', all(x in main for x in [r'\newcommand{\NRR}{\textsf{U}}',r'\newcommand{\NRA}{\textsf{A}}',r'\newcommand{\NRV}{\textsf{?}}']))

corpus = read(O/'corpus-insights.json')
mapping = txt(M/'tables/core-family-map.tex')
rows = re.findall(r'\\cite\{([^}]+)\}\s*&\s*\$([0-9,]+)\\,\\to\\,([0-9,]+)\$\s*&\s*\\texttt\{([IV,]+)\}',mapping)
require('core_map_58_unique_families', len(rows)==58 and len({r[0] for r in rows})==58)
expected = {d['citation_key']:(d['generation_layers'], d['observation_layers'], d['types']) for d in corpus['families']}
require('core_map_values_preserved', all(([int(x) for x in g.split(',')],[int(x) for x in o.split(',')],t.split(','))==expected[k] for k,g,o,t in rows))
require('two_29_row_panels', [len(re.findall(r'\\cite\{',part)) for part in mapping.split(r'\begin{minipage}')[1:]]==[29,29])
require('no_accidental_blank_table_rows', not re.search(r'\\{4}\s*$',mapping,re.M))
def audit_rows(s):
    return [line.strip() for line in s.splitlines() if r'\cite{' in line and '&' in line]
old_matrix = audit_rows(txt(O/'prior-manuscript/tables/family-audit-matrix.tex'))
new_matrix = audit_rows(txt(M/'tables/family-audit-matrix.tex'))
require('180_audit_cells_preserved', len(new_matrix)==20 and new_matrix==old_matrix)

record = read(O/'record-index-source-validation.json')
require('result_ledger_source', sha(P/record['source']) == record['source_sha256'])
idx = txt(M/'tables/r9-record-index.tex').replace(r'\allowbreak{}', '')
require('all_39_record_ids', record['records']==39 and record['families']==26 and all(x['record_id'] in idx and ('\\cite{'+x['family']+'}') in idx for x in record['records_detail']))
require('all_39_record_locators', all(x['printed_locator'] in idx for x in record['records_detail']))
experiment_index = txt(M/'sections/50-r9-experiment-index.tex')
require('artifact_index_complete', all(re.search(r'\bE'+str(i)+r'\b',experiment_index) for i in [1,2,3,5,6,7,8,9,10,11,12,13,14,15,16]) and not re.search(r'\bE4\b',experiment_index) and 'S23.8' in experiment_index)
num = read(O/'condensed-numerical-audit.json')
require('scientific_numbers_preserved', num['status']=='PASS_NUMBERS_AND_RESOLVED_NOTES' and (num['checked_scientific_table_pairs'],num['numerical_rows'],num['numerical_tokens'])==(8,51,346))
for t in num['tables']:
    require('numerical_table_' + t['current'], t['numbers_exact'] and sha(P/t['current'])==t['current_sha256'] and sha(O/t['prior'])==t['prior_sha256'])
for rel,expected_hash in num['input_sha256'].items():
    require('numeric_input_' + rel, sha(P/rel)==expected_hash)

bib = read(O/'bibliography-layout-audit.json')
require('bibliography_current_pdf', bib['status']=='PASS' and bib['pdf_sha256']==sha(M/'main.pdf'))
require('all_77_reference_urls', (bib['references'],bib['external_link_annotations'],bib['unique_external_uris'])==(77,107,77) and not bib['bib_bbl_url_mismatches'] and not bib['bbl_uris_without_pdf_annotation'])
require('reported_identifiers_complete', all(any(x in u for u in r['bbl_urls']) for x in ['2610.20962v1','electronics14071263','2607.18826v1'] for r in [next(v for v in bib['all_references'] if any(x in z for z in v['bbl_urls']))]))
require('publisher_date_spacing', 'publisher version2025' not in txt(M/'main.bbl'))
review = read(O/'content-review.json')
require('content_review_no_unresolved_refs', not review['closure']['missing_inputs'] and not review['closure']['undefined_local_refs'])
for rel,h in {**review['closure']['source_hashes'],**review['final_small_changes_readonly_confirmation']['additional_checked_source_sha256']}.items():
    require('reviewed_' + rel, sha(P/rel)==h)
visual = read(O/'visual_qa.json')
require('visual_review_70_pages', visual['status']=='PASS' and all(d['pdf_sha256']==sha(P/'pdf'/(n+'.pdf')) and d['reviewed_pages']==list(range(1,pages[n]+1)) for n,d in visual['documents'].items()))

anon = read(O/'anonymous-paper-check.json')
z = O/'anonymous-paper-source.zip'
require('anonymous_archive_hash', sha(z)==anon['archive_sha256'])
with zipfile.ZipFile(z) as f:
    require('anonymous_archive_member_hashes', {k:hashlib.sha256(f.read(k)).hexdigest() for k in f.namelist()}==anon['members'] and f.testzip() is None)
    for n in ['main','supplement']:
        require('anonymous_' + n + '_pdf', f.read(n+'.pdf')==(P/'pdf'/(n+'.pdf')).read_bytes())
        for rel in closure(M,n+'.tex'):
            require('anonymous_source_' + rel, f.read('manuscript/'+rel)==(M/rel).read_bytes())
require('latest_checklist_complete', len(read(O/'checklist-coverage.json')['items'])==19)
require('no_new_llm_runs', snap['current_manuscript']['new_llm_runs_this_revision']==0)
with ThreadPoolExecutor(max_workers=10) as pool:
    actual = dict(zip(old, pool.map(lambda k: sha(P / k), old)))
require('prior_experiment_evidence_provenance_hashes', actual == old, len(old))
result = {'status':'PASS','revision':'R9','checked_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'pdf_pages':pages,'pdf_sha256':{n:sha(P/'pdf'/(n+'.pdf')) for n in pages},'scope':'Publication, immutable-source preservation, numerical transcription, current review and visual receipts. Does not certify security, external validity or independent human recoding.'}
if '--save' in sys.argv:
    (O/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'pdf_pages':pages,'retained_files':len(old)},indent=2))
