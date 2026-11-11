# Latest manuscript: R108 Agent communication side-channel SoK

- [Main PDF](main.pdf) | [Supplement PDF](supplement.pdf)
- [Compilable LaTeX ZIP](latex-source.zip)
- [Versioned source, evidence and validation](releases/r108/README.md)
- [B1 timing analysis and replay](releases/r108/b1/README.md)
- [44-setting evidence matrix](releases/r108/evidence/field-map/evidence-matrix.csv)

B1's planned secondary timing-informed cover-removal attack recovers high
task recognition. The direct-feature primary comparisons remain nonsignificant.
Client-receipt timing and supplied windows define this result; packet-time/WAN
validation remains open. A and B2 have not been collected. Main: 15 pages;
supplement: 30 pages. All prior releases and unrelated files are preserved.
Use the versioned source or clean 66-file ZIP for a new Overleaf project.

---

## Historical repository notes

Earlier version notes follow; the links above identify R108.

# Latest manuscript: R105 Agent communication side-channel SoK

- [Main PDF](main.pdf) | [Supplement PDF](supplement.pdf)
- [Compilable LaTeX ZIP](latex-source.zip)
- [Versioned source, evidence and publication scope](releases/r105/README.md)
- [44-setting evidence matrix](releases/r105/evidence/field-map/evidence-matrix.csv)
- [Conditional forwarding power planning](releases/r105/planning/README.txt)

R105 preserves the measured results and focuses the SoK on observer permissions,
protection placement and matched execution outcomes. Main: 15 pages; supplement:
26 pages. The clean source ZIP contains 59 files. The later power calculation
uses existing saved predictions and is planning sensitivity, not a new cohort.
Use the versioned source directory or ZIP for a clean build. Prior releases and
the R102 experiment package remain available; the release README defines scope.

---

## Historical repository notes

The following text records earlier versions; the links above identify R105.

# Agent communication side-channel SoK — R101

**Feedback Paths and Executed Cover**

Latest verified revision: 10 November 2026.

- [Main PDF](main.pdf)
- [Supplement PDF](supplement.pdf)
- [Compilable LaTeX ZIP](latex-source.zip)
- [Versioned source and evidence](releases/r101/)

R101 adds the classical-to-Agent transfer matrix, deployment/access table and
evidence-availability counts. The scope remains 15 direct studies and 44 settings,
with 22 selected mechanism anchors. Original results and their uncertainty are
retained. The main PDF has 15 pages (references start on page 13); the supplement
has 23 pages. Both were visually checked and independently rebuilt from the ZIP.

For a clean build, use releases/r101/source/ or latex-source.zip. The versioned
release README specifies the published evidence subset and verification scope.
The full local review archive and private collection records are not uploaded.
Historical files remain in this repository and in Git history.

---

## Archived repository introduction

The following text describes an earlier release, not R101.

# Agent side-channel SoK — Defense Evidence

R41 将统计范围明确限定为 C1–C5 纳入、含经验攻击推断评估的研究中所报告的缓解结果，并按干预实际改变的功能重新确定 R8 适用性。本轮新增模型请求为 0。

- 在这一来源框架的 52 个 Type I/II 核心家族中，19 家族关联 31 条缓解记录；33 家族在本次抽取中没有关联的合格缓解记录。这不是全部防御文献的普查；纳入来源既有攻击导向研究，也有防御导向研究。
- 对窄范围内容或逻辑功能质量，8 个适用家族中有 3 个明确绑定测量，接受部分证据后为 4/8；另 11 个家族对该质量查询不适用。保持内容的 framing、精确计算及隔离返回路径不能据此获得时限、超时或端到端任务完成保证。
- UI Traces、WRA、Dangol 和 cloud benchmark 四个 agent-associated 家族中，没有关联同条件端到端任务评分（0/4）；这不是四个都会改变执行的隐私 cover。WRA 的原始回答路径可支持窄内容保持，其新增诱饵执行的同条件任务评分仍未绑定（0/1）。Cloud 的 prompt/temperature 干预属于生成质量适用子集，明确测量为 0/1，接受部分证据为 1/1。
- 15/16 适用来源家族明确绑定推断结果，11/18 绑定成本，2/10 绑定匹配的受保护数据拟合对照；这些项目各自保留其适用分母。
- 同一受保护测试视图中，缓冲分桶从未适应攻击的 50.0% 升至重新拟合后的 70.8%；流式分批从 50.0% 升至 100.0%，恒定事件数对照保持 50.0%。结果限定于已有运输层示例。
- 补充材料保留 WRA/GLM 两轮探索及其截断：它们没有简单/适应性攻击的配对对照，不能据此声称 WRA 的适应性恢复或在线防御效果。原始记录和历史实验保留。

主稿 21 页、正文至第 13 页；补充材料 87 页。R8 当前分母、联合查询和来源删除敏感性由 `final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/manuscript/tools/r41_utility_scope.py` 复算，记录级适用性和定位符见 `final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/manuscript/data/r41-utility-scopes.json`，修订说明见 `docs/R41-P0范围与效用适用性修正.md`。原 351 格审计及此前实测结果仍可追溯。

[主稿](main.pdf) · [补充材料](supplement.pdf)