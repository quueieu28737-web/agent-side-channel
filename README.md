# agent-side-channel

当前版本：**2026-10-23，完整 690 次真实 Agent 实验与 SoK 主文结构修订版**。

## 最新论文

- [主稿](main.pdf)：正文截至第 13 页，References 从第 13 页开始，Appendix 在第 17 页；全文 17 页。
- [补充材料](supplement.pdf)：S14 已统一为完整队列的方法、消融、区间、成本及 prompt 对照。
- [本次修订说明](docs/SOK-结构与统计修订说明.md)：主文 58 族映射、20×9 审计矩阵、配对程序差值与轨迹等价性。
- [上一轮完整队列主稿修订说明](docs/R4-690主稿修订说明.md)：完整 690 次结果首次进入主稿的历史记录。

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

联合程序防御降低基线 BA **47.2 / 44.0 个百分点**。新增共同客户簇重采样的配对分析：联合减去原始 BA 的 95% 区间分别为 **[−50.0, −33.3] / [−48.9, −27.8] 个百分点**。规则 prompt 将测得工作流合规率从 **86.2% 提高至 97.1%**，但意图识别仍高于 93%。基线与规则组任务奖励分别为 **110/138** 和 **105/138**。

网络结果来自真实模型轨迹的本地 TLS 回放。真实调用透传、shadow 状态隔离和返回值屏蔽保持逻辑规划器观测历史；复用轨迹隔离程序防御的效果与成本。联合防御的 50% 点估计消除了本攻击套件的实测 BA 优势，配对区间支持显著降幅；原预设绝对上界标准仍单独报告。新增差值分析是 post hoc，不改变冻结协议。

## 源码、数据与校验

包目录：`final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/`。

- `manuscript/`：最新主稿与补充材料的 LaTeX 源码。
- `experiments/sp2027-r4-full-20261023/`：完整队列结果、预测、TLS 捕获及新增 27 次运行。
- `experiments/sp2027-r4-snapshot-20261023/`：不可变 663 次运行快照和基础模型档案。
- `artifact-index.json`：附录四个逻辑模块到实际归档路径的索引。
- `provenance/sok-restructure/`：本轮文稿修订来源、表格生成器、配对重算和校验收据。
- `provenance/main-690/`：上一轮主稿版本的历史来源与收据；其文稿校验器对应旧版排版。

在包目录运行：

```text
python -B verify_package.py
python -B verify_revision.py
python -B provenance/sok-restructure/verify_manuscript.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

完整实验已通过 690 次运行、11,586 个模型决策、2,760 次 TLS 回放和 176 组攻击预测校验；离线重算与保存结果完全一致。本轮复用冻结结果，并复核全部 2,760 个会话的真实调用投影。新增配对差值可用 `python -B provenance/sok-restructure/analyze_paired.py` 重算（需要 numpy 和 scikit-learn）；表格校验与文稿检查需要 pypdf。详细环境见完整队列目录 README。上述校验和复算不调用模型。

LaTeX 使用 IEEEtran 1.8b conference,compsoc；在 `manuscript/` 分别对 `main`、`supplement` 运行 pdflatex、bibtex、pdflatex 两次。

## 版本与交付包

- 当前 GitHub main 的 `main.pdf`、`supplement.pdf` 已纳入完整队列。
- `paper-sok-restructure-20261023.zip` 为本轮增量更新包，适用于提交 `f0fb3d2`；校验信息见同名 JSON。
- `paper-690-manuscript-update-20261023.zip` 保留上一轮完整队列主稿更新版，适用于包含完整队列提交 `c8e90bb` 的仓库。
- [完整队列独立补充](full-cohort-supplement.pdf) 和 `r4-full-cohort-extension-20261023.zip` 保留上一轮状态；前者中的“保留原主稿”描述对应当时版本。
- `paper-review-revised-20261023.zip.001` 等分卷是 **663 次运行的历史论文包**，不代表当前主稿。`reassemble_r4_release.py` 可恢复它；`paper-review-revised-20261021.zip` 保留更早 R3 版本。

R2/R3、663 快照、完整队列数据与旧发布包均保持原样。根目录早期修订脚本是历史工具，不能用于覆盖当前稿件。
