# R7：未核实审计单元的逐项来源复核

## 当前结论

对原14个NR-V单元所涉及的七个研究族，已重新读取公开原文并核查可用工件。当前修正3格，剩余11格（R4=5、R5=6）。这次工作由Luna辅助核查、主任务复读来源并依据既有定义裁定，**不是两位外部人类的盲审或历史实验复现**。

原CSV、作者复核列和κ数值保持原样。`provenance/r7-review/audit-corrections.json`记录显式覆盖层，`audit_overlay.py --check`核对两份当前表。初轮逐条工作笔记与公开来源读取记录保存在同目录，当前表以本文件和覆盖层为准。

## 已解决的3格

| 研究族 / 单元 | 修正 | 直接依据与范围 |
|---|---|---|
| Cloud traffic benchmark / R3 | NR-V → Bound | [§V-C1、Fig.9(a)、§VI-A](https://arxiv.org/html/2609.31877v1)描述prompt前后插入指令并报告reformulation结果，足以支持论文报告层面的执行位置。R3不应额外要求历史run工件。 |
| Shape and Substance / R4 | NR-V → NR-R | [§IX-B1及§VII–VIII](https://arxiv.org/html/2603.25403v1)从未防护测量推算padding成本，未报告该提案下的攻击拟合。用“所查范围未报告”，不称“实验从未发生”。 |
| Shape and Substance / R5 | NR-V → NR-R | 同上，成本推算不构成在同一受防护测试集上的适应攻击对照。来源可读，缺少的是该项报告。 |

## 剩余11格及关闭条件

| 研究族 | 剩余单元 | 已取得的来源证据 | 尚缺的绑定 |
|---|---|---|---|
| Whisper Leak | R4、R5 | [§6.1–6.3、Tables3–5、Fig.7](https://arxiv.org/html/2511.03675v1)报告重新采集、批处理和包注入；[当前公开代码](https://github.com/yo-yo-yo-jbo/whisper_leak)可在变换后切分和拟合。 | 当前代码能力与v1具体结果之间的版本/配置绑定，以及clean/adapted对照共享受防护测试样本的证据。不能把新运行自动当作发表结果的历史运行。 |
| Time Will Tell | R4、R5 | [§VII-B/C](https://arxiv.org/html/2412.15431v1)确实报告prompt修改后的攻击成功率，另给系统padding成本估计；§V-B解释原始阈值拟合。 | prompt防护条件是否重拟合，以及两条件是否在同一受防护held-out样本上比较，仍未明确。家族中存在实际prompt实验，不能仅因padding是成本推算就把整个家族降为“未报告”。 |
| Speculative decoding | R4、R5 | [§4.3–4.4、AppendixD/Table2](https://arxiv.org/html/2411.01076v4)有padding下的攻击准确率及数据设置。 | 受防护RF拟合的具体条件、各对照共享测试trace的说明或工件。相同prompt集合不等于相同受防护trace集合。 |
| Cloud traffic benchmark | R4、R5 | [§V-C1/Fig.9(a)](https://arxiv.org/html/2609.31877v1)有prompt改写结果和总体分组评估说明；[公开仓库](https://github.com/IQSeC-Lab/AI-Traffic-Analysis)可访问。 | 改写分布上的重拟合及与该图结果匹配的测试划分/逐样本对照。R3位置已解决，不自动解决R4/R5。 |
| AHB | R5 | [§4.3、§5.1.2/Table1、AppendixE](https://arxiv.org/html/2604.09574v1)区分在线执行和离线修改；[公开代码](https://github.com/Gebro13/Passing-the-Turing-Test-on-Screen-Agent-Humanization-Benchmark)提供采集/分析能力。 | Table1历史结果中clean/refit模型在共享held-out episode上的匹配输出。R4已有代码层面的Partial状态，本轮不改。 |
| SparLeak | R4、R5 | [§7.1、§7.5/Table4](https://arxiv.org/html/2609.38830v1)给出主实验8:1:1划分及扰动结果。 | 扰动条件到拟合模型的绑定、各条件的共享测试ID。原文可读；该轮匿名工件页面访问失败，不能据此推断其不存在。 |

这里的NR-V表示**当前仍无法核实所要求的结果绑定**。没有把它当作“没有做实验”，也没有为消除问号而补造训练划分或历史预测。每格均有可关闭它的具体证据要求。

## 完成范围

- 已完成：七族公开原文复读、14格逐项处置、3格修正、当前11格计数、来源链接与可核验覆盖层。
- 未进行：给作者发邮件、取得两位外部人类盲审、复现并绑定这些论文的历史run。
- 原有空模板仅保留于不可变实验归档；对应任务已撤销，当前稿件不提供该任务入口。
