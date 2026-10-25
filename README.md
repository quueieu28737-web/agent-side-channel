# Agent side-channel SoK — Defense Transfer Boundaries

当前版本以 **防御效果的迁移边界** 贯穿全文：发射器、执行状态、校准客户、攻击观察、评估环境与模型迁移。82 族地图、39 条记录和九项审计服务于这一主线。

- 主稿 20 页，正文在第 13 页进入 References；Appendix D 纳入完整 82 家族、六轴 holdout 证据矩阵。
- 补充材料 66 页，含迁移矩阵、配对区间、100 次实时 planner 结果及S27/S28 全量记录/holdout 综合及 S29 的 351 格记录级审计。
- Sol 690、Luna 150、MiniMax 115、GLM 115 原始正式运行独立保留；后验 R14 有 690 次新 TLS 捕获，R15 有 100 次新 planner 运行。
- 保留 R13 的 WAN 延迟/抖动扩展及所有历史实验，不静默覆盖原实验结论。

## 核心结果

MiniMax 校准迁移到 GLM 时，取消/退货 BA 从目标模型自身校准的 50.0/67.3% 变为 70.8/50.0%；历史名义配对区间分别为 [-12.6,35.3]/[-38.2,-5.3] 个百分点；R21 的客户配对置换检验与八重 Holm 校正未确认方向性差异，字节/调用成本从 15.95/4.24× 增至 18.65/4.66×。仅写整形以 1.45/1.51× 字节留下 61.3/61.6% 退货 BA。实时 prefix-shadow 与基线成功数为 33/50 和 37/50，差值区间跨零；不作效用无损结论。可变别名、已知客户及局部机制范围均随结果披露。

R19 完成全部 39 条记录的 741 对比较与 351 格审计，把同配置联合绑定、8 个配对迁移区间、字节/调用成本及部署决策表纳入主文；修正 SparLeak 组件效用编码。校验与生成器位于 `provenance/r19-evidence-closure/`。

R20 将 R1–R9 明确为具体复用主张所需的条件，并在摘要、Takeaway 2 与联合表中统一为 CachePrune 一个家族、一个配置、两个结果记录。2/20 是本集合的查询口径，不是领域普及率或论文质量评分。方法中的原作者复核流程保持不变。

最新 R21 补做 100 次训练客户重采样与 46,000 次实际本地 TLS 捕获，区分校准、攻击器重训及联合波动。原表八个目标级对比各进行 99,999 次客户配对置换，Holm 校正后均未显著；撤回“退货降低已确认”表述。主文保留原始成本/点估计并加入本地校准稳定性，完整分布与统计代码在 `experiments/sp2027-r21-calibration-stability/`。

## 复现与校验

从发布包目录运行 `python verify_package.py` 可只读验证完整清单、历史数据及源码/PDF来源绑定。当前系统化修订的生成器、逐项编码、来源摘录与校验收据位于 `provenance/r16-synthesis/`；历史实验发布收据保留于 `provenance/r11-review/`。论文和补充材料分别以 `manuscript/main.tex` 与 `manuscript/supplement.tex` 构建。

当前匿名论文源码包为 `provenance/r21-calibration-stability/anonymous-paper-source.zip`。它不包含开发 Git 历史；完整实验的匿名托管需按投稿流程另行提供。矩阵综合已有来源绑定提取，未解决的轴明确记为 ?，不被计作原论文未报告。

[R19 逐项修订与验收说明](docs/R19-记录联合审计与迁移决策修订.md)

[主稿](main.pdf) · [补充材料](supplement.pdf) · [本轮结果与验收说明](docs/R14-R15-迁移边界与实时规划器.md) · [发布包](final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/README.md)
