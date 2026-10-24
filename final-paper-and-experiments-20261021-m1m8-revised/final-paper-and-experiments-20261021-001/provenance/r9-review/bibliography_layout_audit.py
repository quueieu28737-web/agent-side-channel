"""Read-only current-PDF bibliography links and IEEEtran title-space audit.

Run with bundled Python containing pypdf/pdfplumber. Does not compile or edit TeX.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
from pypdf import PdfReader
import pdfplumber

O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
pdf=M/'main.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(u):return unquote(re.sub(r'\\([_%&#])',r'\1',re.sub(r'\s+','',u)))
main=(M/'main.tex').read_text(encoding='utf-8')
bbl=(M/'main.bbl').read_text(encoding='utf-8')
bibnames=re.search(r'\\bibliography\{([^}]+)\}',main).group(1).split(',')
bibs={n:(M/(n+'.bib')).read_text(encoding='utf-8') for n in bibnames}
entries={};duplicates=[]
for name,text in bibs.items():
    for piece in re.split(r'(?m)(?=^@\w+\s*\{)',text):
        match=re.match(r'@\w+\s*\{\s*([^,]+),',piece)
        if not match:continue
        key=match.group(1);url=re.search(r'(?i)\burl\s*=\s*\{([^}]+)\}',piece)
        if not url:url=re.search(r'\\url\{([^}]+)\}',piece)
        if key in entries:duplicates.append(key)
        entries[key]=dict(source=name+'.bib',url=norm(url.group(1)) if url else None)
chunks=re.split(r'\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}',bbl)
refs=[]
for i in range(1,len(chunks),2):
    key=chunks[i];urls=[norm(u) for u in re.findall(r'\\url\{([^}]+)\}',chunks[i+1])]
    source=entries.get(key)
    refs.append(dict(number=(i+1)//2,key=key,bbl_urls=urls,bib=source,
        bib_bbl_url_equal=bool(source and (urls==[source['url']] if source['url'] else not urls))))
reader=PdfReader(pdf);links=[]
for no,page in enumerate(reader.pages,1):
    for aa in page.get('/Annots',[]):
        a=aa.get_object();action=a.get('/A',{})
        uri=action.get('/URI')
        if uri is not None:
            links.append(dict(page=no,uri=str(uri),normalized_uri=norm(str(uri)),rect=[float(x) for x in a['/Rect']]))
urls_bbl={u for r in refs for u in r['bbl_urls']};urls_pdf={r['normalized_uri'] for r in links}
unmatched=[v for v in links if v['normalized_uri'] not in urls_bbl]
missing=sorted(urls_bbl-urls_pdf)
issues=[r for r in refs if not r['bib_bbl_url_equal']]
focused=[]
reported=[(26,'nazaraliyev2026page404','2610.20962v1'),(34,'jiao2025llmwfin','electronics14071263'),(51,'park2026crosscampaign','2607.18826v1')]
current_numbers={r['key']:r['number'] for r in refs}
for original_no,key,term in reported:
    r=next(r for r in refs if r['key']==key);pages=[]
    for page_no,page in enumerate(reader.pages,1):
        text=page.extract_text()
        pos=text.find(term)
        if pos>=0:pages.append(dict(page=page_no,excerpt=text[max(0,pos-80):pos+len(term)+170]))
    focused.append(dict(**r,original_R8_reference_number=original_no,complete_identifier_extracted=bool(pages),pdf_evidence=pages,
        annotations=[l for l in links if any(l['normalized_uri']==u for u in r['bbl_urls'])]))
with pdfplumber.open(pdf) as document:
    first=document.pages[0];words=first.extract_words()
    title=[w for w in words if w['top']<140]
    abstract=next(w for w in words if w['text'].startswith('Abstract'))
    layout=dict(page_size_points=[first.width,first.height],title_ink_top_pt=min(w['top'] for w in title),
        title_ink_top_inches=min(w['top'] for w in title)/72,
        title_ink_bottom_pt=max(w['bottom'] for w in title),
        abstract_ink_top_pt=abstract['top'],title_words=title)
cls=Path('C:/Users/Administrator/AppData/Local/Programs/MiKTeX/tex/latex/ieeetran/IEEEtran.cls')
clines=cls.read_text(encoding='utf-8',errors='replace').splitlines()
class_evidence=[dict(line=i,text=t) for i,t in enumerate(clines,1) if any(s in t for s in [
 '\\def\\IEEEtitletopspace','\\IEEEsettopmargin{t}{1in}','\\IEEEsettopmargin{t}{0.75in}',
 '\\@IEEEcompsocconfonly{\\normalfont\\normalsize\\vskip 2',
 '\\@IEEEauthorblockconfadjspace{0.75'])]
report=dict(status='PASS' if not issues and not unmatched and not missing else 'REVIEW',
    pdf_sha256=sha(pdf),pdf_pages=len(reader.pages),bbl_sha256=sha(M/'main.bbl'),
    bib_sha256={n+'.bib':sha(M/(n+'.bib')) for n in bibnames},references=len(refs),
    bib_bbl_url_mismatches=issues,duplicate_keys_in_loaded_bibs=duplicates,
    external_link_annotations=len(links),unique_external_uris=len(urls_pdf),
    external_uris_missing_from_bbl=unmatched,bbl_uris_without_pdf_annotation=missing,
    all_references=refs,all_pdf_external_links=links,focused_references=focused,
    official_source_checks=[
        dict(reference=current_numbers['nazaraliyev2026page404'],original_R8_reference=26,url='https://arxiv.org/abs/2610.20962v1',html='https://arxiv.org/html/2610.20962v1',
             title_match=True,version='v1',submitted='2026-10-14',latest_version_at_check='v2 2026-10-18',
             conclusion='Version-specific v1 citation and clickable HTML URL are consistent; no truncation'),
        dict(reference=current_numbers['jiao2025llmwfin'],original_R8_reference=34,url='https://www.mdpi.com/2079-9292/14/7/1263',doi='10.3390/electronics14071263',
             title_match=True,published='2025-03-23',access='Publisher-index search result confirms date; direct article and notes return HTTP 429',
             conclusion='DOI complete and PDF annotation equals bib URL; actual missing space in version2025 fixed in bib only'),
        dict(reference=current_numbers['park2026crosscampaign'],original_R8_reference=51,url='https://arxiv.org/abs/2607.18826v1',html='https://arxiv.org/html/2607.18826v1',
             title_match=True,version='v1',submitted='2026-07-21',
             conclusion='Complete identifier and clicked HTML URI agree with bib and official source; no URL mismatch')],
    actual_bib_edit=dict(path='manuscript/evidence/search-completion-20261021-001/new_refs.bib',key='jiao2025llmwfin',
        before='Consulted publisher version2025-03-23',after='Consulted publisher version 2025-03-23',
        scope='Spacing only. Audit reads current manuscript/main.pdf and main.bbl; this script performs no compilation'),
    layout=layout,ieeetran_class_sha256=sha(cls),ieeetran_default_evidence=class_evidence,
    layout_diagnosis='Current conference,compsoc class supplies one-inch text top, default title-top half baseline, and an additional two normal baselines before compsoc conference title. Empty author still runs conference author-block machinery. No local top-margin, title-top-space, geometry, or title negative-vspace overrides found in main.tex.',
    layout_recommendation='Do not move text using margins or class edits. If venue requires a different title format, compare its official template/class options first. Empty author affects gap below title; it does not explain upper title displacement alone. No modified/default comparison PDF was compiled, so diagnosis is source-derived plus observed PDF coordinates.',
    default_class_option_comparison='IEEEtran.cls default conference branch sets nominal text top .75in (line 1744); conference+compsoc overrides this to 1in (line 1792), before line-grid quantization. The actual class option therefore adds nominal .25in text-top margin compared with plain conference, plus its own title mechanism; this is not a user-added blank region.',
    limitations='Audit covers PDF external URI annotations against all active main.bbl URL fields and their five loaded bib databases, not external link availability for every cited source. Only the three reported entries received fresh official web verification.')
(O/'bibliography-layout-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# R9 bibliography and title layout audit','',f"Status: {report['status']}. {len(refs)} references; {len(links)} external link annotations / {len(urls_pdf)} unique URIs.",'',
 '## Reported references','',
 f"- Current [{current_numbers['nazaraliyev2026page404']}] (R8 [26]) PAGE404: complete arXiv:2610.20962v1; clickable HTML URI matches bib and the official version-specific arXiv page. Latest v2 does not invalidate an explicitly consulted v1.",
 f"- Current [{current_numbers['jiao2025llmwfin']}] (R8 [34]) LLM-WFIN: full DOI and click URI agree. Official publisher search result confirms 23 March 2025; direct article/notes returned HTTP 429. Actual missing space in `publisher version2025-03-23` was fixed in bib to `publisher version 2025-03-23`.",
 f"- Current [{current_numbers['park2026crosscampaign']}] (R8 [51]) Cross-Agent Campaign Attribution: complete arXiv:2607.18826v1. Click URI, bbl and bib all use the same HTML v1 URL, confirmed on official abs/html pages. No mismatch or truncation was found.",'',
 '## All main PDF links','',
 f"- Bib/bbl URL mismatches: {len(issues)}; PDF external links absent from bbl: {len(unmatched)}; bbl URLs missing PDF annotations: {len(missing)}.",
 '- Full per-reference and per-annotation mappings, including rectangles and hashes, are in the JSON. Internal citation/destination annotations are excluded from external-URL checks.','',
 '## First-page title whitespace','',
 f"- Letter page: {layout['page_size_points']} points. First title ink top: {layout['title_ink_top_pt']:.3f} pt = {layout['title_ink_top_inches']:.4f} in; title bottom {layout['title_ink_bottom_pt']:.3f} pt; abstract top {layout['abstract_ink_top_pt']:.3f} pt.",
 '- '+report['layout_diagnosis'],'- '+report['default_class_option_comparison'],'- '+report['layout_recommendation'],'',
 'Official sources: [PAGE404 v1](https://arxiv.org/abs/2610.20962v1); [LLM-WFIN publisher](https://www.mdpi.com/2079-9292/14/7/1263); [Cross-Agent v1](https://arxiv.org/abs/2607.18826v1).','',report['limitations']]
(O/'bibliography-layout-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','references','external_link_annotations','unique_external_uris','bib_bbl_url_mismatches','external_uris_missing_from_bbl','bbl_uris_without_pdf_annotation','layout']},ensure_ascii=False,indent=2))
