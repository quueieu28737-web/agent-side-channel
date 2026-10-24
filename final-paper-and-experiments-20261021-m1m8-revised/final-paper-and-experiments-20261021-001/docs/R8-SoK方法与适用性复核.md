# R8 SoK 方法与适用性复核

## 审查范围

只读检查了 `manuscript/sections/03-methodology.tex`、`27-intervention-contracts.tex`、`01-introduction.tex`、`tables/six-check-audit.tex`，以及历史 `evidence/retained-release007/history-release006/decision-audit/{RULES.txt,six-checks.csv,semantic-coding.csv,coding.json,summary.json}` 和当前 `provenance/r7-review/audit-corrections.json`。旧 CSV、历史 κ 和主稿均未修改。本复核是源码/账本审查，不是独立人类复核。

## 三项批评的裁定

### 25/60 的分母

`03-methodology.tex` 写的是“query set overlaps 17/24 selected seed papers and 25/60 earlier indexed families”。所以 25/60 是六条 Boolean 检索式与**先前60个已索引家族**的词面交集，不是25个研究占60个纳入研究，也不是对某个总体的召回率。60是历史快照的家族数，现有文稿明说抽样为 purposive，且检索路线还包括种子、定向会议筛查及引文追踪。它只能支持“这些查询单独覆盖不全，因而使用互补发现路线”；不能支持 recall、敏感度或领域覆盖率。建议文中始终称为 query overlap/recovery，不简称“42%覆盖率”。

### R5：适用性有明确边界，适用不等于历史论文必须做自适应实验

R5 是“匹配的自适应测试”证据项；若攻击者是可拟合/校准的学习器，防护改变观测分布时，protected-fit 与 matched protected-test 对抗性复用判断有意义。它不应泛化为任何固定变换、解析成本推算、硬件隔离或无学习器的访问控制都欠缺一次 refit。原六项审计的 C4 本来就写明“when an adaptation inference is at issue”，并区分 NA 与 NR-V；这提供了可辩护的适用性敏感性定义。

此前生成的 `applicability-sensitivity.json` 是用旧C4做16家族适用性近似，不是新版R5结果；下面完整overlay已从20行主文矩阵直接解析，并作为当前计数依据。

### 20家族九项分布与R5分母核验

新建 `provenance/r8-review/family-status-overlay.csv/.json` 和生成器 `build_overlay.py`。脚本从主文矩阵20行逐格读取B/P/U/?/--，映射为 Bound/Partial/NR-R/NR-V/NA，断言每项分布总和为20。R1–R9分布依次是：R1 20/0/0/0/0；R2 17/3/0/0/0；R3 17/3/0/0/0；R4 4/1/1/5/9；R5 2/2/1/6/9；R6 18/2/0/0/0；R7 17/1/2/0/0；R8 3/3/11/0/3；R9 11/3/5/0/1（顺序均为 Bound/Partial/NR-R/NR-V/NA）。

R5不是19格。原表确有 **NR-R=1**，表格行已写作 `0 (1)`；完整合计为 2+2+1+6+9=20。R5可适用分母是20减9个NA=11；2/11只表示有2个家族在其适用范围内绑定了匹配自适应测试。另有2 Partial、1 NR-R、6 NR-V。NR-R是范围内未报告；NR-V是必要绑定尚未核实；两者都不应写成“未做”。更窄的“仅要求对明确可学习/可校准攻击作matched adaptation”口径，可额外将 Shape and Substance 从适用集移至NA，给出2/10（其它10族保持原状态）；但这是一项定义敏感性，不能覆盖主表原口径。R5所有20族逐格理由见 `family-status-overlay.json` 的 `R5_reason`。

R5逐族适用性/证据理由：

| 家族 | R5状态 | 理由摘要 |
|---|---|---|
| UI Traces | Bound | 在线动作扰动/防护条件有适配攻击与同条件结果绑定。|
| WRA | NA | 诱饵工具执行/意图保护不以学习攻击器的受保护分布refit为该项复用主张。|
| NetEcho | Partial | 有学习器和防护变换；matched held-out adaptation绑定不完整。|
| Early Bird | Partial | 攻击用K条件校准；校准与防护后同测试集的对应关系不完整。|
| Whisper Leak | NR-V | 已说明长度条件阈值攻击；防护后拟合/匹配测试的版本运行绑定未验证。|
| SpliceLeak | NA | QCP/缓存隔离组件评估不是学习攻击器的自适应防护对照。|
| Time Will Tell | NR-V | 阈值攻击存在；padding/指令前后匹配与拟合绑定未核实。|
| I Know What You Said | NA | 关闭zero-copy是系统机制控制；不是学习分类器适配对照。|
| Speculative decoding | NR-V | 随机森林攻击明确；防护条件训练及同一受保护测试集绑定未核验。|
| Dangol workflow | Bound | capture子实验报告自适应fit/test；不把该结论外推到独立live OHTTP条件。|
| Cloud traffic benchmark | NR-V | prompt重写下有分类器结果，但protected-fit与匹配测试绑定未核验。|
| Remote timing | NA | 固定速率解析成本/流量分析不是学习攻击器再训练主张。|
| TDXRay | NA | oblivious lookup机制/微基准无学习攻击适配比较。|
| SafeKV | NA | 确定性缓存隔离/窗口控制，不是学习分类器的适配测试。|
| AHB/Turing | NR-V | 可重训攻击器存在；表中发布结果对应训练工件及匹配测试绑定未完成。|
| KV-Gov | NA | 命名空间分离、分析裁判及成本微基准，不是自适应分类器对照。|
| CachePrune | NA | 固定缓存淘汰机制的效用/成本测试不主张学习攻击器refit。|
| OTRO | NA | tokenizer策略/机制替换，没有适配攻击器对照。|
| SparLeak | NR-V | 学习攻击器评估存在；防护拟合与matched-test绑定待核。|
| Shape and Substance | NR-R | 检查范围报告固定/解析padding成本建议；未报告该项所需的protected-fit/matched-test对照。|

### R8两种utility estimand

宽口径R8是矩阵原定的“task **or component** utility”：Bound 3、Partial 3、NR-R 11、NA 3，适用分母17，完整绑定率3/17；14/17为部分绑定或检查范围未报告。窄口径仅问“部署任务效用”，将 TDXRay 的词表覆盖/查表功能utility移至NA：Bound 2、Partial 3、NR-R 11、NA 4，分母16，2/16。这里没有把11个NR-R升级成实验失败；改的是适用对象。脚本把两种口径及逐家族九格状态全部写入JSON。

R8逐族理由（宽口径）：UI Traces—离线归因的用户任务效用未报告；WRA—分离报告的可见性代理与诱饵任务效用未完全匹配；NetEcho—主题识别不是用户任务效用；Early Bird—语义缓存组件开销不是端到端效用；Whisper Leak—回放规模代理不等于任务效用；SpliceLeak—QCP成本是组件指标、未给任务效用；Time Will Tell—分析padding开销无受保护任务效用；I Know—NA，关零拷贝的组件成本并非此类任务效用问题；Speculation—NA，token payload是资源成本不是效用；Dangol—工作流恢复与bytes/latency存在，客观任务策略效用未报告；Cloud traffic—语义保持是断言、未做客观任务测量；Remote timing—速率成本曲线没有匹配任务效用；TDXRay—查表与词表覆盖是组件utility（窄任务口径NA）；SafeKV—检测器与服务性能分开测量，任务utility未报告；AHB—在线条件有任务正确率（Bound）；KV-Gov—模拟ASR/硬件差距/HMAC成本不是一项共同的任务utility（NR-R）；CachePrune—QA F1/摘要ROUGE等下游utility绑定（Bound）；OTRO—NA，机制不定义可比较的任务utility；SparLeak—ROUGE结果是局部摘要代理，非自治工作流utility（Partial）；Shape and Substance—防护下医疗/文档客观任务utility未报告。

### 参考文献形态盘点

`publication-form-labels.csv` 保留R1–R9的20族子表，`all-citations-form-labels.csv` 列出编译后 `main.bbl` 中全部77条实际引用。类别分布：arXiv-only 49；venue-labelled 15；venue-labelled-with-preprint 5；book 1；standard 2；vendor-doc 4；unknown 1。审计20族子表自身分布：arXiv-only 16、venue-labelled 3、venue-labelled-with-preprint 1。unknown是 `jiao2025llmwfin` 的bib entry type缺失，但bbl明确列出 *Electronics* 14(7), 1263 和 DOI，因此归 venue-labelled；类别按渲染条目而非 entry type 优先。这里仅盘点稿件参考文献**如何呈现**，不是出版状态认证；arXiv-only标签不证明未发表，venue label也不认证评审过程。`build_overlay.py` 基于当前 `main.bbl`、refs bib文件与保守类型/字面标签分类，未联网穷查77篇。

对支持跨记录例子的八篇材料，另按要求查官方页面，详细记录在 `provenance/r8-review/official-source-status-checks.json`（日期2026-10-24）。结果限于所查页面：WRA 官方 USENIX Security '26 页确认收录；Early Bird 官方 IEEE Xplore 索引页显示 TIFS 2025、第20卷、页11431–11446及2025-10-17出版日期（网页本身因JS/机器人拦截无法直接打开，元数据来自官方搜索结果）；NetEcho、SplitDecoy、AHB/Turing、Dangol、CachePrune、OTRO 的官方 arXiv 页显示其引用版本/修订时间，但未在这些页面发现 venue 引用。对后六者只能写“本次限定检索找到 arXiv 页面、未独立确认venue”，不能据此断言“仍是预印本”或无正式发表。尤其 CachePrune 有同名异作，核对按本稿 `wu2026cacheprune` 的题名与 arXiv:2605.23640，而不是另一篇同名 prompt-injection论文。

### R8：应把组件效用与部署任务效用分层

新版定义为“task or component utility”，因此硬件/微基准家族不该仅因没有用户任务成功率就被全局判 NA：TDXRay 的词表覆盖与查表开销、I Know 的加载/内存代价，均可作为组件层效用/代价证据，但不能推成端到端任务效用。KV-Gov 的模拟 ASR、HMAC成本与硬件间隙是不同测量对象；不得合成一条防护前沿。反过来，代理分数也不能自动升级为任务效用：检测准确率、内容分类准确率、语义保持断言分别不是用户任务成功。

`27-intervention-contracts.tex` 当前明确报20家族中3个 NA，故 R8 的分母为17；Bound 3/17，另有 Partial 3、NR-R 11，即适用家族中14/17没有完整绑定“同一工作点上的效用”。NR-R表示审阅范围没有报告所需结果；不是已证明不存在结果。若把问题改成“是否测到部署任务效用”，组件微基准可在该**窄问题**下记为NA，但这会改变 estimand 与分母，不能沿用3/17而不重算所有家族。审查的16家族基线中，I Know 与 TDXRay明确有组件效用子字段；脚本把它们与部署任务效用分开列出，没有重写原标签。

## 三个跨记录的非显然边界

这些例子由历史账本中的 `target_object`、`receiver`、`endpoint_definition` 与论文威胁角色直接推出；它们说明为何不能把某一记录的数值/机制原样迁移到另一记录，不表示两篇工作互相验证。

1. `WRA-decoy-execution`（Jeong，§§8.1–8.3，Tables 8–11）观测带URL/域名的目的地序列，目标是私人意图重建，且防护可执行诱饵操作；`NET-upstream-local`（NetEcho，§IV-C–E）观察包长/时序恢复话题。二者虽都归入 traffic-envelope，接收字段、目标和行动后果不同；topic BA 或填充开销不能直接预测意图诱饵的效用/成本。
2. `UI-delay-offline` 的来源是归档站点事件，目标为模型身份归因，时间戳变换为离线处理；`AHB-online-executed` 是面向平台检测器的在线行为人性化/规避。相似的“延迟/行为”措辞不意味着同一方向：归因防护的可接受结果与规避检测的策略效用相反，离线收益不能证明在线执行安全或保持任务效用。
3. `GAO-zero-copy-off` 是同机无特权共享页探测者对本地内存/输入输出文本的推断；`TDXRAY-oblivious-map` 是恶意 hypervisor 观测页行为、替换 token-to-ID 查表。二者都属 local-memory，但接收者权限、泄露原语及干预位置不同。I Know 的加载延迟/内存开销不可作为 TDXRay 的端到端推断成本，反之亦然。

这些结论的具体单元ID、接收者及来源URL/hash可在 `decision-audit/semantic-coding.csv` 对照；记录仅支持源限定比较，不支持普遍迁移率。

## 编码可靠性、Origin A/B 与出版状态

历史 `RULES.txt` 已明确旧 decision-audit 是回顾性 AI 辅助审计、并非独立人类编码，且其协议与新版 R1–R9 不同。主稿方法段说明作者核验39条结果记录/180个历史审计格，所列 κ 是“初始AI草稿—作者核验”的非独立一致性统计；它不能称独立 inter-rater κ。该区分已写在主稿，审查未发现应将其改称独立盲审的依据。审核流程可被他人复查，仍不等价于独立复现或双人裁决。

对 Origin A/B 不应做过强推论：来源层分类只有在信号来源、receiver 的可见字段和威胁极性都对齐时，才支持相应的跨记录比较。分类不自带因果识别，也不表明某一来源“导致”某种泄漏或防护有效。上面的三组反例表明同一宽泛起点（网络、行为、内存）能对应不同目标/权限/效用方向。新颖性应表述为系统化的证据绑定/比较框架，不是首次发现这些来源或提出新的因果定律。

账本为所引材料固定了 arXiv版本或官方会议PDF URL、章节定位和SHA；这能说明被审阅的是哪个文本快照，但不能单凭 arXiv ID 推断其最终出版状态。此次只读复核没有逐项核实所有家族的出版商目录，因此不报告全体的预印本/已发表比例。若需要这项比例，应另以官方会议/期刊目录逐篇核实，保留查询日期和标识符；不要从年份或引用键推断状态。

## 文件和可复算性

`applicability-sensitivity.py` 只读取历史六项审计CSV，输出同目录JSON；运行命令：`python provenance/r8-review/applicability-sensitivity.py`。它校验16个家族各有6条记录，输出 family ID 映射、分母和状态数。无旧数据、manifest、主稿或Git状态变更。
