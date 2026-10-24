import csv, json, re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MATRIX=ROOT/'manuscript/tables/family-audit-matrix.tex'
BBL=ROOT/'manuscript/main.bbl'
BASEBIBS=[ROOT/'manuscript/refs.bib',ROOT/'manuscript/refs-final-additions.bib',ROOT/'manuscript/refs-deployment.bib']
OUT=Path(__file__).parent
text=MATRIX.read_text(encoding='utf-8')
status_map={'\\textbf{B}':'Bound','\\textbf{P}':'Partial','U':'NR-R','?':'NR-V','--':'NA'}
families=[]
for line in text.splitlines():
    if '&' not in line or r'\cite{' not in line or r'\midrule' in line: continue
    fields=[x.strip() for x in line.split('&')]
    if len(fields)<10: continue
    m=re.search(r'\\cite\{([^}]+)\}',fields[0])
    if not m: continue
    key=m.group(1)
    vals=[]
    for f in fields[1:10]:
        f=re.sub(r'\\\\.*$','',f).strip()
        # Strip formatting while preserving status token.
        if r'\textbf{B}' in f: vals.append('Bound')
        elif r'\textbf{P}' in f: vals.append('Partial')
        elif f=='U': vals.append('NR-R')
        elif f=='?': vals.append('NR-V')
        elif f=='--': vals.append('NA')
        else: raise ValueError((key,f))
    if len(vals)!=9: raise ValueError((key,vals))
    families.append((key,vals))
assert len(families)==20 and len({x[0] for x in families})==20

# Read generated bibliography blocks. This is a metadata label, not certification.
bbl=BBL.read_text(encoding='utf-8')
blocks={}
for m in re.finditer(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\\end\{thebibliography\})',bbl,re.S):
    blocks[m.group(1)]=m.group(2)
entry_types={}
for bp in BASEBIBS:
    if not bp.exists(): continue
    bt=bp.read_text(encoding='utf-8')
    for m in re.finditer(r'@(\w+)\s*\{\s*([^,]+),',bt): entry_types[m.group(2).strip()]=m.group(1).lower()
def venue_label(key):
    b=blocks.get(key)
    if b is None: return 'unknown:no-main.bbl-entry'
    has_arxiv='arXiv preprint' in b or 'arXiv:' in b
    venue=bool(re.search(r'\\emph\{(?!arXiv preprint)[^}]+\}',b)) or ' in \emph{' in b or 'Proceedings' in b
    if has_arxiv and not venue: return 'arXiv-only-label-in-main.bbl'
    if venue: return 'venue-labelled-in-main.bbl'
    return 'unknown:ambiguous-bibliography-entry'

def full_form_label(key):
    b=blocks.get(key)
    if b is None: return 'unknown:no-main.bbl-entry'
    low=b.lower(); et=entry_types.get(key,'')
    if key.lower().startswith('rfc') or re.search(r'\b(iso|rfc|etsi)\s*[-:]?\s*\d+',low): return 'standard'
    if et in ('book','inbook','incollection','booklet'): return 'book'
    if et in ('manual','online') or key.lower() in {'kubernetesdryrun','stripesandboxes','postgresrollback','postgressequences'}:
        return 'vendor-doc'
    has_arxiv='arxiv preprint' in low or bool(re.search(r'arxiv:\d',low)) or 'arxiv.org/' in low
    is_venue=(bool(re.search(r'\bin\s*\\emph\{',b)) or bool(re.search(r'\\emph\{[^}]*(?:transactions|journal|proceedings|symposium|conference|workshop|electronics|acm|ieee|acl anthology)[^}]*\}',low)))
    if has_arxiv and is_venue: return 'venue-labelled-with-preprint'
    if has_arxiv: return 'arXiv-only'
    if is_venue: return 'venue-labelled'
    return 'unknown'

# Extend publication-form inventory to every actually cited main.bbl item.
all_rows=[]
for key,b in blocks.items():
    all_rows.append({'citation_key':key,'form':full_form_label(key),'bib_entry_type':entry_types.get(key,'unknown'),'title_or_bibliography_excerpt':re.sub(r'\s+',' ',b.strip())[:350],'r8_audit_family':str(key in {k for k,_ in families}).lower(),'limit':'Current manuscript citation rendering/metadata only; not independent peer-review certification'})
with (OUT/'all-citations-form-labels.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=all_rows[0].keys()); w.writeheader(); w.writerows(all_rows)
all_counts=dict(Counter(r['form'] for r in all_rows))
assert len(all_rows)==77 and sum(all_counts.values())==77
assert all_counts=={'arXiv-only':49,'venue-labelled':16,'venue-labelled-with-preprint':5,'book':1,'standard':2,'vendor-doc':4}

records=[]
r5_reason={
'uitraces2026':'Online action intervention; protected-condition adaptive result bound.',
'jeong2026wra':'Executable decoy intervention; learned protected-fit reuse is outside scoped claim.',
'netecho2025':'Learner and defense transform present; matched protected test binding partial.',
'earlybird2025':'K-conditioned calibration present; protected-condition pairing partial.',
'whisperleak2025':'Threshold learner present; post-defense fit/matched-test binding unverified.',
'spliceleak2026':'Deterministic cache/QCP mechanism, no adaptive learner comparison.',
'timewilltell2024':'Threshold learner present; defense-fit/test binding unverified.',
'gao2025iknow':'Zero-copy mechanism control, no learned-classifier adaptation comparison.',
'wei2024speculation':'Random Forest present; protected-fit and matched test binding unverified.',
'dangol2026workflow':'Bound for stored-capture adaptive contrast only; not transferred to live OHTTP.',
'pouryousef2026traffic':'Classifier under reformulation; protected-fit/matched-test binding unverified.',
'carlini2024remote':'Fixed-rate analytical cost, not an adaptive learned-attack claim.',
'hornetz2026tdxray':'Deterministic oblivious lookup benchmark, no adaptive classifier comparison.',
'chu2025safekv':'Deterministic cache isolation/window control, no adaptive classifier comparison.',
'zhu2026turing':'Refittable attack; publication run artifact and matched test binding unverified.',
'addagada2026kvgov':'Namespace isolation/analytical judge, no adaptive classifier comparison.',
'wu2026cacheprune':'Fixed cache policy evaluation, no adaptive classifier refit claim.',
'lee2026otro':'Tokenizer/mechanism intervention, no adaptive classifier contrast.',
'chen2026sparleak':'Learned attack present; protected fit and matched test binding unverified.',
'hadad2026shape':'Inspected scope reports analytic padding proposal, not protected fit/matched-test experiment.'}
r8_reason={
'uitraces2026':'Offline attribution outcome; objective user-task utility unreported.',
'jeong2026wra':'Proxy visibility and executable-decoy task outcomes are not fully joined.',
'netecho2025':'Topic prediction is not downstream user-task utility.',
'earlybird2025':'Semantic-cache component timing is not end-to-end utility.',
'whisperleak2025':'Replay volume proxy is not objective task utility.',
'spliceleak2026':'QCP component cost; task utility unreported.',
'timewilltell2024':'Analytical padding cost without protected-task utility.',
'gao2025iknow':'NA for family-level task/component utility question as scoped; loading/memory costs remain separate component evidence.',
'wei2024speculation':'NA: token payload is resource cost, not utility.',
'dangol2026workflow':'Recovery and live bytes/latency measured; objective workflow utility unreported.',
'pouryousef2026traffic':'Semantic preservation asserted; no objective task-utility measurement.',
'carlini2024remote':'Rate-cost analysis without same-condition task utility.',
'hornetz2026tdxray':'Bound component utility: vocabulary coverage; not deployment task utility.',
'chu2025safekv':'Detector and serving performance are separate; task utility unreported.',
'zhu2026turing':'Bound online task accuracy under intervention.',
'addagada2026kvgov':'ASR, hardware gap, and HMAC cost are separate objects; no joint utility.',
'wu2026cacheprune':'Bound QA F1/summarization ROUGE outcomes.',
'lee2026otro':'NA: no scoped task utility outcome for mechanism-only tokenizer analysis.',
'chen2026sparleak':'Partial: local ROUGE proxy, not autonomous workflow utility.',
'hadad2026shape':'Protected medical/document task utility unreported.'}
for key,vals in families:
    d={'family':key}
    d.update({f'R{i+1}':v for i,v in enumerate(vals)})
    d['bibliography_label']=full_form_label(key)
    d['R5_reason']=r5_reason[key]
    d['R8_reason']=r8_reason[key]
    records.append(d)
with (OUT/'family-status-overlay.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
dist={f'R{i+1}':dict(Counter(r[f'R{i+1}'] for r in records)) for i in range(9)}
app={}
for i in range(9):
    c=dist[f'R{i+1}']; app[f'R{i+1}']={'applicable':20-c.get('NA',0),'sum_all_statuses':sum(c.values()),'counts':c}
assert all(x['sum_all_statuses']==20 for x in app.values())
assert app['R5']['counts']=={'Bound':2,'Partial':2,'NR-V':6,'NA':9,'NR-R':1}
assert app['R8']['counts']=={'Bound':3,'Partial':3,'NR-R':11,'NA':3}
strict=dict(app['R8']['counts'])
strict['Bound']-=1; strict['NA']+=1 # TDXRay: component coverage, not deployment-task utility.
result={
 'inputs':{'matrix':'manuscript/tables/family-audit-matrix.tex','bibliography':'manuscript/main.bbl'},
 'family_count':20,'per_family':records,'distributions':app,
 'all_main_citations':{'count':len(all_rows),'form_counts':all_counts,'csv':'provenance/r8-review/all-citations-form-labels.csv','classification_basis':'main.bbl output plus bibliography entry type; cited-form labels only'},
 'r5_applicability':{'definition':'Matrix applicability; 20 minus NA. In R5 the 9 NA rows are fixed/non-learning scopes where a matched adaptive attack test is not the scoped claim.','counts':app['R5']['counts'],'applicable_n':app['R5']['applicable'],'matched_adaptation_bound_rate':'2/11','narrow_sensitivity_excluding_hadad':{'family':'hadad2026shape','rationale':'If R5 is limited to experiments with a learned/calibrated adaptive attacker, the inspected fixed analytic padding proposal can be regarded NA rather than NR-R.','counts':{'Bound':2,'Partial':2,'NR-R':0,'NR-V':6,'NA':10},'applicable_n':10,'bound_rate':'2/10'}},
 'r8_sensitivity':{
   'broad_component_or_task_utility':{'counts':app['R8']['counts'],'applicable_n':app['R8']['applicable'],'bound_rate':'3/17','partial_plus_unreported':14},
   'strict_deployment_task_utility':{'rule':'Treat TDXRay as NA because its measured utility is vocabulary coverage in a lookup microbenchmark, not downstream task utility; other 19 status judgements retained.','counts':strict,'applicable_n':16,'bound_rate':'2/16','partial_plus_unreported':14}},
 'arithmetic_note':'R5 expanded values are 2 Bound + 2 Partial + 1 NR-R + 6 NR-V + 9 NA = 20. The NR-R cell is present as 0 (1) in six-check-audit.tex; no missing cell.',
 'publication_note':'Bibliography labels only. “venue-labelled” means main.bbl renders a journal/proceedings venue; “arXiv-only” means the bibliography entry gives arXiv without a journal/proceedings label. Neither label is an independent peer-review verification. Unknowns are retained.',
 'status_legend':{'Bound':'B','Partial':'P','NR-R':'U, unreported in inspected scope','NR-V':'?, binding unverified','NA':'--'}
}
(OUT/'family-status-overlay.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
with (OUT/'publication-form-labels.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['family','main_bbl_label','interpretation_limit'])
    for r in records: w.writerow([r['family'],r['bibliography_label'],'Bibliography form only; not independent peer-review certification'])
print(json.dumps({'family_n':20,'distributions':app,'r5':result['r5_applicability'],'r8':result['r8_sensitivity']},indent=2))


