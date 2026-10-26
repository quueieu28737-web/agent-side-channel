"""Document the literature-only body and the one-page appendix case."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
v=json.loads((O/'verification.json').read_text(encoding='utf8'));main=v['pdfs']['main'];supp=v['pdfs']['supplement']
text=f'''# R23：按 SoK 重构主文，将 Exp 1–4 合并为附录案例

## 本轮定位

主文的贡献只来自文献系统化：结果级证据模型、82 家族地图、39 条记录的全量比较审计、配置级联合绑定、六轴 holdout 综合和复用决策。原四个自建实验不再是主文贡献，也不再以四个独立章节出现。

摘要和引言删除模型实验数值、四个实验的并列贡献和反复的 supporting 定位。Table 1 的最后一列改为“审计文献中的依据”，四个 RQ 均由完整记录或家族审计回答。结论回到比较对象、配置绑定和迁移轴，不再用实验数字收束。

## 主文逐项调整

| 位置 | 调整 |
|---|---|
| 摘要 | 只保留 SoK 的范围、审计发现及复用程序，不含自建模型实验或校准数字 |
| 引言 | 三项贡献统一为证据模型／地图、全量比较／绑定审计、holdout 综合／复用程序 |
| Table 1 | 各 RQ 只链接对应文献审计，不列 Exp 1–4 作为支撑 |
| §4–§6 | 保留层级规律、全部记录比较与配置联合绑定、完整 holdout 综合 |
| §7 | 文献实例解释复用判断，结尾仅用一句引向附录案例 |
| 决策表 | 移除自建实验数值与实验表链接，按 R1–R9 和 holdout 轴给出最低证据要求 |
| 原 §8 | 从主文源码入口移除，主文直接进入讨论、伦理与有效性范围 |
| 讨论／局限 | 以语料、记录和比较适用性为中心；实验采样和模型范围移入案例／补充 |

## 一个附录案例

Appendix E 的一个 case study 位于第 {main['appendix_case_page']} 页，连同对照表共 {v['case_source_words_including_grid']} 个源文本空白分词，整段与表格在同一页。四个对照只是该案例的四个审计边界，不再编号为 Exp 1–4：

1. 发射器：将观测位置、缓冲／流式成本绑定到具体输出接口。
2. 执行状态：区分观测相似、影子隔离的逻辑一致性和真实状态变化。
3. 校准：保留本地重校准敏感性与八重 Holm 修正，避免将原差异归因于模型来源。
4. 观察视图：在同一捕获上区分长度、时序和攻击套件，保留成本对象。

案例保留原先的样本分母、操作类别标签、逻辑一致性／真实 planner 效用边界及未通过原绝对筛选标准的事实。其作用是示范审计程序的应用；SoK 统计和结论来自文献记录。

## 补充材料同步

- S1–S31 编号保持，S31 改为附录案例明细的说明。
- 新增 S32，完整保留此前主文的 cohort、模型内对照和校准／局部整形／训练敏感性表。
- S11 的旧主文来源、S18 的实验位置对照和 S24 的模型结果说明已改为当前附录或补充位置，不再指向不存在的主文 8.1–8.4。
- 历史 Exp/E/R 编号继续用于代码与归档；所有原始结果与完整数据表保留。

## 校验与交付

- {v['unchanged_scientific_and_prior_provenance_files']:,} 个实验、证据和旧 provenance 文件与 R22 发布逐文件哈希一致。本轮新增实验和模型调用均为零。
- 方法与作者编码不变，十组详细数据表逐字节保持，案例四个对照数值分别绑定到原始表格／统计说明。
- 主文有 {main['main_body_tables']} 张表，均为文献系统化；主文实证章节数量为零。
- 主稿 {main['pages']} 页，正文 {main['references_start']-1} 页，第 {main['references_start']} 页开始 References；单个案例在第 {main['appendix_case_page']} 页。补充材料 {supp['pages']} 页。
- 引用、标签、PDF 副本和匿名源码闭包核验通过；所有最终页面渲染检查，重点检查摘要、Table 1、决策表、一页案例和 S32。

当前验证器为 `provenance/r23-appendix-case-study/verify_revision.py`，完整发布包仍用 `python verify_package.py` 只读校验。文稿、PDF、源码包、清单和两个 GitHub main 同步更新。
'''
(R/'docs/R23-纯SoK主文与附录案例.md').write_text(text,encoding='utf8',newline='\n')
(O/'README.md').write_text('''# R23: literature SoK with one appendix case

The main manuscript presents only the literature evidence model, complete audit, joint bindings, holdout synthesis and reuse procedure. Exp 1–4 are consolidated into one compact appendix case. Full empirical grids remain in the supplement; no experiments, raw results or coding were changed.

Build the committed manuscript with `build_pdfs.py`, render it with `render_review.py`, and run `verify_revision.py` for body scope, the single-page case, numerical bindings, preserved evidence, citations and published PDF copies. `update_metadata.py` registers the current sources. `release_ops.py anonymous` packages the paper/source closure; `release_ops.py manifest` updates the full artifact inventory after all outputs are final. `write_docs.py` generates the Chinese revision note from the verification receipt.

The committed sources are authoritative; historical editorial generators should not be used to recreate the current manuscript.
''',encoding='utf8',newline='\n')
print('R23_DOCUMENTATION_WRITTEN')
