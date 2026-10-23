# agent-side-channel

当前版本：2026-10-23 真实 Agent 实验快照修订。主稿将结果记录审计、受控边界实验和真实 Agent 评估串联，突出有数据支撑的贡献。

## 已完成：690 运行的独立补充

完整队列现已完成：414 训练＋276 测试，115 任务、两个 prompt、各三次。阅读 [完整队列补充 PDF](full-cohort-supplement.pdf)；说明见 [完整队列交付说明](docs/R4-完整队列补充说明.md)。主稿和原补充材料保留 663 快照的历史范围。

- 完整测试基线网络 BA：取消 **97.2%**、退货 **94.0%**；训练集校准的联合程序防御：**50.0% / 50.0%**，成本 **15.39× 字节、3.83× 调用**。
- 规则 prompt 合规率 **97.1%**，原始网络 BA 仍为 **97.2% / 93.5%**；任务奖励基线 **110/138**、规则组 **105/138**。
- 完整校验覆盖 690 运行、2,760 次 TLS 回放和 176 组攻击预测；增量核验将全部 11,586 个模型决策与轨迹对应，攻击重算与保存结果完全一致。
- 新目录 `experiments/sp2027-r4-full-20261023/` 复用旧快照，仅新增最后 27 个运行的模型记录。`r4-full-cohort-extension-20261023.zip` 是依赖旧发布包的增量包，其校验信息在同名 `.json` 文件中。

完整结果保持相同结论方向；区间仍未支持两个目标同时达到预设有限攻击套件标准。真实 LLM 轨迹、本地 TLS 回放与外部独立验证的范围在补充中明确区分。

## 当前论文与结果

- 阅读：main.pdf、supplement.pdf；E9 方法和完整消融在补充材料 S14。
- 快照：663 个完成运行；训练 414 次，测试 249 次。主分析采用两个 prompt 组各 3 次均完整的 41 个测试任务，共 246 次；另 3 次保留单独报告。
- 基线网络攻击 BA：取消 96.7%、退货 93.4%；仅训练集校准的在线 shadow cover + 恒定分帧：50.0% / 50.0%，字节 15.3 倍、调用 3.8 倍。
- 规则 prompt 工作流合规率为 96.7%，但意图识别仍高于 92%；任务完成率基线 82.1%、规则组 78.0%。
- 统一 GPT-6.1 Sol / low；训练和测试客户不重叠；训练完成后先冻结防御，再采集测试。
- 网络测量是实际模型轨迹的本地 TLS 回放；程序条件复用轨迹，因此奖励相等是结构性质。区间尚不证明已消除泄漏。

完整包目录：final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/。
新增实验：experiments/sp2027-r4-snapshot-20261023/，含原始轨迹、模型记录、冻结参数、全部预测及校验程序。
修订说明：docs/R4-真实Agent快照修订说明.md；包内 REVISION-R4.md。

完整交付包：paper-review-revised-20261023.zip.001 等分卷，清单在 paper-review-revised-20261023.parts.json。下载全部分卷后运行 `python reassemble_r4_release.py`，按 SHA256 验证并合成为完整 ZIP。旧 paper-review-revised-20261021.zip 保留为 R3 历史包。

## 复现

在完整包目录运行：

    python -B verify_package.py
    python -B verify_revision.py
    python -B experiments/sp2027-r2/verify_r2.py
    python -B experiments/sp2027-r3/verify_r3.py
    python -B experiments/sp2027-r4-snapshot-20261023/verify_snapshot.py

R4 使用 Python 3.12、numpy 2.5.4、scikit-learn 1.9.0，详细复算顺序见其 README。校验与离线复算不发起模型请求。
LaTeX 使用 IEEEtran 1.8b conference,compsoc；在 manuscript/ 中分别运行 pdflatex、bibtex、pdflatex 两次。

## 快照与后续补充

主稿的 663 快照与新完成的 690 全队列分别报告。后者作为独立补充，原主稿、S14 和快照不被覆盖。原工作目录 experiments/sp2027-r4/ 不进入版本化发布包；全队列发布通过旧快照和新增记录重建，无需这个本地目录。

R2 注册、R3 重分析和历史输入包保留。独立外部验证、多模型/多环境泛化、在线延迟与反馈效用，以及审计相对简单清单的增量价值，仍是后续工作。

第一轮根目录脚本是历史工具，不能用于覆盖当前论文。当前包的编译日志、来源闭包和 SHA256 清单随交付更新。
