"""Register R26 documents and audit overlay; preserve historical evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
sys.path.insert(0,str(P));from verify_package import closure
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
revision='r26-source-reconciliation'
purpose='R26: distinguish attack generalization from defense transfer; reconcile 11 source cells; specify record/cohort rules and positive reuse decisions'
s=load(P/'provenance/snapshot.json');s['purpose']=purpose
for n in ['main','supplement']:
 s['documents'][n]['closure']=closure(M,n+'.tex');s['documents'][n]['pdf_sha256']=sha(P/'pdf'/(n+'.pdf'))
names={n for doc in s['documents'].values() for n in doc['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':revision,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
 'scope':'Literature SoK with one appendix case; versioned source-reporting reconciliation; raw experiments unchanged.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json')
a['modules'][revision]={'description':purpose,'paths':[f'provenance/{revision}/'+n for n in ['verification.json','visual-check.json','anonymous-paper-check.json','analysis.json','data-verification.json','family-cell-review.csv','record-audit.csv','holdout-object-ledger.csv','cohort-rules.json']]}
old=a['current_verification'];cur=f'provenance/{revision}/verify_revision.py'
if old!=cur and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=cur;a['current_publication']=list(dict.fromkeys(a['current_publication']+[cur,f'provenance/{revision}/verification.json']))
save(P/'artifact-index.json',a)
v=load(O/'verification.json');pdf=v['pdfs'];mainpdf=pdf['main']
text=f'''# R26：RQ3 与原文证据收敛

本轮完成用户要求的五项修订，论文保持三项 SoK 贡献：记录级比较、配置级联合绑定、部署决策。实证结果保留在附录案例和补充材料。

## 逐项修改

1. **RQ3**：主文区分攻击泛化、受防御条件评估和冻结校准迁移。82 家族矩阵的 19 个 H 标记按评估对象重索引，不能从攻击留出测试继承防御迁移结论。两项拓扑 H 是识别器泛化；三项模型 H 均不在 20 个缓解家族中。保留 Time Will Tell 等共同规则的跨条件结果价值。
2. **原文复核**：核对六篇论文的固定版本方法/结果段，另核对三个正面或 holdout 案例来源。11 个原家族问号调整为 4 个部分绑定 P、7 个范围内未报告 U，未新增 B；同步 19 个记录单元格。6 个其他记录级问号仍保留，不能由家族结论自动补齐。S34 与逐格文件提供版本、定位符、哈希和理由。
3. **记录拆分**：区分家族、比较记录、模型/参数坐标与结果。按原语、执行方式、接收者/目标或独立成本对象拆分；不把参数网格当作独立记录。明确提取范围为 20 个缓解家族与 6 个上下文家族。
4. **问题分组**：公开 39 条记录的九组规则、成员及边界。六个非单例组产生 133 对，三个单例组不产生相关对。这是既有账本的回溯性规则说明，未声称预注册。
5. **具体决策与正面实例**：Early Bird 前缀恢复与 CachePrune 直接恢复可作限定范围的候选比较；CachePrune 的同配置保护/质量/成本包可供可行性判断。Early Bird 的语义处理成本不能给前缀策略定价，需另测服务成本。主文决策表明确保留什么、下一步测什么。

## 数值与解释

- 全部 741 对、133 个相关对及 17/105/11 分类保持不变。
- 严格联合绑定仍为 4/22、5/22、2/17、2/20、0/14；2/20 是 CachePrune 两个结果、一个共享配置。
- 先前 S33 的 16/17 是复核前接受 P/? 的敏感性上界；现行 S34 对应为 6/17。二者版本已明确标注，不能混用。
- 原实验、冻结协议、原始数据、效应量及历史审计文件均保留。新 Sol 实验不能核实外部论文的训练与测试来源，因此本轮新增实验和模型调用均为 0。

## 校验与交付

- 351 个记录单元格、180 个家族显示单元格、165 个查询成员、20 个状态情景、九组成员及 19 个 H 对象已独立复算。
- 主稿 {mainpdf['pages']} 页，正文止于第 {mainpdf['main_body_last_page']} 页，References 从第 {mainpdf['references_start']} 页开始；单个案例位于第 {mainpdf['appendix_case_page']} 页。
- 补充材料 {pdf['supplement']['pages']} 页；当前校正为 S34，S33 保留历史敏感性。
- 编译、引用闭包、PDF 副本一致性、版面检查和发布清单均有记录。

当前审计为源报告的定向核对，不构成独立人际编码信度或未公开训练流程的证明。范围内未报告不等于来源作者没有执行过该实验。
'''
(R/'docs/R26-RQ3与原文证据收敛.md').write_text(text,encoding='utf8',newline='\n')
for target in [R/'README.md',P/'README.md']:
 root=target==R/'README.md';prefix='' if root else 'pdf/'
 note='docs/R26-RQ3与原文证据收敛.md' if root else f'provenance/{revision}/verification.json'
 overview=f'''# Agent side-channel SoK — Defense Evidence Transfer

当前稿以记录级比较、配置级联合绑定和部署决策为主线。R26 完成 RQ3 的攻击/防御对象区分、11 个原文审计单元格复核、记录拆分与九组问题规则，以及正面可复用实例。

## 关键结果

- 82 家族；39 记录；741 对完整库存，133 个相关对中 17 个描述性匹配。
- 11 个家族待核单元格调整为 4 P、7 U；无新增 B。历史记录保持，当前覆盖层见 S34。
- 联合绑定 4/22、5/22、2/17、2/20、0/14 不变。CachePrune 两条结果共享一个保护/质量/成本包。
- 留出矩阵区分攻击泛化与防御迁移，不能继承另一评估对象的证据。
- 新实验与模型调用为 0；全部原始实验和完整统计结果保留。

## 当前交付

主稿 {mainpdf['pages']} 页，正文止于第 {mainpdf['main_body_last_page']} 页；补充材料 {pdf['supplement']['pages']} 页。根目录、manuscript/、发布包 pdf/ 的 PDF 一致。

运行发布包的 `python verify_package.py` 核验清单、数据与源码/PDF 绑定。当前文稿核验为 `provenance/{revision}/verify_revision.py`。同目录匿名源码包仅包含论文与补充材料；完整实验托管需要单独的匿名快照。

[本轮修订与校验]({note})

[主稿]({prefix}main.pdf) · [补充材料]({prefix}supplement.pdf)
'''
 target.write_text(overview,encoding='utf8',newline='\n')
print('R26_METADATA_REGISTERED')
