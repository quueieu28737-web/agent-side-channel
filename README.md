# Agent side-channel SoK — Reusing Defense Evidence

当前R34围绕来源中可核查的报告实践、同配置证据和部署测量计划。任务以docs/CURRENT-PLAN.md为准，历史清单不恢复已撤销任务。

## 当前综合

- 82家族地图；20家族的33条缓解记录，另6条背景记录。
- 明确推断16/17、效用4/17、匹配自适应2/11；接受P后17/17、6/17、2/11。统一14家族中推断/成本/效用为13/6/3，宽松14/10/5。
- Agent隐私/归因子集0/4明确、2/4部分效用；保护与成本明确绑定时5/8家族分属不同记录，P口径下为3/12。
- 33条缓解记录的执行型为14条；网络观察子集6执行/4变换/2位置未确认，避免误称回放占多数。
- 原记录、编码、pair判断和实验不变；新增确定性状态、适用性与成员排除敏感性。没有新增独立编码或模型实验。

## 当前交付

主稿21页，正文至第13页；补充材料81页。根目录、manuscript与包pdf副本一致。

`python tools/reporting_patterns.py`从manuscript内复算F1–F6；发布包`python verify_package.py`检查完整清单。当前文稿检查为`provenance/r34-reporting-patterns/verify_revision.py`，报告实践复算为`verify_reporting.py`。匿名源码包仅覆盖论文与补充材料；完整实验托管仍需单独匿名快照。

[主稿](main.pdf) · [补充材料](supplement.pdf)
