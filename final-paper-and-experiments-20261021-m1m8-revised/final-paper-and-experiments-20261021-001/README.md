# Agent side-channel SoK — Defense Transfer Boundaries

当前版本以 **防御效果的迁移边界** 贯穿全文：发射器、执行状态、校准客户、攻击观察、评估环境与模型迁移。82 族地图、39 条记录和九项审计服务于这一主线。

- 主稿 21 页，正文在第 13 页进入 References；Appendix D 纳入完整 82 家族、六轴 holdout 证据矩阵。
- 补充材料 61 页，含迁移矩阵、配对区间、100 次实时 planner 结果及新增 S27/S28 全量记录/holdout 综合。
- Sol 690、Luna 150、MiniMax 115、GLM 115 原始正式运行独立保留；后验 R14 有 690 次新 TLS 捕获，R15 有 100 次新 planner 运行。
- 保留 R13 的 WAN 延迟/抖动扩展及所有历史实验，不静默覆盖原实验结论。

## 核心结果

MiniMax 校准迁移到 GLM 时，取消/退货 BA 从目标模型自身校准的 50.0/67.3% 变为 70.8/50.0%。仅写整形以 1.45/1.51× 字节留下 61.3/61.6% 退货 BA。实时 prefix-shadow 与基线成功数为 33/50 和 37/50，差值区间跨零；不作效用无损结论。可变别名、已知客户及局部机制范围均随结果披露。

最新 R18 基于 manuscript-channel-side 的合并提交 `225c5fe` 重建，保留修订结构，修正配对审计分母、holdout 未解决状态表述与 GLM 降幅舍入；相关数据和 PDF 校验位于 `provenance/r18-merged-manuscript/`。

## 复现与校验

从发布包目录运行 `python verify_package.py` 可只读验证完整清单、历史数据及源码/PDF来源绑定。当前系统化修订的生成器、逐项编码、来源摘录与校验收据位于 `provenance/r16-synthesis/`；历史实验发布收据保留于 `provenance/r11-review/`。论文和补充材料分别以 `manuscript/main.tex` 与 `manuscript/supplement.tex` 构建。

当前匿名论文源码包为 `provenance/r18-merged-manuscript/anonymous-paper-source.zip`。它不包含开发 Git 历史；完整实验的匿名托管需按投稿流程另行提供。矩阵综合已有来源绑定提取，未解决的轴明确记为 ?，不被计作原论文未报告。

[主稿](pdf/main.pdf) · [补充材料](pdf/supplement.pdf)
