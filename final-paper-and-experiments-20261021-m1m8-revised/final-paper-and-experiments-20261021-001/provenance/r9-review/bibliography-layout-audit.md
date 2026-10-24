# R9 bibliography and title layout audit

Status: PASS. 77 references; 107 external link annotations / 77 unique URIs.

## Reported references

- Current [22] (R8 [26]) PAGE404: complete arXiv:2610.20962v1; clickable HTML URI matches bib and the official version-specific arXiv page. Latest v2 does not invalidate an explicitly consulted v1.
- Current [30] (R8 [34]) LLM-WFIN: full DOI and click URI agree. Official publisher search result confirms 23 March 2025; direct article/notes returned HTTP 429. Actual missing space in `publisher version2025-03-23` was fixed in bib to `publisher version 2025-03-23`.
- Current [59] (R8 [51]) Cross-Agent Campaign Attribution: complete arXiv:2607.18826v1. Click URI, bbl and bib all use the same HTML v1 URL, confirmed on official abs/html pages. No mismatch or truncation was found.

## All main PDF links

- Bib/bbl URL mismatches: 0; PDF external links absent from bbl: 0; bbl URLs missing PDF annotations: 0.
- Full per-reference and per-annotation mappings, including rectangles and hashes, are in the JSON. Internal citation/destination annotations are excluded from external-URL checks.

## First-page title whitespace

- Letter page: [612, 792] points. First title ink top: 96.430 pt = 1.3393 in; title bottom 127.430 pt; abstract top 183.939 pt.
- Current conference,compsoc class supplies one-inch text top, default title-top half baseline, and an additional two normal baselines before compsoc conference title. Empty author still runs conference author-block machinery. No local top-margin, title-top-space, geometry, or title negative-vspace overrides found in main.tex.
- IEEEtran.cls default conference branch sets nominal text top .75in (line 1744); conference+compsoc overrides this to 1in (line 1792), before line-grid quantization. The actual class option therefore adds nominal .25in text-top margin compared with plain conference, plus its own title mechanism; this is not a user-added blank region.
- Do not move text using margins or class edits. If venue requires a different title format, compare its official template/class options first. Empty author affects gap below title; it does not explain upper title displacement alone. No modified/default comparison PDF was compiled, so diagnosis is source-derived plus observed PDF coordinates.

Official sources: [PAGE404 v1](https://arxiv.org/abs/2610.20962v1); [LLM-WFIN publisher](https://www.mdpi.com/2079-9292/14/7/1263); [Cross-Agent v1](https://arxiv.org/abs/2607.18826v1).

Audit covers PDF external URI annotations against all active main.bbl URL fields and their five loaded bib databases, not external link availability for every cited source. Only the three reported entries received fresh official web verification.
