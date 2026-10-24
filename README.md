# agent-side-channel

## 当前更新：E13 Timing、在线工具延迟与完整隧道对照

完成 **4,140 个新实测 TLS 会话**，覆盖原 690 条真实 Agent 轨迹和六种传输/调度条件。训练测量后冻结全部攻击模型，再采集测试集。逐次响应与最终状态检查全部通过；主稿已加入 E13，补充材料新增 S19。

详见 [实际结果、修订和范围](docs/R6-Timing与隧道对照实验.md)。这是本地在线工具执行测量，未新增 LLM 生成、生产 API 或独立客户。原 690 次模型运行和历史证据保持不变。

- [当前主稿](main.pdf)：正文 13 页，全文 17 页。
- [当前补充材料](supplement.pdf)：36 页，S19 为新测量完整结果。
- 当前校验入口：包内 `provenance/timing/verify_publication.py`；新实验为 `experiments/sp2027-r6-timing/`。

以下保留前轮交付记录；其页数、无 Timing 实验说明和校验入口对应当时版本。


当前版本：**2026-10-24，完整 690 次真实 Agent 实验、作者复核溯源与表格可读性修订版**。

## 本轮更新：审稿问题 2–5

主文明确两阶段提取—作者复核流程，Table 8 使用清晰的文字状态码，Table 5/12 改善数字和区间展示。§6.1 与新增 S18 给出 **20 族 / 33 条缓解记录＋6 族 / 6 条对照记录**的精确映射，补齐实验编号定位，并明确 Timing 与绝对阈值的评估边界。详见 [修订与核对说明](docs/审稿问题2-5-修订与证据核对.md)。实验数据不变；没有新增 Timing 或独立盲审结果。

## 前轮更新：Shadow Cover 的部署路径与观察者边界

主稿 §8.2–§8.4、§9.1 和新增补充 S17 明确逐调用 padding 与完整恒定速率隧道的区别，给出只读/no-op、API 原生隔离、可信 MCP/Tool 网关三条路径，以及中继、网关和提供方的信任边界。详见 [修订说明](docs/Shadow-Cover-部署架构修订说明.md)。全部 690 次实验与历史归档保持原样，本轮增加架构论证与官方文档引用。

## R5 新增：交叉拟合、运行点前沿与泄漏定位（已写入主稿 §8.5 与 S15）

- 审稿意见与修改清单：docs/R5-SP2027-审稿与修改清单.md；包内说明：REVISION-R5.md；实验：experiments/sp2027-r5-crossfit/，运行 `verify_r5.py` 校验。
- E10 交叉拟合：使用完整 690 次运行，覆盖 53 个客户，其中取消、退货正例客户分别为 14 和 18 个。
  - 未防御时网络 BA 为 91.7%/85.5%。
  - 训练集校准的防御使 BA 降低 31–39 个百分点，区间不含 0；在分桶防御下，规则组与基线组的差值区间均跨零。
- E11 运行点前沿：
  - 1024 字节分桶使 BA 降到 52.2%/52.7%，字节成本 12.4×，比恒定分帧（19.8×）低 37%，两目标 BA 为 52.2%/52.7%（恒定分帧为 60.5%/52.1%）。
  - 按训练集规则选中分桶点后，在冻结的 46 个测试任务上，字节成本从 15.4× 降到 9.8×。
- E12 泄漏定位：意图由写调用携带。只看写调用时 BA 为 84–92%，去掉写调用后约为 55–60%；规则 prompt 降低读序列多样性，写序列多样性近似不变。

## 最新论文

- [主稿](main.pdf)：正文截至第 13 页，References 从第 13 页开始，Appendix 在第 17 页；全文 17 页。
- [补充材料](supplement.pdf)：共 31 页；S14 为完整队列结果，S17 为部署架构与观察者边界，S18 为证据映射、编码流程与后续评估规格。
- [上一轮 SoK 修订说明](docs/SOK-结构与统计修订说明.md)：主文 58 族映射、20×9 审计矩阵、配对程序差值与轨迹等价性。
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

联合程序防御降低基线 BA **47.2 / 44.0 个百分点**。新增共同客户簇重采样的配对分析：联合减去原始 BA 的 95% 区间分别为 **[−50.0, −33.3] / [−48.9, −27.8] 个百分点**。规则 prompt 将两条读取顺序规则的机械遵循度从 **86.2% 提高至 97.1%**，但意图识别仍高于 93%。基线与规则组任务奖励分别为 **110/138** 和 **105/138**。

网络结果来自真实模型轨迹的本地 TLS 回放。真实调用透传、shadow 状态隔离和返回值屏蔽保持逻辑规划器观测历史；复用轨迹隔离程序防御的效果与成本。联合防御的 50% 点估计消除了本攻击套件的实测 BA 优势，配对区间支持显著降幅；原预设绝对上界标准仍单独报告。新增差值分析是 post hoc，不改变冻结协议。

## 源码、数据与校验

包目录：`final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/`。

- `manuscript/`：最新主稿与补充材料的 LaTeX 源码。
- `experiments/sp2027-r4-full-20261023/`：完整队列结果、预测、TLS 捕获及新增 27 次运行。
- `experiments/sp2027-r4-snapshot-20261023/`：不可变 663 次运行快照和基础模型档案。
- `artifact-index.json`：附录四个逻辑模块到实际归档路径的索引。
- `provenance/review-closure/`：当前表格、映射、作者声明、历史文件保全与 PDF 校验收据。
- `provenance/shadow-deployment/`：前轮部署架构修订的来源与历史收据。
- `provenance/sok-restructure/`：上一轮 SoK 修订来源、表格生成器、配对重算和历史文稿收据。
- `provenance/main-690/`：上一轮主稿版本的历史来源与收据；其文稿校验器对应旧版排版。

在包目录运行：

```text
python -B verify_package.py
python -B verify_revision.py
python -B provenance/review-closure/verify_manuscript.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

完整实验已通过 690 次运行、11,586 个模型决策、2,760 次 TLS 回放和 176 组攻击预测校验；离线重算与保存结果完全一致。此前校验已核对全部 2,760 个会话的真实调用投影；本轮逐文件核对冻结数据与这些收据保持原样。配对差值可用 `python -B provenance/sok-restructure/analyze_paired.py` 重算（需要 numpy 和 scikit-learn）；表格校验与文稿检查需要 pypdf。详细环境见完整队列目录 README。上述校验和复算不调用模型。旧 `provenance/sok-restructure/verify_manuscript.py` 校验旧版页数，当前稿件使用上方新文稿校验器。

LaTeX 使用 IEEEtran 1.8b conference,compsoc；在 `manuscript/` 分别对 `main`、`supplement` 运行 pdflatex、bibtex、pdflatex 两次。

## 版本与交付包

- 当前 GitHub main 的 `main.pdf`、`supplement.pdf` 已纳入完整队列。
- `paper-review-closure-20261024.zip` 为当前审稿修订增量包，基于 `74ea9e8`，配套 JSON 核对全部条目与归档哈希。
- `paper-shadow-deployment-20261024.zip` 为前轮部署架构增量包，基于 `35d43a8`；配套 JSON 核对全部条目与归档哈希。
- `paper-sok-restructure-20261023.zip` 为上一轮增量更新包，适用于已合入 R5 的提交 `17db1ab`；校验信息见同名 JSON。
- `paper-690-manuscript-update-20261023.zip` 保留上一轮完整队列主稿更新版，适用于包含完整队列提交 `c8e90bb` 的仓库。
- [完整队列独立补充](full-cohort-supplement.pdf) 和 `r4-full-cohort-extension-20261023.zip` 保留上一轮状态；前者中的“保留原主稿”描述对应当时版本。
- `paper-review-revised-20261023.zip.001` 等分卷是 **663 次运行的历史论文包**，不代表当前主稿。`reassemble_r4_release.py` 可恢复它；`paper-review-revised-20261021.zip` 保留更早 R3 版本。

R2/R3、663 快照、完整队列数据与旧发布包均保持原样。根目录早期修订脚本是历史工具，不能用于覆盖当前稿件。
