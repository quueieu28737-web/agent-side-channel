HISTORICAL DISCOVERY RECORD — 2026-09-12
The dated classifications/counts below are historical, not the current inclusion authority.
Use the current paper and evidence-release004/literature/ for the present inventory.

# Targeted coverage correction, 2026-09-12

Scope: implement the author's review-driven SoK convergence. This is not a new exhaustive search or a completed native-database review. Discovery below occurred during the immediately preceding audit in the same project conversation; primary pages were reopened in this revision. No full-manuscript content was uploaded.

## Executed discovery query families (web search, not native database exports)

- '"agent" "side channel" fingerprinting traffic 2026 paper'
- '"agent" "traffic" "fingerprinting"' (arxiv.org filter)
- '"MCP" "timing" "side channel"' (arxiv.org filter)
- '"LLM" "side-channel" "2026"' (usenix.org / ndss-symposium.org filters)
- '"LLM" "side-channel" "speculative"'
- '"LLM" "side-channel" "MIG" usenix 2026'
- '"agent" "metadata leakage" paper traffic'
- '"Network-Level Prompt and Trait Leakage in Local Research Agents" usenix'
- '"A2A-MetaTrace" arxiv'
- '"Debenedetti" "side-channel" language models'

Search-result totals, full hit exports, and recall: NR-V. Results were used as leads; neither zero results nor this list demonstrates saturation. Native IEEE/ACM/ScienceDirect execution is unverified.

## Screening decisions and checked sources

| Record | Decision | Reason / checked source scope |
|---|---|---|
| WRA network leakage | Core A | Passive destination/timing inference from agent workflows; [proceedings abstract and metadata](https://www.usenix.org/conference/usenixsecurity26/presentation/jeong). Published 2026; earlier 2025 preprint is the same study. |
| FP-Agent | Core A, behavioral part | [Primary abstract](https://arxiv.org/abs/2605.01247) and [paper sections 1--3](https://arxiv.org/html/2605.01247v1): behavioral fingerprints separated from static browser attributes and explicit identification. |
| Speculative decoding | Core B | [v4 abstract and version history](https://arxiv.org/abs/2411.01076v4); query/datastore inference via acceptance-pattern observables. Original 2024 and revised 2026 versions count once. |
| Behind Bars | Core B | [Proceedings abstract/metadata](https://www.usenix.org/conference/usenixsecurity26/presentation/gu-cheng): cross-MIG interference and LLM inference case. |
| Time Will Tell | Restore B table row | Already cited in baseline; detailed extraction remains NR-V. |
| PromptEcho | Restore B table row | [Proceedings abstract/metadata](https://www.usenix.org/conference/usenixsecurity26/presentation/li-sijia). Rechecked topic and similarity results, not exact recovery. |
| Gao et al. | Restore B table row | [Proceedings abstract/metadata](https://www.usenix.org/conference/usenixsecurity25/presentation/gao-zibo). Token/position leakage and local input/output recovery. |
| Prompt-cache audit | Restore/add B table row | [ICML proceedings abstract](https://proceedings.mlr.press/v267/gu25b.html) reports both sharing audits and hidden model-architecture inference. The latter meets the same hidden-property criterion used for identity fingerprints. Earlier classification as context-only is corrected. |
| PersonaFingerprint | Adjacent measurement | [Abstract](https://arxiv.org/abs/2605.15962) and [paper sections 2--3](https://arxiv.org/html/2605.15962v1): agent-generated personas; external validity to real users separate. |
| Privacy Side Channels in ML Systems | Boundary comparison | [USENIX 2024 primary record](https://www.usenix.org/conference/usenixsecurity24/presentation/debenedetti). Broader lifecycle / preprocessing / filtering rather than counting every component as runtime metadata. |
| A2A-MetaTrace | Pending artifact lead | [Author repository](https://github.com/dangoldbj/a2a-metatrace); paper status, observation validity, classifier and protocol security evaluation NR-V. Not added to attack totals. |
| SCAgent / agent-assisted side-channel discovery | Exclude from A | Agent is attacker/analysis tool, not leaking workflow victim. SpliceLeak remains B for the same distinction. |

Core reconciliation: 10 previously tabulated + 4 already cited records restored + 4 newly included records = 18, comprising A=4 and B=14. This arithmetic is a current-file count, not a validated PRISMA flow. Every core source URL is also retained in corpus.csv.

## Boundary dictionary

- Secret: inferred hidden variable. Identity is a separate goal, not automatically a user-privacy secret.
- Origin: layer whose execution creates the signal; observation: layer where the attacker obtains it. Mappings are our analysis.
- NR-R: confirmed not reported in checked source; NR-V: not verified; NR-A: inaccessible source; NA: not applicable.
- No inherited NR is silently promoted to NR-R.
- Source abstract checks support only their explicit content, not full-text methods, confidence intervals, or artifact correctness.

## Metadata work

Primary USENIX/PMLR/arXiv records supplied full authors for PromptEcho, Gao, Gu, Vekaria, AgentDAM, Browser Privacy, PrivacyPeek, AgentSCOPE and MCP Security Bench. AgentDAM arXiv v3 reports NeurIPS 2025 D&B acceptance; the bibliography labels this as author-reported while proceedings metadata remain pending. Publisher/DOI retrieval did not yield verified author lists for MSA and the multi-agent privacy record; these remain explicit metadata TODOs. No authors were inferred from titles.

## Outstanding coverage

Native-database exports; backward/forward citation screening; neighboring late-2026 papers; full-text extraction for the new studies; exact inherited numeric claims; A2A/MCP artifact screening; single-coder checks. This update does not establish that the topic has been fully surveyed.
