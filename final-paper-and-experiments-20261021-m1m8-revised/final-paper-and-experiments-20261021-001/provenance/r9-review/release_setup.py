"""Prepare R9 release metadata tooling and the user-facing change record."""
from pathlib import Path
import subprocess,json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
old=P/'provenance/r8-review'
s=(old/'release_ops.py').read_text()
s=s.replace('R8','R9').replace('r8-review','r9-review')
s=s.replace('Current R9 SoK revision, construct-validity analysis, matched comparisons and applicability-aware audit; prior experiments preserved.','Current R9 self-contained SoK presentation: operational audit rules, four demonstrations, grouped family map and complete record/experiment appendices; experimental results preserved.')
s=s.replace("'r9_record_applicability_and_self_audit'","'r8_record_applicability_and_self_audit'").replace("'provenance/r9-review/defense-self-audit.json'","'provenance/r8-review/defense-self-audit.json'").replace("'provenance/r9-review/applicability-sensitivity.json'","'provenance/r8-review/applicability-sensitivity.json'").replace("'provenance/r9-review/all-citations-form-labels.csv'","'provenance/r8-review/all-citations-form-labels.csv'").replace("'provenance/r9-review/family-status-overlay.csv'","'provenance/r8-review/family-status-overlay.csv'")
s=s.replace("'provenance/r7-review/verify_publication.py'","'provenance/r8-review/verify_publication.py'")
s=s.replace('R9 construct validity, same-operation attributes, customer sensitivity and self-audited SoK synthesis','R9 self-contained audit rules, four demonstrations and complete appendix indexes')
s=s.replace('ec2cb3955da5f73fac796637227510ccedb8265b','eab92ad71011a5a6de6ce5e2de737d7ca57ad767')
s=s.replace('provenance/r9-review/prior-package-manifest.json','provenance/r9-review/prior-release/SHA256SUMS.json')
(O/'release_ops.py').write_text(s,encoding='utf8',newline='\n')
oldroot=subprocess.run(['git','show','HEAD:README.md'],cwd=R,capture_output=True,check=True).stdout
(O/'prior-release/root-README.md').write_bytes(oldroot)
# Minor final synthesis edit; raw map values and all evidence remain fixed.
f=M/'sections/26-corpus-map.tex';s=f.read_text()
start=s.index('The 32 map-only families add');end=s.index('\\subsection{Relationship',start)
s=s[:start]+r"""The 32 map-only families extend coverage beyond mitigation comparisons: 15 list serving origins, 11 hardware and 11 orchestration; 19 concern confidentiality, nine attribution, one evasion and all five authorized-diagnostic families. They comprise 22 families without a scoped mitigation evaluation, five diagnostics, four unbound quantitative assertions, and SplitDecoy's boundary case (\S\ref{sec:defenses}). Mapping these families locates privacy targets, operator capabilities and candidate validation environments even when no scoped mitigation record enters the ledger. Counts are overlapping family-label incidences; the audit then applies its reuse rules to the 39 scoped result records.

"""+s[end:]
s=s.replace('They do not claim a new padding construction or generalize classical website-fingerprinting results; they measure where an established mechanism changes cost or residual inference when applied to streamed LLM and agent traffic.','These measurements connect established mechanisms to the cost and residual inference observed in streamed LLM and agent traffic.')
f.write_text(s,encoding='utf8',newline='\n')
print('R9_RELEASE_TOOLS_READY')
