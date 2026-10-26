"""Register the three-contribution SoK revision without changing scientific evidence."""
from pathlib import Path
from datetime import datetime,timezone
from pypdf import PdfReader
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
sys.path.insert(0,str(P));from verify_package import closure
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
revision='r24-three-sok-contributions'
purpose='R24: record-level comparison, configuration-level joint binding and deployment decisions; empirical nonsignificance is not evidence of framework validity'
s=load(P/'provenance/snapshot.json');s['purpose']=purpose
for name in ['main','supplement']:
    s['documents'][name]['closure']=closure(M,name+'.tex');s['documents'][name]['pdf_sha256']=sha(P/'pdf'/(name+'.pdf'))
names=set(n for doc in s['documents'].values() for n in doc['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':revision,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
    'scope':'Three literature-derived SoK contributions; one appendix worked case with all original statistical results retained in the supplement.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json')
a['modules'][revision]={'description':purpose,'paths':[f'provenance/{revision}/'+n for n in ['verification.json','visual-check.json','anonymous-paper-check.json']]}
old=a['current_verification'];current=f'provenance/{revision}/verify_revision.py'
if old!=current and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=current
a['current_publication']=list(dict.fromkeys(a['current_publication']+[current,f'provenance/{revision}/verification.json']))
save(P/'artifact-index.json',a)
docs={n:PdfReader(M/(n+'.pdf')) for n in ['main','supplement']}
pages={n:len(d.pages) for n,d in docs.items()}
refs=next(i+1 for i,p in enumerate(docs['main'].pages) if 'References' in p.extract_text())
body_end=refs if docs['main'].pages[refs-1].extract_text().split('References',1)[0].strip() else refs-1
case=next(i+1 for i,p in enumerate(docs['main'].pages) if 'Case Study: Applying' in p.extract_text())
for target in [R/'README.md',P/'README.md']:
    root=target==R/'README.md'
    main='main.pdf' if root else 'pdf/main.pdf'
    supp='supplement.pdf' if root else 'pdf/supplement.pdf'
    note='docs/R24-三项SoK贡献与统计解释.md' if root else f'provenance/{revision}/verification.json'
    text=f'''# Agent side-channel SoK — Defense Evidence Transfer

当前主文统一为三项 SoK 贡献，摘要、引言、Table 1、综合讨论和结论使用同一论证结构：

1. **记录级比较**：完整检查 39 条记录的 741 对；133 对涉及相关问题，其中 17 对支持来源限定的描述性比较。15 对同家族记录中，8 对涉及不同原语、目标或成本对象。
2. **配置级联合绑定**：351 个记录审计单元格把推断、效用和成本关联到具体配置。联合包由 CachePrune 的两条记录提供，对应一个家族、一个配置；不能将它解读为两个独立配置。
3. **部署决策**：82 家族的六轴 holdout 矩阵与决策表说明哪些证据支持所提部署变化，以及还需要测量什么。

## 案例与统计范围

原 Exp 1–4 保留为一个附录案例。校准检验评估模型来源对比；不显著结果不构成防御等价或审计框架正确的证据。本地重校准对照来自区分模型来源与有限训练样本变化的设计要求。

全部历史效应量、置信区间、八项原始及 Holm 校正检验、100 次训练重采样和联合训练／测试区间保留。100 次重采样描述已有客户内的敏感性，没有增加独立客户。绝对工程筛选标准未通过的事实保持。本轮无新增实验或模型调用。

## 当前交付

- 主稿 {pages['main']} 页；正文止于第 {body_end} 页，References 从第 {refs} 页开始。
- 单个附录案例位于第 {case} 页；主文的证据来自文献审计。
- 补充材料 {pages['supplement']} 页，S30 保存完整统计修正，S31–S32 保存详细案例表。
- 根目录、发布包 pdf/ 和 manuscript/ 内 PDF 逐字节一致。

在发布包运行 `python verify_package.py` 检查清单、保存数据和源码/PDF 绑定。当前文稿检查为 `provenance/{revision}/verify_revision.py`，匿名论文源码包为 `provenance/{revision}/anonymous-paper-source.zip`；完整实验匿名托管需独立快照。

[本轮修订与校验]({note})

[主稿]({main}) · [补充材料]({supp})
'''
    target.write_text(text,encoding='utf8',newline='\n')
print('R24_METADATA',pages,'body_end',body_end,'case',case)
