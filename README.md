# agent-side-channel

当前版本：**2026-10-23，完整 690 次真实 Agent 实验主稿修订版**。

## R5 新增：交叉拟合、运行点前沿与泄漏定位（已写入主稿 §8.5、Table 13 和 S15）

- 审稿意见与修改清单：docs/R5-SP2027-审稿与修改清单.md；包内说明：REVISION-R5.md；实验：experiments/sp2027-r5-crossfit/，运行 `verify_r5.py` 校验。
- E10 交叉拟合：使用完整 690 次运行，覆盖 53 个客户，其中取消、退货正例客户分别为 14 和 18 个。
  - 未防御时网络 BA 为 91.7%/85.5%。
  - 训练集校准的防御使 BA 降低 31–39 个百分点，区间不含 0；规则组与防御之间无交互。
- E11 运行点前沿：
  - 1024 字节分桶使 BA 降到 52.2%/52.7%，字节成本 12.4×，比恒定分帧（19.8×）低 37%，泄漏也不更高。
  - 按训练集规则选中分桶点后，在冻结的 46 个测试任务上，字节成本从 15.4× 降到 9.8×。
- E12 泄漏定位：意图由写调用携带。只看写调用时 BA 为 84–92%，去掉写调用后约为 55–60%；规则 prompt 只统一了读调用序列。

## 最新论文

- [主稿](main.pdf)：正文 13 页，另附 1 页附录和 4 页参考文献。
- [补充材料](supplement.pdf)：S14 已统一为完整队列的方法、消融、区间、成本及 prompt 对照。
- [本次修订说明](docs/R4-690主稿修订说明.md)：更新范围、核心贡献和来源。

论文题目改为 **SoK: Evaluating LLM and Agent Side-Channel Defenses — From Evidence Audits to Real-Agent Measurements**。主线是将结果记录审计、可执行部署检查与真实 Agent 测量连接起来，明确哪些观察、状态和评估条件决定防御效果。

## 完整结果

全部 **690/690** 运行：115 个任务 × 2 个 prompt × 3 次重复。统一 GPT-6.1 Sol / low；414 次训练完成后冻结防御，再采集 276 次客户不重叠的测试。

| 测试条件 | 取消意图 BA | 退货意图 BA | 字节成本 | 调用成本 |
|---|---:|---:|---:|---:|
| 基线 | 97.2% | 94.0% | 1.00× | 1.00× |
| 规则 prompt | 97.2% | 93.5% | 1.00× | 1.00× |
| 仅 padding | 66.1% | 55.5% | 4.02× | 1.00× |
| 仅 shape cover | 60.8% | 51.9% | 4.16× | 3.83× |
| 联合程序防御 | 50.0% | 50.0% | 15.39× | 3.83× |
| 规则 + 联合防御 | 50.0% | 60.6% | 15.72× | 3.88× |

联合程序防御降低基线 BA **47.2 / 44.0 个百分点**。规则 prompt 将测得工作流合规率从 **86.2% 提高至 97.1%**，但意图识别仍高于 93%。基线与规则组任务奖励分别为 **110/138** 和 **105/138**。

网络结果来自真实模型轨迹的本地 TLS 回放。程序条件复用轨迹，奖励相等是结构性质。主稿与 S14 报告全部置信区间；联合防御点估计为 50%，但两个目标尚未同时满足预设有限攻击套件标准。

## 源码、数据与校验

包目录：`final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/`。

- `manuscript/`：最新主稿与补充材料的 LaTeX 源码。
- `experiments/sp2027-r4-full-20261023/`：完整队列结果、预测、TLS 捕获及新增 27 次运行。
- `experiments/sp2027-r4-snapshot-20261023/`：不可变 663 次运行快照和基础模型档案。
- `provenance/main-690/`：本轮文稿修订来源、表格生成器和校验收据。

在包目录运行：

```text
python -B verify_package.py
python -B verify_revision.py
python -B provenance/main-690/verify_manuscript.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

完整实验已通过 690 次运行、11,586 个模型决策、2,760 次 TLS 回放和 176 组攻击预测校验；离线重算与保存结果完全一致。详细复算命令见完整队列目录 README。校验和离线复算不调用模型。

LaTeX 使用 IEEEtran 1.8b conference,compsoc；在 `manuscript/` 分别对 `main`、`supplement` 运行 pdflatex、bibtex、pdflatex 两次。

## 版本与交付包

- 当前 GitHub main 的 `main.pdf`、`supplement.pdf` 已纳入完整队列。
- `paper-690-manuscript-update-20261023.zip` 为本轮主稿更新包，适用于包含完整队列提交 `c8e90bb` 的仓库；校验信息见同名 JSON。
- [完整队列独立补充](full-cohort-supplement.pdf) 和 `r4-full-cohort-extension-20261023.zip` 保留上一轮状态；前者中的“保留原主稿”描述对应当时版本。
- `paper-review-revised-20261023.zip.001` 等分卷是 **663 次运行的历史论文包**，不代表当前主稿。`reassemble_r4_release.py` 可恢复它；`paper-review-revised-20261021.zip` 保留更早 R3 版本。

R2/R3、663 快照、完整队列数据与旧发布包均保持原样。根目录早期修订脚本是历史工具，不能用于覆盖当前稿件。
