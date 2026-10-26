# Agent side-channel SoK — Defense Evidence Transfer

当前版本按 **SoK** 组织主文：82 家族地图、39 条结果记录的完整比较审计、配置级联合绑定、六轴 holdout 综合，以及复用决策表。原 Exp 1–4 已合并为附录 E 的一个 case study，不再作为主文贡献。

- 主稿 16 页，正文共 9 页，第 10 页进入 References。
- 单个案例位于第 14 页；主文不含独立实证章节、模型对照表或校准实验数字。
- 补充材料 69 页，保留原始实验全表、统计修正、S31 详细结果和新增 S32 的案例数据登记表。

## 核心系统化结果

全量比较覆盖 39 条记录的 741 对，其中 133 对属于相关问题，17 对支持来源限定的描述性比较；15 对同家族记录中有 8 对涉及不同原语、目标或成本对象。351 格记录级审计将推断、效用和成本绑定到同一配置；2/20 联合绑定来自 CachePrune 一个家族、一个配置的两个结果。82 家族的六轴 holdout 矩阵区分各类迁移证据，复用决策表据此明确需要补充的测量。

## 案例与数据保留

发射器、执行状态、校准和观察视图被压缩为一个审计应用案例。Sol 690、Luna 150、MiniMax 115、GLM 115、100 次实时 planner，以及 100 次校准重采样/46,000 次 TLS 捕获均按原协议和统计范围保留。R21 的多重比较和训练敏感性修正保持有效；案例不替代文献审计的证据。

## 复现与校验

在发布包目录运行 `python verify_package.py` 验证完整清单、历史数据与源码/PDF 绑定；当前文稿校验为 `provenance/r23-appendix-case-study/verify_revision.py`。原方法与作者编码未改变，本轮没有新增实验或模型请求。

当前匿名论文源码包为 `provenance/r23-appendix-case-study/anonymous-paper-source.zip`，包含当前论文与补充材料的源码闭包和 PDF；完整实验匿名托管仍需提供独立快照。

[R23 校验记录](provenance/r23-appendix-case-study/verification.json)

[主稿](pdf/main.pdf) · [补充材料](pdf/supplement.pdf)
