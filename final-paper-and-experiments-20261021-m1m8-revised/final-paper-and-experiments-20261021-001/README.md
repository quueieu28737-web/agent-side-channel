# 真实 Agent 快照修订版（2026-10-23，R4）

## 完整队列补充已完成

690 运行（414 训练＋276 测试）的独立补充位于 `experiments/sp2027-r4-full-20261023/`；阅读 `pdf/full-cohort-supplement.pdf`。原主稿、原补充材料和 663 快照保持原样，以下快照说明保留其历史样本范围。新增全队列网络 BA 为基线 97.2%/94.0%、联合程序防御 50.0%/50.0%；字节/调用成本 15.39×/3.83×。规则 prompt 合规率 97.1%，但原始网络 BA 仍为 97.2%/93.5%。

新增 27 个运行与此前单列的 3 个运行共同把主测试样本从 246 扩展为 276。全部模型、prompt、划分、校准和预先冻结的分析代码保持一致。复算：

    python -B experiments/sp2027-r4-full-20261023/verify_extension.py
    python -B experiments/sp2027-r4-full-20261023/reproduce.py --reanalyze

新增数据以增量方式引用旧模型档案；完整队列不依赖本地工作目录。完整校验、决策对齐和重算结果随新目录交付，详情见其 README。`provenance/full-cohort-delivery.json` 记录本次交付范围。

## 历史快照说明

最新阅读文件：pdf/main.pdf、pdf/supplement.pdf；来源在 manuscript/。修订说明见 REVISION-R4.md。

R4 新增 GPT-6.1 Sol / low 真实 Agent 轨迹、仅训练集校准的完整防御组件评估和规则 prompt 对照。当前固定快照保留 663 个完成运行；主分析使用 414 训练运行及 41 个完整配对测试任务的 246 运行。剩余计划运行作为后续补充，不混入本轮数字。

核心结果：基线网络取消/退货 BA 为 96.7%/93.4%，在线 shadow cover + 恒定分帧为 50.0%/50.0%，成本为 15.3× 字节和 3.8× 调用。规则 prompt 达到 96.7% 的工作流合规率，但意图识别仍高于 92%。正文突出这些实测贡献；完整区间、消融、成本与方法在 Supplement S14。

## 实验和来源

- experiments/sp2027-r4-snapshot-20261023/：当前不可变快照，全部原始轨迹、压缩模型记录、冻结校准、TLS 捕获、预测和校验程序。
- experiments/sp2027-r3/：历史后审稿重分析；E6/E7 的当前历史区间和工具识别结果以 R3 为准。
- experiments/sp2027-r2/：历史 E5–E8、原始注册和结果。注册 commit 16f6254。
- experiments/reviewer-audit/、experiments/revision-m1-m8/、evidence/retained-release007/：更早的证据与修订数据，保持历史范围。
- provenance/snapshot.json 和 SHA256SUMS.json：当前来源闭包和全包字节清单。

本地活跃目录 experiments/sp2027-r4/ 是继续采集的工作区，不属于冻结交付包；清单显式排除它。发布目录自身的所有文件仍逐一校验。

## 校验与复算

    python -B verify_package.py
    python -B verify_revision.py
    python -B experiments/sp2027-r2/verify_r2.py
    python -B experiments/sp2027-r3/verify_r3.py
    python -B experiments/sp2027-r4-snapshot-20261023/verify_snapshot.py

前三项使用标准库。R3/R4 依赖 numpy / scikit-learn；R4 运行环境与离线复算顺序见其实验 README。校验不调用模型。R4 的最终收据为 validation.json。

LaTeX 使用 IEEEtran 1.8b conference,compsoc。进入 manuscript/，对 main、supplement 分别运行 pdflatex、bibtex、pdflatex 两次。最新 PDF 和编译日志均在本包。

## 结果范围

E9 测量真实模型轨迹的本地 TLS 回放，防御参数不接触测试集。程序条件复用同一轨迹，故奖励不变是结构性质。当前是一个模型、一个公开基准的内部完成快照，尚非完整 690 队列或外部独立验证。主稿保留必要范围说明，操作日志放入归档。

REVISION-R3.txt、REVISION-RESPONSE.txt 和原始输入包是历史文档，其中“未运行真实 LLM”等状态只适用于当时版本。后续全队列结果以单独补充交付，不覆盖本轮冻结快照。
