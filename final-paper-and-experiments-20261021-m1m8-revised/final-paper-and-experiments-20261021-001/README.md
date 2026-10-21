# 审稿意见修订版（2026-10-21）

本包已按两份意见重写主稿、同步补充材料，并从保存输入重跑本地 TLS 和零售工具实验。

- 阅读：`pdf/main.pdf`（18页：13正文＋1附录＋4参考文献）；`pdf/supplement.pdf`（14页）。
- 修订说明：`REVISION-RESPONSE.txt`，逐条对应 A1–A16、B1–B21，并列出没有补做的研究。
- 编辑：`manuscript/main.tex`、`manuscript/supplement.tex`。
- 当前实验：`experiments/reviewer-audit/`；脚本、逐单位结果、预测、区间及混淆矩阵均保留。
- 文本差异：`provenance/manuscript.patch`；原稿备份：`provenance/pre-review-manuscript.zip`。
- 历史证据：`evidence/retained-release007/`和`experiments/revision-m1-m8/`保持历史内容，不能用其中旧摘要覆盖本轮修正。

## 第二轮修订（2026-10-21，`test` 分支）

- 新增 `experiments/sp2027-r2/`：E5 流式发射器（TLS 1.2/1.3）、E6 随机化 cover 与策略感知攻击者、E7 加密 agent–tool 链路组合，以及实验前提交的 7 条审计判断（`PREREGISTRATION.json`，commit `16f6254`）。结果为 5 条证实、2 条部分证实、0 条被推翻。
- 主稿第 8 节改写为 “Controlled Transfer Tests”（Table 10–12）；第一轮受控实验完整表格移到 Supplement S11，E5–E7 全部区间在 S12。
- 审稿意见与修改清单：仓库根目录 `docs/R2-SP2027-审稿与修改清单.md`。
- 校验：`python -B experiments/sp2027-r2/verify_r2.py`（仅用标准库）。
- 复跑：需要 scikit-learn 1.9 和 tiktoken（o200k_base），命令见 `experiments/sp2027-r2/README.md`。
- 仍未完成：独立盲法人工编码、匿名公开仓库、自主 Agent 实验，详见清单 B 类。

## 关键改动

T2/T3匹配成本为2.30×/1.43×；训练集定cap为2.18×。旧0.87×/0.91×跨工作负载分母已撤回。
工具测试多数类基线77.55%；取消计数及已知插入位置攻击为100%，撤回隐私—效用前沿主张。
DB、完整账户和reference-changed对象指标分列。39记录覆盖26个家族；20是报告审计家族数。
24场景仅作作者构造示例，不再宣称独立有效性或64.6pp优势。

## 校验与复算

只读校验（Python标准库，不调用模型、不重跑实验）：

```text
python -B verify_package.py
python -B verify_revision.py
```

当前实验重算需要Python 3.10+、numpy、cryptography、pydantic；只运行本地socket和公开模拟数据。

```text
python -B experiments/reviewer-audit/recompute.py tls
python -B experiments/reviewer-audit/recompute.py retail
python -B experiments/reviewer-audit/recompute.py scenarios
```

零售重跑约数分钟，保存6210条任务/种子/位置/策略记录；TLS随机padding包含首次socket及其余49次记录核算。
重跑会更新输出，随后需要更新SHA256清单；原始交付清单是本次保存版本的凭据，不是未来重跑的通用哈希。

LaTeX使用IEEEtran 1.8b conference,compsoc。进入manuscript，分别运行pdflatex、bibtex、pdflatex两次。
当前PDF已编译并检查，无未定义引用/标签和overfull box。日志保存在provenance/build-logs。

## 证据范围

没有自主Agent联合实验、TLS1.3/QUIC/时序攻击、外部独立场景、真实MCP/API普查或新增人工编码。
本包是本地可复查材料，不是匿名线上发布凭据，也不保证论文录用。匿名仓库及作者级来源确认仍需完成。
