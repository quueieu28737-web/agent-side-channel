# agent-side-channel

## 当前版本：R7 强化攻击、流量对照与逐项审稿修订

- [主稿](main.pdf)：正文不超过13页，全文17页；References在Appendix之前。
- [补充材料](supplement.pdf)：48页，S20为强化Timing攻击/经典WF适配/功效规划，S21为强化交叉拟合和写调用消融，S22为新增Luna研究。
- [逐项验收清单](docs/R7-逐项修改验收清单.md)：覆盖T1–T13全部40个子项，明确已完成工作与尚需外部资源的要求。
- [完整源码与数据包](final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/README.md)：当前校验、环境、归档与复算入口。

### 当前证据

1. **SoK贡献**：82个研究族、39条结果记录、58族主文映射和20×9审计矩阵。可信度来自记录与原文定位符的绑定；κ明确为非独立的提取—作者复核一致性。公开来源复核修正3个状态，仍有11个未核实绑定。
2. **主描述性结果**：原690次Sol运行的客户五折交叉拟合，53客户。11攻击器union下，标准提示组未防御BA为91.7%/85.5%，联合恒定分帧为60.5%/55.5%，联合分桶为57.1%/52.7%。配对降幅仍明确；绝对阈值未获确认。两prompt与所有运行点完整保留。
3. **Timing与成本**：E13保留4,140个实测本地工具TLS会话。E14在同一轨迹上评估13种条件、52个prompt/目标单元，增加CNN与k-FP类攻击并保留旧suite。312个新学习器已另行重训，预测逐项一致。Tamaraw、FRONT、WTF-PAD、Walkie-Talkie提供明确的RPC适配。成本图以共同7攻击器作匹配比较，另保留完整攻击并集结果；实测RPC时延与离线调度跨度分面展示。
4. **新模型实采**：另有150次正式GPT-6 Luna/low运行（75个旧retail任务×2prompt），10次试点另列。58训练/92测试轨迹、10/24个不重叠客户；每prompt攻击训练29条、测试46条。正式reward逐次在新sandbox重算，原始模型证据以可核验归档提供。它是同厂商、同环境、旧客户的补充，不替代跨厂商或新环境验证。

### 解读范围

“实验与文件校验通过”不等于“绝对安全阈值通过”。模型名称是服务返回的别名。网络结果区分原始模型轨迹、本地TLS回放、live工具执行与离线WF变换；程序条件的reward复用不等于实测live-cover重规划。规则prompt是机械读序控制。

尚未获得：第二环境、固定开源权重、不同厂商模型、新增独立阳性客户、live cover下的LLM重规划对照、两位外部盲审编码者。这些要求逐项列入清单与前瞻协议，未用重复运行或AI复核替代。

### 校验与复算

在源码与数据包目录运行：

```text
python -B provenance/r7-review/verify_publication.py
python -B verify_package.py
python -B verify_revision.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

当前入口是`provenance/r7-review/`。较早`timing/`、`review-closure/`、`sok-restructure/`中的文稿校验器绑定旧版页数与表述，保留作历史记录。详细实验重算命令及依赖见包README和各实验目录README；均不需要重新调用LLM。

### 历史保存与投稿

原690运行、663快照、R2/R3/R5/R6数据和旧ZIP发布包保留原样；它们的页数、结果表与写作说明属于相应历史版本。旧根/包README保存在本轮provenance中，避免多个版本同时标为“当前”。当前交付以本提交的两份PDF、源文件、`SHA256SUMS.json`及校验收据为准。

[S&P 2027合规核对](docs/R7-SP2027-合规核对.md)列出页数、伦理、AI披露与Open Science事项。公开Git仓库不是匿名投稿快照；作者仍需准备匿名、不可变的审稿工件并完成HotCRP身份/COI与伦理字段。
