# R7：主稿 Table 8 中 NR-V 格逐项复核

复核日期：2026-10-24（Europe/London）  
复核角色：Luna 辅助核查；这是对仓库内作者核验记录和来源定位器的二次检查，不是外部人类盲审或独立编码。

## 最终裁定（覆盖下方初轮保留状态）

根任务复读原文并与 Luna 对照 R3/R4/R5 定义后，新增显式覆盖层 `provenance/r7-review/audit-corrections.json`：Cloud traffic benchmark 的 R3 从 NR-V 改为 Bound；Hadad 的 R4/R5 从 NR-V 改为 NR-R。**当前剩11格NR-V（R4=5，R5=6）**。Cloud的论文明确报告prompt前后插入与实际reformulation结果，已满足论文报告级placement定义；Hadad相关范围只报告padding成本推算，未报告保护条件拟合/匹配测试，故应区分“未报告”和“未核实”。这不是历史run复现或人类独立评分。旧CSV、κ和下方初轮报告保留；当前主文/补充表由覆盖层生成。

## 初轮范围和口径

主文矩阵 `manuscript/tables/family-audit-matrix.tex`；补充审计表为 `manuscript/tables/six-check-audit.tex`（Table~\ref{tab:six-check-audit}，审计口径说明见 `manuscript/sections/31-result-audit.tex`）汇总 20 个 mitigation family、180 个 R1–R9 格。表中问号对应 NR-V，即需要的 source/run/version binding 当前无法验证；它不是“论文完全没有做该实验”。逐格计数为 R3 1 格、R4 6 格、R5 7 格，共 **14 格 NR-V**。R4/R5 是对需要学习/校准的攻击尤其相关的 D1 protected-condition fit 与 D2 matched adapted test 两个不同绑定问题。

作者既有方法段记录称，作者核对并更正了 39 条结果记录、180 个审计格；这是作者核验的报告。本文件只复查 NR-V 的证据边界，不重标作者标签，也不改变主稿。`m7_dual_coding_checks.csv` 的 `coder2_independent_expert` 字段不能据此表述为外部人类盲审：本次不把 AI 工作流称为独立人类编码，也不扩展或重算 κ。

## 逐格登记

以下逐行记录每个来源结果对应的审计依据；同一 family 的多个结果定位重复落在同一个 family-level Table 8 格，不按结果数重复计格。合并后 Table 8 共 14 格。论文定位指仓库中 `experiments/reviewer-audit/combined_result_records.json` 所保存的既有 locator 元数据；旧记录声称的 `source_path` 均指向 `evidence/recent-agent-review-20261018-001/sources/...`。本包内未找到这些路径下的旧 txt/html 缓存；后续已通过 arXiv 官方 HTML 在线打开七个家族的来源版本，并按下方“公开原文复核”登记精确章节、HTML 行号和结果。下列来源与定位先列作者既有 locator，二次核对结果见后续小节。

| # | Table 8 格 | 来源与既有精确定位 | 为什么仍为 NR-V | 可解决该格的证据 |
|---:|---|---|---|---|
| 1 | R3 × `pouryousef2026traffic` | `traffic-v1.txt` locator：V-C1, Fig. 9a；既有 anchor “prompt reformulation reduces model-fingerprinting accuracy from”；derived line 532。 | 图中 prompt reformulation 的 fingerprint 结果与防护动作是否实际作用于目标生成/请求路径未绑定；结果图本身不能说明拦截或执行位置。 | 论文/补充材料明确说明 defense 的插入点和执行路径，或版本对应的代码/实验配置及 Fig. 9a 对应 run，证明防护在请求进入目标前实际执行。 |
| 2 | R4 × `whisperleak2025` | `whisper-v1.txt` locator：§6.1, Tables 3–4；anchor “new parallel data collections”；derived line 773。 | 新采集 padded/unpadded 数据、LightGBM AUPRC 的描述未把 Table 3–4 的每个报告结果绑定到防护条件上拟合的具体模型/训练划分。 | Table 3–4 对应版本的数据划分、训练脚本/配置、模型工件或运行日志，明确 train split 包含 padded/protected 条件，并绑定到所报告的行/列。 |
| 3 | R5 × `whisperleak2025` | 同上：§6.1, Tables 3–4，line 773。 | 未见 Table 3–4 的 clean 与 defense/adapted 分数是否在同一个受保护测试集上配对的 run-level 绑定；仅有并行采集的描述不足以证明相同样本/划分。 | 同一版本中 clean/adapted 两条件共享的 held-out protected sample IDs 或 split manifest、两条件评分输出及表格映射。 |
| 4 | R4 × `whisperleak2025` | `whisper-v1.txt` locator：§6.2, Fig. 7；anchor “we simulated batching”；derived line 785。 | Fig. 7 是模拟/离线 batching；现有记录将 replay fitting binding 标为 NR-V，未将具体拟合样本与图中防护结果绑定。 | Fig. 7 的生成脚本及 run 配置、用于拟合的 batching/protected traces 清单、模型工件/输出与图中曲线映射。 |
| 5 | R5 × `whisperleak2025` | 同上：§6.2, Fig. 7，line 785。 | 未确认 Fig. 7 的对照是否使用完全相同的受保护测试 trace；图/文字中的汇总对比不能单独建立同一测试集配对。 | 图中各条件共享的 trace ID/split 文件及逐 trace 预测或评分结果，标明 Fig. 7 的系列。 |
| 6 | R4 × `whisperleak2025` | `whisper-v1.txt` locator：§6.3, Table 5；anchor “Our implementation models first merging simultaneously-arriving packets”；derived line 790。 | Table 5 的 stochastic packet-generation/injection replay 结果缺少被引用的具体 protected-fit 数据、运行版本和结果行绑定。 | Table 5 对应的 packet synthesis 配置/随机种子、输入 trace、训练/拟合 split、模型及结果导出之间的可复现映射。 |
| 7 | R5 × `whisperleak2025` | 同上：§6.3, Table 5，line 790。 | 未绑定 Table 5 各对照条件是否用同一受保护 trace 集进行评估；记录明确该模式是离线随机 packet generation，但无法据此判定它有没有配对。 | Table 5 对应的 shared held-out trace/seed manifest、两条件输出和表格单元映射。 |
| 8 | R4 × `timewilltell2024` | `time-v1.txt` locator：§7.2；anchor “Provide a 60-word explanation”；derived line 539。 | 既有审计指出其对输入长度条件化阈值/分类器的拟合，尚未核实该阈值是否在防护后的分布重拟合；不能把“count-rule”当成“没有拟合”。 | §7.2 所用阈值的拟合数据/流程，证明保护条件是否进入拟合；如有代码，给出与该结果对应的 run/config。 |
| 9 | R5 × `timewilltell2024` | `time-v1.txt` locator：§7.2，line 539。 | 尚未核实防护前后是否在同一个受保护测试样本集上对比；攻击阈值拟合与测试集配对是独立绑定。 | §7.2 clean/defense 的同一 protected held-out 样本清单、阈值工件、逐条件预测/评分和表格映射。 |
| 10 | R4 × `timewilltell2024` | `time-v1.txt` locator：§7.3；anchor “necessitating an average of 67% padding”；derived line 544。 | §7.3 的 padding 结果与攻击校准/拟合样本间缺少版本和 run-level 绑定；当前定位器只确认报告段落 anchor。 | §7.3 结果对应的输入/输出样本、阈值训练集、padding 配置及输出表格的可追溯 run manifest。 |
| 11 | R5 × `timewilltell2024` | `time-v1.txt` locator：§7.3，line 544。 | 未确认该 padding 对照的两条件评估是否沿用同一受保护 held-out 样本，故无法判断差值是 matched adapted test。 | clean 与 padded 条件共用的 held-out ID/split 记录、评分明细和 §7.3 汇总映射。 |
| 12 | R4 × `wei2024speculation` | `speculation-v4.txt` locator：§4.2、§4.4、§6.1，Fig. 6–7/Table 2；anchor “calculated using only the token bytes and ignoring metadata”；derived line 330。 | 现有源审计确认有 Random Forest attack；但针对 REST padding 条件是否以该受保护分布重训，以及拟合结果与 reported accuracy/table 的具体绑定未验证。 | §4.2/4.4/6.1 对应 RF 的训练数据、条件划分、脚本/模型工件和 Table 2/Fig. 6–7 的 run mapping。 |
| 13 | R5 × `wei2024speculation` | 同上：§4.2、§4.4、§6.1，Fig. 6–7/Table 2，line 330。 | 未核实 clean 与 REST defense 的 RF 结果是否基于同一 protected held-out test set；8.7× 是 token-payload 比，不会回答测试集配对问题。 | 与 accuracy 结果对应的 shared held-out sample IDs/split、两条件 RF 预测或评分明细，以及表格行/列映射。 |
| 14 | R5 × `zhu2026turing` | `ahb-v1.txt` locator：§5.1.2, Table 1; Appendix E.1–E.3；anchor “task success and offline mode”；derived line 838。 | 既有检查称 released code 能按 condition refit（D1-code），但 Table 1 历史结果没有确认 clean/refit 输出在同一 held-out episodes 上配对；代码能力不等于发表结果采用了该运行。 | Table 1 每一行对应的历史运行配置、clean/refit 模型工件、episode/split IDs、逐条件预测和 Table 1 映射；单独展示可运行的代码不足以关闭此格。 |
| 15 | R4 × `chen2026sparleak` | `2609.38830-native.txt` locator：§3.1、§4–7、Table 4；source locator 元数据在 `combined_result_records.json`。 | Table 4 的 sparse-token defense accuracy 尚未绑定到防护分布上拟合的具体攻击器、训练数据和 run。 | Table 4 对应版本的训练/评估划分、模型工件、配置及逐运行结果映射，能确认是否在 sparse-token 防护条件上拟合。 |
| 16 | R5 × `chen2026sparleak` | 同上：§3.1、§4–7、Table 4。 | 未见 clean 与 sparse-token 结果所用的同一 protected held-out test binding；准确率和 perplexity 的并列呈现不是配对证明。 | 共享测试样本/split IDs、逐条件预测或评分、Table 4 数据生成和对应 run。 |
| 17 | R4 × `hadad2026shape` | `2603.25403v1.txt` locator：§IV、V、VII、VIII、IX；source locator 元数据在 `combined_result_records.json`。 | 在线读取 arXiv:2603.25403v1 后，§VII-B/C 给出攻击数据与结果；§IX-B1 仅提出 constant-work padding，并从已测的 49s/111s 推出 126% latency estimate。所读原文没有显示防护条件下的重拟合 run，也没有 paired protected held-out test；这是来源可读但证据未报告/未绑定，不是获取受阻。 | §V/VII 的拟合/攻击方法原文及相应数据划分/run；如只报告固定攻击，则需把该限制与当前 NR-V 规则区分后由作者重新裁定。 |
| 18 | R5 × `hadad2026shape` | 同上：§IV、V、VII、VIII、IX。 | 解析 padding overhead 不提供攻击效果的 matched-test 证据；也未能从包内原文材料确认两个条件的测试集是否共享。 | 同一 protected test sample/trace ID 清单、clean 与 defense 预测/评分输出及论文中对应结果位置；若原研究无此配对，则保持 NR-V 或由作者依规则重新分类，而不推定结果。 |

## 公开原文复核（2026-10-24）

公开来源均成功/受阻状态和逐格裁定另存于 `provenance/r7-review/nrv-public-source-verification.json`。直接阅读的是 arXiv 官方 HTML：Whisper Leak [§6.1/Table 4](https://arxiv.org/html/2511.03675v1)、Time Will Tell [V-B、VII](https://arxiv.org/html/2412.15431v1)、Speculation [§4.4/Appendix D](https://arxiv.org/html/2411.01076v4)、Traffic Benchmark [V-C1/Fig. 9](https://arxiv.org/html/2609.31877v1)、AHB [§4.3、§5.1/Table 1](https://arxiv.org/html/2604.09574v1)、SparLeak [§7.1/Table 4、§7.5](https://arxiv.org/html/2609.38830v1)、Shape and Substance [§VII、§IX-B1](https://arxiv.org/html/2603.25403v1)。以下“足以关闭”按 Table 8 所要求的结果绑定严格判断；读取到了相关论述不等于查到了对应历史 run。

| Table 8 格 | 本轮读到的直接来源证据 | 是否足以关闭 | 未关闭原因/来源状态 |
|---|---|---|---|
| R3 × `pouryousef2026traffic` | V-C1 明确将 prompt rewrite 定位为 application/model-level，并说明 LLMmap 在原 prompt 前后插入 execution-trigger instructions；Fig. 9(a) 报告重写/温度变化下的准确率（HTML 261–273）。官方 [GitHub repository](https://github.com/IQSeC-Lab/AI-Traffic-Analysis) 可读。 | 否（支持高层 placement） | 原文能说明被测 prompt-level 位置，不足以单独核实 Table 8 所要求的请求执行/dispatch run binding；当前公开仓库也未将具体 Fig. 9(a) 的 classifier、fold 与运行输出绑定。原文与 repo 可得，精确 run 绑定缺失。 |
| R4 × `pouryousef2026traffic` | 同 Fig. 9(a)。 | 否 | 4-fold 分组评估是可见的，但论文没有说明 attack model 是否在 reformulated/protected distribution 重新拟合；没有具体 fitted model/data split 与结果行绑定。原文可得，受保护拟合证据未报告。 |
| R5 × `pouryousef2026traffic` | 同 Fig. 9(a)。 | 否 | 4-fold 描述未给出防护/基线共用的 held-out prompt IDs 或逐样本成对结果。原文/数据采集 repo 可得，matched-test IDs 未披露或未与图绑定。 |
| R4 × `whisperleak2025` | §6.1 说使用新采集的 obfuscation on/off traffic，Table 4 为 LightGBM 五次试验中位数 AUPRC；§6.2 batching 是模拟；§6.3 injection 是基于 capture 的合成/回放（arXiv HTML 321–337、342 起）。[作者 GitHub repo](https://github.com/yo-yo-yo-jbo/whisper_leak) 公开 benchmark code 的当前主分支 around `whisper_leak_benchmark.py` lines 486–507 是先对全表实施 mitigation，再 split。 | 否 | 公开代码足以显示一个通用现行 pipeline 会在 mitigation 后切分/拟合，但未钉住 arXiv v1 的 Table 4/Fig. 7/Table 5 历史 commit/config/run。因此不升级到“发表结果已证明 protected-fit”。来源可得，版本—run 绑定缺失。 |
| R5 × `whisperleak2025` | 同上；Table 4 只报告 median across 5 trials，Fig. 7 也汇总 5 trials；§6.3 介绍随机 packet replay。 | 否 | 正文及当前 repo 未列跨 clean/mitigation 共享的 held-out trace/sample IDs，也未给逐 trial 同 trace 评分映射。原文可得，paired-test 证据未报告/未绑定。 |
| R4 × `timewilltell2024` | V-B lines 218–225 明示 attack profiling 用每类 100 个已知输入拟合 input-length-conditioned threshold；VII-B/C 讨论 tokenizer/system/prompt defenses，§VII 的 padding 段给 overhead 估计。 | 否 | 清楚的 clean-profile 流程不是 defended refit；未发现对 padding/protected distribution 重拟合并对应至所报结果的 run。原文可得，相关实验未报告。作者可以按既定 R4 规则另行审议 NR-V/NR-R。 |
| R5 × `timewilltell2024` | 同上；source 提供 profiling/test 的概念划分，但对 mitigation 主要报告 padding overhead。 | 否 | 未发现 padding 前后同一 protected held-out input/test-set 的攻击结果比较或 ID manifest。原文可得，matched comparison 未报告。 |
| R4 × `wei2024speculation` | Appendix D Table 2 明确报告 fixed/random padding 下的 attack accuracy；说明 20 traces per prompt、temperature 0.8 和 payload overhead（HTML 721–743）。 | 否 | 可核实存在防护条件下的 accuracy 数字，但未说明 RF 是否在 padded protected data 上训练/重拟合，且无模型工件到 Table 2 行的绑定。原文可得，protected-fit 细节缺失。 |
| R5 × `wei2024speculation` | 同 Table 2；正文另描述 Experiment 1/2 known prompts 与 Experiment 3 train/test prompt 分开（§4.3、lines 152–155）。 | 否 | 同一 prompt set 不等于同一受防护 held-out traces；Table 2 没有标明 no-padding 与 padding 使用共享 test trace IDs。原文可得，matched-test binding 未披露。 |
| R5 × `zhu2026turing` | §4.3 将 external wrapper 说明为执行前把 raw actions 转换为 humanized actions；§5.1.2 区分在线真实执行和离线 post-hoc 修改；Table 1 同列报告检测与 task accuracy（HTML 236–251、264–280、326–340）。官方 [AHB code repo](https://github.com/Gebro13/Passing-the-Turing-Test-on-Screen-Agent-Humanization-Benchmark) 声明公开分析/采集代码。 | 否 | 原文确认 mode 与结果表，但没有共享 held-out episode IDs/逐 episode paired detector outputs。公开 repo 有分析 notebook但未在所读文件中找到绑定至 Table 1 的 historical episode manifest。原文与代码可得，paired output/ID 绑定缺失。 |
| R4 × `chen2026sparleak` | §7.1 line 294 报 8:1:1 sample-disjoint split；§7.5 lines 308–315/Table 4 说明 inference 时以随机 token 替换并报告 ASR/ROUGE。 | 否 | 8:1:1 是主攻击评估的 split 描述；Table 4 没写该 attack model 是否对 mitigation 条件重新训练。原文可得，mitigation-to-fit binding 未披露。作者声明公开匿名工件，但本轮直接打开 artifact 页面失败，因此代码/文件获取受阻。 |
| R5 × `chen2026sparleak` | 同 Table 4，baseline 和 10/20/30% perturbation 结果并列。 | 否 | 表格未声明 perturbation 各条件与 baseline 共用同一 held-out query/test IDs；匿名工件网页本轮不可访问，无法用工件补充核验。原文可得，paired IDs 缺失；代码工件访问受阻。 |
| R4 × `hadad2026shape` | §VII-B/C 可读攻击与数据/实验结果；§IX-A–B1 lines 370–387 讨论 countermeasure 并提出 constant-work padding，126% 是由 measured 49s/111s 推导的 latency estimate。 | 否 | 该 mitigation 定位是建议/估算，未见 protected-condition fit 实验。原文可得，但没有相应实验证据；作者应考虑既有规则下 NR-V/NR-R 的分类。 |
| R5 × `hadad2026shape` | 同 §IX-B1。 | 否 | 126% overhead 推算不是 attack outcome 对比；没有 defended attack run 或共享 held-out test IDs。原文可得，但 matched-test 实验证据未报告。 |

**初轮逐格结论：14/14 格暂保留；最终三格修正见文首。** 公开来源读取成功的家族为 7/7；公开原文可读但缺少所需的 protected-fit、matched-test 或历史 run 映射是主要障碍，不再将这一轮描述为“只能因本地缓存缺失而无法检查”。SparLeak 匿名工件网站的直接访问失败，是唯一记录的外部工件获取受阻项；这不影响按可读论文保留 NR-V。旧 Table 8 标签、审计状态和计数均未修改。
## 本次可解决性与计数

在当前工作区里，以上 18 条来源结果明细汇总到 **14 个 family-level Table 8 格**：Whisper Leak 三种结果共用该 family 的 R4/R5 格，TimeWillTell 两个结果段共用该 family 的 R4/R5 格；其余 family 分别对应其所列 R4/R5 格。总计 R3=1、R4=6、R5=7。旧版 source-cache 路径仍不在包内，但本轮已从公开来源成功读取七个来源家族的 arXiv HTML。逐格核查发现，若干论文给出 mitigation 结果，或明确说明 offline/online 模式；但没有找到把相应结果绑定到 protected-condition fit 的具体模型/数据，或绑定到同一 protected held-out sample/trace IDs 的材料。因此所有 NR-V 均保持未关闭。对于论文只提出防护而未报告受防护攻击试验的 R4/R5 格，原文可读但相关实验证据未报告；作者可按现有规则判断应为 NR-V 还是 NR-R。本轮不改审计标签。逐项所需材料见上表。

复核采用的仓库文件：

- `manuscript/tables/family-audit-matrix.tex`：主文 family 审计矩阵。
- `manuscript/tables/six-check-audit.tex`：补充材料中的 R1–R9 审计计数表。
- `manuscript/sections/31-result-audit.tex`、`manuscript/sections/03-methodology.tex`：审计定义与作者核验/统计报告口径。
- `experiments/revision-m1-m8/m6_split_checks.csv`：180 格展开表和每格摘要。
- `experiments/revision-m1-m8/m7_dual_coding_checks.csv`：既有 coder/adjudication 标签记录；不据其 `coder2` 字段主张外部人类盲审。
- `experiments/reviewer-audit/combined_result_records.json`：已存 locator、source path、anchor、derived line 与 D1/D2 binding 状态。

没有发送邮件，没有改主稿、旧实验文件或清单，也没有提交 Git 变更。初轮报告的历史计数为 R3=1、R4=6、R5=7，合计14；最终覆盖层已将其中3格修正，当前合计11。






