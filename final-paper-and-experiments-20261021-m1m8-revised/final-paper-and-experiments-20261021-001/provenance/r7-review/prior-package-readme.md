# Current E13 measurement revision

Current manuscript and supplement include 4,140 live tool sessions and timing/full-tunnel controls. See `experiments/sp2027-r6-timing/README.md` and `provenance/timing/validation.json`. Current verification: `python -B provenance/timing/verify_publication.py`. Historical document-specific verifiers below describe earlier editions.

# 完整 690 次真实 Agent 实验与 SoK 主文结构修订版

当前论文：`pdf/main.pdf`、`pdf/supplement.pdf`；源文件在 `manuscript/`。正文截至第 13 页，References 从第 13 页开始，附录在第 17 页，全文 17 页；补充材料 31 页。E9 使用完整 414 训练＋276 测试。当前修订来源与检查在 `provenance/review-closure/`；`provenance/shadow-deployment/` 保留前轮部署论证；`provenance/sok-restructure/` 保留上一轮 SoK 文稿与配对统计记录；`provenance/main-690/` 保留上一轮文稿版本的记录。

主文 Table 5 显示全部 58 个核心研究族的生成层、观察层及威胁类型；Table 8 显示 20 个防御族的全部 180 个 R1–R9 审计单元。符号区分绑定、部分、未报告、未核实和不适用。检索对账表与 24 场景混淆矩阵已移到补充材料。`artifact-index.json` 将 Appendix A 中的四个逻辑模块映射到实际归档文件；保留物理目录及旧数据以保障可追溯性。

## 核心结果与贡献

论文把 82 个研究家族、39 条结果记录和 20 个防御家族的审计连接到受控实验与真实 Agent 评估。完整队列使用 115 个任务、两个 prompt、各三次重复，模型统一为 GPT-6.1 Sol / low。

- 基线网络取消/退货 BA 为 **97.2% / 94.0%**。
- 仅训练集校准的在线 shadow cover + 恒定分帧降低 **47.2 / 44.0 个百分点**至 **50.0% / 50.0%**；成本 **15.39× 字节、3.83× 调用**。
- 规则 prompt 将机械规则遵循度提高到 **97.1%**，但网络 BA 仍为 **97.2% / 93.5%**。
- 主表加入 padding-only 与 shape-only 消融；S14 给出全部区间、资源成本和配对 prompt 差异。
- 新增事后配对程序差值：联合减原始的 BA 为 −47.2 [−50.0, −33.3] 和 −44.0 [−48.9, −27.8] 个百分点。使用原 2,000 次共同客户簇抽样，每次重新取两种条件的攻击套件最大值。原绝对阈值及原始结果不变。

网络测量使用真实模型轨迹的本地 TLS 回放。真实工具调用透传，shadow 状态与响应隔离，保持逻辑规划器观测历史，因而可以在同一轨迹上比较纯程序层防御。该等价性假定确定性工具及无时间相关副作用；不涵盖在线交互延迟和共享资源反馈。50% 点估计与配对降幅支持实测信号抑制；有限客户簇上的绝对上界判定仍未达到两目标共同标准。主文和 S14 分别报告这两个统计问题。

## 数据与历史版本

- `experiments/sp2027-r4-full-20261023/`：已验证完整队列，完整预测、结果、捕获和新增 27 次运行；复用基础档案，无需本地工作区。
- `experiments/sp2027-r4-snapshot-20261023/`：不可变 663 次快照（414 训练、246 主分析测试、另 3 次单列测试）。后 3 次与新增 27 次一起将完整测试扩展至 276 次。
- `experiments/sp2027-r3/`：历史重分析，E6/E7 当前历史区间和工具识别结果的来源。
- `experiments/sp2027-r2/`：历史 E5–E8、原始注册和结果。
- `experiments/reviewer-audit/`、`experiments/revision-m1-m8/`、`evidence/retained-release007/`：更早证据，保持原样。
- `provenance/snapshot.json` 和 `SHA256SUMS.json`：当前文稿来源闭包与全包文件哈希。

本轮按用户要求将完整队列纳入主稿，取代先前“只作为独立补充”的文稿安排。原 663 论文版保存在提交 `9e1278b` 和历史分卷包中；完整队列独立补充及其交付收据保持 `c8e90bb` 状态。`REVISION-R4.md`、`provenance/full-cohort-delivery.json` 以及更早说明均为对应阶段的历史记录。

`experiments/sp2027-r4/` 是已完成采集的本地工作区，不属于发布包，清单显式排除；发布目录其余所有文件逐一校验。

## 校验与复算

```text
python -B verify_package.py
python -B verify_revision.py
python -B provenance/review-closure/verify_manuscript.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
python -B experiments/sp2027-r4-full-20261023/verify_extension.py
python -B experiments/sp2027-r4-full-20261023/reproduce.py --reanalyze
```

前四项为文件、来源和文稿一致性检查；文稿检查另需 pypdf。后两项核对决策和评分、重建完整队列并运行冻结分析。新增配对差值由 `python -B provenance/sok-restructure/analyze_paired.py` 复算；两份表格生成器接受 `--check` 做只读比对。实验复算环境为 Python 3.12、numpy 2.5.4、scikit-learn 1.9.0，详见实验 README。全部命令均不发起模型请求。旧 `provenance/main-690/verify_manuscript.py` 对应提交 `f0fb3d2` 的历史布局，不用于当前稿件。

在 `manuscript/` 中，对 main、supplement 分别运行 pdflatex、bibtex、pdflatex 两次。IEEEtran 1.8b conference,compsoc；最新 PDF 与编译日志随包交付。


## 已合并的 R5 与当前统计补充

`experiments/sp2027-r5-crossfit/` 保留远端已发布的交叉拟合、六点前沿、训练内选点和写调用定位数据。当前主文 §8.5 / Table 12 及补充 S15 引用这些结果；其 README 与 `REVISION-R5.md` 保留历史写作记录，当前范围和解释以本文及 `provenance/sok-restructure/` 为准。

新增 S16 的 32 格任务置换参考由 `provenance/sok-restructure/conditional_null.py` 生成，`--check` 可作确定性重算核对；它不替代原客户簇区间或阈值。R5 再验证收据在 `r5-reverification.json`，表格可用 `verify_r5_tables.py` 重新生成比对。

## 2026-10-24 部署架构修订

§8.2–§8.4、§9.1 与新增 S17 将 per-call padding、完整传输隧道、调用可见中继、可信网关及提供方状态观察分开。三条 shadow 实现路径为合法读取/no-op、原生非提交/测试环境、网关隔离模拟器。新增五条官方部署引用，原 82 研究族与全部实验数据不变。当前文稿检查使用 `provenance/review-closure/verify_manuscript.py`（包含本轮后续修订）；旧 `provenance/sok-restructure/verify_manuscript.py` 对应 16/27 页历史版本。

## 审稿问题 2–5 修订

新增 S18 列出 82 族到 39 条记录的完整映射：20 个缓解族贡献 33 条记录，6 个对照族各贡献 1 条。作者已明确确认 39 条记录和 180 单元格的定位核验，以及 82 族分类复核；κ 表示归档提取—复核两列的一致性，另有最终裁定列。独立盲审模板是复现基础设施。

Table 8 改用 B/P/U/?/–，不改变状态；Table 5 与 Table 12 改善排版而保持数值。S18 同时提供实验编号对应、绝对阈值解释和 Timing/闭环评估规格。没有新增模型、Timing 或外部验证结果。旧 shadow-deployment 文稿检查针对前轮 17/29 页，当前为 17/31 页。
