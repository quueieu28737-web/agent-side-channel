# 完整 690 次真实 Agent 实验主稿修订版

当前论文：`pdf/main.pdf`、`pdf/supplement.pdf`；源文件在 `manuscript/`。正文 13 页，全部 E9 数字采用完整 414 训练＋276 测试运行，S14 同步更新。修订说明和来源检查在 `provenance/main-690/`。

## 核心结果与贡献

论文把 82 个研究家族、39 条结果记录和 20 个防御家族的审计连接到受控实验与真实 Agent 评估。完整队列使用 115 个任务、两个 prompt、各三次重复，模型统一为 GPT-6.1 Sol / low。

- 基线网络取消/退货 BA 为 **97.2% / 94.0%**。
- 仅训练集校准的在线 shadow cover + 恒定分帧降低 **47.2 / 44.0 个百分点**至 **50.0% / 50.0%**；成本 **15.39× 字节、3.83× 调用**。
- 规则 prompt 将测得合规率提高到 **97.1%**，但网络 BA 仍为 **97.2% / 93.5%**。
- 主表加入 padding-only 与 shape-only 消融；S14 给出全部区间、资源成本和配对 prompt 差异。

网络测量使用真实模型轨迹的本地 TLS 回放。程序条件复用轨迹，奖励相等是结构性质。完整区间尚未支持两个意图同时达到预设有限攻击套件标准。独立外部复现、多模型/多环境迁移和交互延迟/反馈效应为后续评估方向。

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
python -B provenance/main-690/verify_manuscript.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
python -B experiments/sp2027-r4-full-20261023/verify_extension.py
python -B experiments/sp2027-r4-full-20261023/reproduce.py --reanalyze
```

前四项为文件、来源和文稿一致性检查；文稿检查另需 pypdf。后两项核对决策和评分、重建完整队列并运行冻结分析。实验复算环境为 Python 3.12、numpy 2.5.4、scikit-learn 1.9.0，详见实验 README。全部命令均不发起模型请求。

在 `manuscript/` 中，对 main、supplement 分别运行 pdflatex、bibtex、pdflatex 两次。IEEEtran 1.8b conference,compsoc；最新 PDF 与编译日志随包交付。
