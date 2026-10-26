"""Condense appendix navigation to avoid an almost-empty text page before tables."""
from pathlib import Path
O=Path(__file__).resolve().parent;M=O.parents[1]/'manuscript'
content={
'30-reproducibility-guide.tex':r"""\section{Audit Trail}\label{app:audit-trail}
The artifact preserves the 82-family map, 39-record ledger, 180 family cells and 351 record cells with source versions and locators. S33 publishes query membership and sensitivity checks. Case-study protocols, observations and uncertainty calculations retain their original cohorts and provenance.
""",
'49-r9-record-index.tex':r"""\section{Result-record index}\label{app:records}
Table~\ref{tab:r9-record-index} indexes all 39 records by measurement mode and source locator. Marks distinguish six contextual controls ($\ddagger$) and six final-search additions ($\dagger$); all enter the pair inventory. The ledger retains full locators, versions and hashes.
""",
'50-r9-experiment-index.tex':r"""\section{Case-Study Artifact Index}\label{app:experiments}
Table~\ref{tab:r9-experiment-index} maps the single appendix case to historical artifact keys and supplementary methods. These keys preserve original task/customer memberships; S30 retains the corrected permutation/Holm tests and calibration resampling.
"""
}
for n,s in content.items():(M/'sections'/n).write_text(s,encoding='utf8',newline='\n')
f=M/'sections/59-holdout-compact.tex';s=f.read_text()
start=s.index('Table~');end=s.index(r'\begin{table*}')
s=s[:start]+r"""Table~\ref{tab:r19-holdouts} covers 82 families and 492 cells. Axes: T task/input/user; M model; C harness/topology; H hardware; N network/load; D time. Codes: H reported holdout; V condition comparison/recalibration; X scoped restriction; ? unresolved; -- conceptual/inapplicable. Scope C/A denotes core/adjacent. H records separation, not transfer success; ? does not establish an absent experiment. S28 retains source locators and qualified interpretations.
"""+s[end:]
f.write_text(s,encoding='utf8',newline='\n')
print('APPENDIX_NAVIGATION_COMPACTED')
