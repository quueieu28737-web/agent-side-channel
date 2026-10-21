# agent-side-channel

论文第三轮审稿修订版（2026-10-21）：结果记录审计与受控边界案例。案例不作为审计准确率或外部有效性验证。

## 当前版本

- 最新阅读文件：main.pdf、supplement.pdf。
- 完整修订包：paper-review-revised-20261021.zip，与目录和 PDF 同步。
- 修订说明：docs/R3-证据与评估修订说明.txt；包内 REVISION-R3.txt。
- 最新分析：包内 experiments/sp2027-r3/，含训练折工具识别、184 组折外预测、逐次重取攻击器最大值的 bootstrap 区间和训练模板溢出审计。
- P5 目前支持已有泄漏持续；P7 不建立两个目标的联合保护。撤回用判断命中数证明审计有效性的叙述。
- 尚缺真实 LLM planner、训练专用防御校准的效果重跑、独立人工编码、外部正反例与简单基线。

## 目录与版本

| 路径 | 内容 |
| --- | --- |
| final-paper-and-experiments-20261021-m1m8-revised/ | 当前完整包，含源码、实验、历史证据和来源清单 |
| paper-review-revised-20261021.zip | 当前完整修订包 |
| final-paper-and-experiments-20261021-m1m8-revised.zip | 历史输入快照，不是当前修订稿 |
| docs/R2-SP2027-审稿与修改清单.md | 第二轮历史审稿与修改记录 |
| 修订说明.txt | 第一轮历史修订说明 |

第二轮 test 内容已在 main。E5 为 TLS 1.2/1.3 流式发射器，E6 为随机 cover，E7 为加密 agent–tool 链路。注册 commit 为 16f6254。原始注册、观测和 outcome 文件保留；当前解释及 E6/E7 区间以 R3 为准，不累计历史 outcome 标签作为有效性指标。

## 校验与复算

进入完整包内 final-paper-and-experiments-20261021-001：

    python -B verify_package.py
    python -B verify_revision.py
    python -B experiments/sp2027-r2/verify_r2.py
    python -B experiments/sp2027-r3/verify_r3.py

前三项使用标准库；R3 需要 numpy / scikit-learn，版本见其 README。最终结果在包内 experiments/sp2027-r3/validation.txt。

R3 重算顺序：

    python -B experiments/sp2027-r3/reanalyze.py
    python -B experiments/sp2027-r3/make_tables.py

重算不调用模型 API，使用 R2 保存观测重新拟合固定分类器。R2 原实验复跑命令见其 README。重算后需要重编 PDF 并更新来源和 SHA256 清单。

## 编译

LaTeX 使用 IEEEtran 1.8b，conference, compsoc。在 manuscript/ 中分别对 main 与 supplement 运行 pdflatex、bibtex、pdflatex 两次。当前 PDF 与日志均保存在包内。

根目录 prepare_revision.py、revise_manuscript.py、build_revision_tables.py、finish_retail_revision.py、finalize_text.py、package_revision.py 为第一轮历史脚本，不能用来覆盖当前修订包。
