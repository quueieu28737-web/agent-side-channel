"""Write the Chinese R22 change and validation note from saved verification."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
v=json.loads((O/'verification.json').read_text(encoding='utf8'))
text=f'''# R22：防御证据迁移 SoK 的定位与结构修订

## 定位和贡献层级

本轮按“以防御证据迁移为主线、由受控实验支撑的 SoK”重构。核心产出是完整文献审计、配置级联合绑定、六轴 holdout 综合与部署决策。受控研究测量选定部署变化的后果，并为决策提供具体的推断、状态、效用和成本依据。

摘要、引言、Table 1 和结论统一为三步：识别可复用证据，测量具体边界变化的后果，形成最小重新评估要求。校准稳定性是受控研究的一部分，不再与“四个实验”重复并列。

## 系统综合的扩充

- §5 将 741 对全量审计的判断连接到行动：已知对象错配要求重新测量，未决绑定要求核对来源，描述性相容支持保留原分母的限定比较。
- §5 解释联合绑定的递进关系：推断＋效用 4/22，推断＋成本 5/22，适应性＋推断 2/17，推断＋效用＋成本 2/20；最后一项仍明确是 CachePrune 一个家族、一个配置、两个结果。
- §6 解释六类 holdout 各自支持的迁移主张，以及多个轴分别通过不能自动证明联合部署条件。
- §7 由“三个案例”改为“从证据到复用决策”的综合，明确记录比较、联合绑定、holdout 三个步骤，保留有选择标准的机制案例，并承接部署决策表。

## §8 压缩与主文自洽

源文本从 {v['section8_source_words_before']} 词缩至 {v['section8_source_words_after']} 词，减少 {v['section8_source_word_reduction_percent']}%。该计数按两个 §8 源文件的空白分词计算，不包含独立表格文件，不作为严格英文词法计数或页面比例。

主文保留四个研究模块、共同测量约定和 cohort 分母，以及四类关键表：冻结对照、模型内评价、校准／局部整形／训练敏感性，以及在线与离线成本对照。原始 21 张主文表收敛为 16 张。每个研究都以实际复用决策收束。

| 详细结果 | 主文安排 | 补充安排 |
|---|---|---|
| 发射器完整表 | 保留决定性数字与成本 | S12 既有完整表，S31 索引 |
| Dispatch 策略表 | 保留状态与重训关键对照 | S31 完整收录 |
| 冻结真实 Agent 表 | 四行摘要，保留区间和字节／调用比 | S31 保留双 prompt、原 reward 和配对差值 |
| Cross-fit 表 | 保留完整队列关键点与成本 | S31 完整收录 |
| Oracle 定位表 | 保留调用占比、定位与干预后结果 | S31 完整收录 |
| Flush 移除表 | 保留检测与下游推断区分 | S31 完整收录 |
| Timing 控制表 | 选择七个直接支持部署决策的点 | S31 保留全部十三行及上界 |

原七组详细表文件逐字节保持。四行冻结摘要和七行 Timing 摘要逐格对照原表验证。原始数据、协议、预测、校准、所有历史结果和作者编码均未改变；没有新增实验、模型请求或客户。

## 统计与效用口径

保留 R21 的校正：八个客户配对对比经 Holm 校正均不显著；GLM 本地 return BA 的 95% 敏感性范围是 50.0–67.9%。这些结果支持加入本地重校准基线，不支持把原始 +20.8/−17.3 点方向归因于模型来源。

Oracle 定位、可实现写检测和仅写整形保持不同证据范围；M 行实测 RPC 与 S 行离线变换仍使用各自攻击套件与成本对象。100 次新 planner 运行只支持 prefix scheduler 的实测效用范围。

## 发布校验

- 受保护的实验、证据和旧 provenance 共 {v['unchanged_scientific_and_prior_provenance_files']:,} 个文件与前一发布提交逐文件哈希一致。
- 源码闭包、引用键、标签和跨表引用核验通过；两份最终编译日志无未定义引用、重复标签、Overfull 或浮动表溢出。
- 主稿 {v['pdfs']['main']['pages']} 页，第 {v['pdfs']['main']['references_start']} 页进入 References，正文满足 13 页限制。补充材料 {v['pdfs']['supplement']['pages']} 页，既有 S1–S30 编号保留，新明细索引为 S31。
- 所有最终页面渲染总览检查，重点检查摘要／Table 1、系统综合、压缩表格、校准统计表及 S31。标准 placeins 2.2 以原版源码随附，用于让 §8 浮动表留在该节；来源和 SHA-256 记于本目录。
- 根目录、包内 pdf 目录与 manuscript 内 PDF 副本逐字节一致；匿名论文源码包和完整发布清单一并更新。

验证收据：`provenance/r22-sok-positioning/verification.json`、`visual-check.json` 和 `anonymous-paper-check.json`。完整包可运行 `python verify_package.py` 校验，文稿修订可运行本目录 `verify_revision.py` 校验；二者均不发起模型调用。
'''
(R/'docs/R22-证据迁移SoK定位与篇幅重构.md').write_text(text,encoding='utf8',newline='\n')
(O/'README.md').write_text('''# R22 SoK positioning release

This editorial revision makes defense-evidence transfer the SoK's organizing question, expands whole-ledger/holdout synthesis and condenses the supporting studies. It adds no experiments or customers.

The committed manuscript sources are authoritative. `build_pdfs.py` builds both documents; `render_review.py` renders the delivered pages; `verify_revision.py` checks protected evidence, exact table subsets, citations and PDF copies. `update_metadata.py` registers the release. `release_ops.py anonymous` builds the anonymous paper/source bundle; `release_ops.py manifest` refreshes the complete package inventory after all outputs are final. `write_docs.py` generates the Chinese change note from the saved verification.

Do not run historical revision generators to rebuild the current manuscript. The scientific experiment protocols and original results remain unchanged.
''',encoding='utf8',newline='\n')
print('R22_DOCUMENTATION_WRITTEN')
