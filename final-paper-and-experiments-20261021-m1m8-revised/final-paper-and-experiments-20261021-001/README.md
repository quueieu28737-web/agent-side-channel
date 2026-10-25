# Agent side-channel SoK — Defense Transfer Boundaries

当前版本以 **防御效果的迁移边界** 贯穿全文：发射器、执行状态、校准客户、攻击观察、评估环境与模型迁移。82 族地图、39 条记录和九项审计服务于这一主线。

- 主稿 18 页，正文在第 13 页进入 References，附录随后。
- 补充材料 56 页，含完整迁移矩阵、配对区间与 100 次实时 planner 结果。
- Sol 690、Luna 150、MiniMax 115、GLM 115 原始正式运行独立保留；后验 R14 有 690 次新 TLS 捕获，R15 有 100 次新 planner 运行。
- 保留 R13 的 WAN 延迟/抖动扩展及所有历史实验，不静默覆盖原实验结论。

## 核心结果

MiniMax 校准迁移到 GLM 时，取消/退货 BA 从目标模型自身校准的 50.0/67.3% 变为 70.8/50.0%。仅写整形以 1.45/1.51× 字节留下 61.3/61.6% 退货 BA。实时 prefix-shadow 与基线成功数为 33/50 和 37/50，差值区间跨零；不作效用无损结论。可变别名、已知客户及局部机制范围均随结果披露。

## 复现与校验

从发布包目录运行 `python verify_package.py` 可只读验证完整清单、历史数据及源码/PDF来源绑定。分项数值/状态重构入口见各实验 README。当前发布收据位于 `provenance/r11-review/`；论文和补充材料分别以 `manuscript/main.tex` 与 `manuscript/supplement.tex` 构建。

匿名论文源码包为 `provenance/r11-review/anonymous-paper-source.zip`。它不包含开发 Git 历史；完整实验的匿名托管需按投稿流程另行提供。

[主稿](pdf/main.pdf) · [补充材料](pdf/supplement.pdf)
