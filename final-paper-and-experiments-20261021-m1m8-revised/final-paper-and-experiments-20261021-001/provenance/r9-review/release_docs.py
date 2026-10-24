"""Publish R9 change checklist and reproduction entry points."""
from pathlib import Path
import json
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
pages={n:len(PdfReader(P/'pdf'/f'{n}.pdf').pages) for n in ['main','supplement']}
rows=[
('1a','主文核心论证不依赖 S1–S23','已完成','§2–§8提供定义、数据口径和发现；S编号仅在附录C作可选的细节导航。'),
('1b','统一 NR-R/NR-A/NR-V 与 U/A/?','已完成','主稿和补充材料共用 B/P/U/A/?/--；Supplement首页提供旧CSV字段映射，原始数据字段保留。'),
('1c','主文定义 R1–R9 判定标准','已完成','新增Table 8逐项给出Bound条件、适用性和证据状态，Table 9紧接20×9矩阵。'),
('1d','同一PDF容纳39记录与实验索引','已完成','Appendix A为审计轨迹/逻辑等价；B为39条记录、族引用及来源定位；C为四模块与历史实验映射及扩展结果。'),
('1e','遵守附录及正文页数要求','已完成','按官方CFP采用正文≤13、总计≤18的保守约束；参考文献之后放附录。未拼接52页补充材料。'),
('2a','集中反复的防御性免责声明','已完成','§1 Scope给出范围，§9.3集中统计/效用/外部效度边界；摘要、模块Finding和结论突出研究给出的判断。'),
('2b','突出本论文特色和正面洞察','已完成','强调以结果记录识别三类证据转移错误，以及四个实测演示如何改变部署选择。'),
('3a','实验分支收敛为四个模块','已完成','Exp 1发射位置；Exp 2执行状态与链路；Exp 3真实轨迹/操作特征；Exp 4时序/延迟/匹配传输对照。'),
('3b','处理旧E编号和开发痕迹','已完成','旧E键仅作附录及Supplement复现索引；unused E4不再出现在当前PDF索引。历史代码不改名。'),
('3c','收拢扩展与敏感性分析','已完成','Luna、客户权重/删除、同操作属性诊断收入Appendix C与补充细节，保留真实阴性结果及口径。'),
('3d','增加SoK宏观规律与map-only族分析','已完成','§4新增P2/P5信号来源与P3/P4接收面分布，以及32 map-only族的层级/目标覆盖。多标签以incidence计数。'),
('4a','明确动作目标的科学用途','已完成','Exp 3说明cancel/return来自参考请求动作，定位加密元数据保留的操作特征；重点呈现合规与隐私分离、保护位置和匹配成本。'),
('4b','属性诊断不作过度宣传','已完成','Appendix C保留20实例/15客户、BA30.3%、单次shuffle65.2%、两提示同特征等事实，§9.3说明其不确定性。'),
('5a','核对首页标题上方留白','核实符合模板','首标题ink top=96.43pt（1.339in），来自IEEEtran conference,compsoc默认设置；保留标准边距、字号、行距。'),
('5b','核对原[26]/[51] URL','核实原链接完整','原arXiv 2610.20962v1和2607.18826v1的可点击URI、bbl及bib一致；按bibkey跟踪重新排序后的编号。'),
('5c','修正原[34]日期/核对DOI','已完成','修正publisher version2025为publisher version 2025；DOI完整为10.3390/electronics14071263。'),
('5d','58族表增加视觉分组','已完成','Table 6两栏各29族，按P1、P1/P2、P2及工作流来源加标题和横线；58族全部G/O/Type原值保留。'),
('QA1','数值和单位校验','已完成','8张科学表、51行、346个数字与R8对应表完全一致；291=97合格任务×3seed，173变更+118失败。'),
('QA2','PDF与发布包校验','以最终收据为准','validation.json、visual_qa.json和SHA256SUMS.json绑定最终PDF及全部发布文件。'),
]
content='# R9：主文自洽与贡献呈现逐项修改\n\n本轮按“突出核心贡献、主文独立可读、集中交代证据边界”重构。既有实验、训练/测试划分、结果与历史发布证据保持不变，本轮新增LLM运行0个。\n\n| 项目 | 用户意见 | 处理 | 当前落点 |\n|---|---|---|---|\n'
for row in rows:content+='| '+' | '.join(row)+' |\n'
content+=f'\n## 当前交付\n\n- 主稿：{pages["main"]}页；补充材料：{pages["supplement"]}页。正文、References和Appendix的实际页码见最终验证收据。\n- 主稿以四模块呈现比较发现，补充材料保留S1–S23及全部历史实证细节。\n- 原R8论文源、PDF、manifest及README保存在 provenance/r9-review/prior-manuscript/ 和 prior-release/；没有重新运行或覆盖历史实验。\n- 官方投稿规则核对：https://sp2027.ieee-security.org/cfpapers.html （2026-10-24）。使用IEEEtran conference,compsoc，保持默认边距、字体和行距；该规则不允许无限长附录。\n\n## 写作与结果边界\n\n正文现在强调结果记录框架、跨层接收视图、状态风险、合规与操作隐私分离、时序与轻量传输对照。这次是基于已验证结果的呈现重构；既有统计功效、真实在线规划效用和外部效度限制集中保留在§9.3。\n'
(R/'docs/R9-主文自洽与贡献呈现修改清单.md').write_text(content,encoding='utf8',newline='\n')
coverage={'revision':'R9','items':[dict(zip(['id','request','status','location'],r)) for r in rows],'scope':'Editorial synthesis; no new LLM runs; frozen experimental data unchanged.'}
(O/'checklist-coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rootlink=P.relative_to(R).as_posix()
readme=f"""# Agent side-channel SoK — R9

当前论文突出 **source-bound result records**、三类证据转移错误和四个实验演示。

- [主稿](main.pdf)：{pages['main']}页，包含完整58族地图、R1–R9规则、20族审计矩阵、39记录与实验索引。
- [补充材料](supplement.pdf)：{pages['supplement']}页，保留完整方法与结果。
- [逐项修改清单](docs/R9-主文自洽与贡献呈现修改清单.md)。
- [可复现发布包]({rootlink}/README.md)。

本轮未新增模型实验或更改旧结果。原Sol 690运行、Luna 150运行及后续分析保持原始来源与样本范围。当前版本以正文四模块组织阅读，以附录历史E键定位复现代码。

## 核验

进入发布包目录，使用具有pypdf/pdfplumber的Python环境：

    python provenance/r9-review/verify_publication.py
    python verify_package.py

数值、来源、链接、版式及历史字节核验收据在 provenance/r9-review/。LaTeX构建入口为 manuscript/main.tex 与 manuscript/supplement.tex，使用IEEEtran v1.8b的conference,compsoc选项。

匿名论文源包位于发布包 provenance/r9-review/anonymous-paper-source.zip；正式投稿的完整实验匿名托管和注册披露由作者按投稿流程完成。
"""
(R/'README.md').write_text(readme,encoding='utf8',newline='\n')
package=readme.replace('[主稿](main.pdf)','[主稿](pdf/main.pdf)').replace('[补充材料](supplement.pdf)','[补充材料](pdf/supplement.pdf)').replace('[逐项修改清单](docs/R9-主文自洽与贡献呈现修改清单.md)','[逐项修改清单](provenance/r9-review/docs/R9-主文自洽与贡献呈现修改清单.md)').replace(f'- [可复现发布包]({rootlink}/README.md)。','- 当前源码与来源绑定：artifact-index.json、provenance/snapshot.json、SHA256SUMS.json。')
(P/'README.md').write_text(package,encoding='utf8',newline='\n')
print('R9_DOCS',len(rows),pages)
