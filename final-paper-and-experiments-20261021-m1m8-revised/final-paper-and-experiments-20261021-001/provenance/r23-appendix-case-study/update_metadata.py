"""Register the literature-SoK release and its single appendix case."""
from pathlib import Path
from datetime import datetime,timezone
from pypdf import PdfReader
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
sys.path.insert(0,str(P));from verify_package import closure
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
s=load(P/'provenance/snapshot.json');s['purpose']='R23: literature-only SoK main body; Exp 1-4 consolidated into one compact appendix case study'
for name in ['main','supplement']:
    s['documents'][name]['closure']=closure(M,name+'.tex');s['documents'][name]['pdf_sha256']=sha(P/'pdf'/(name+'.pdf'))
names=set(n for doc in s['documents'].values() for n in doc['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':'R23-appendix-case-study','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
    'scope':'The literature audit, configuration-linked joins and holdout synthesis are the main contributions; empirical components form one compact appendix case with full grids in the supplement.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json');a['modules']['r23-appendix-case-study']={'description':s['purpose'],'paths':['provenance/r23-appendix-case-study/verification.json','provenance/r23-appendix-case-study/visual-check.json','provenance/r23-appendix-case-study/anonymous-paper-check.json','manuscript/sections/62-appendix-case-study.tex','manuscript/sections/64-case-study-register.tex']}
old=a['current_verification']
if old!='provenance/r23-appendix-case-study/verify_revision.py' and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']='provenance/r23-appendix-case-study/verify_revision.py'
a['current_publication']=list(dict.fromkeys(a['current_publication']+['provenance/r23-appendix-case-study/verify_revision.py','provenance/r23-appendix-case-study/verification.json']));save(P/'artifact-index.json',a)
ds={n:PdfReader(M/(n+'.pdf')) for n in ['main','supplement']}
pages={n:len(d.pages) for n,d in ds.items()};refs=next(i+1 for i,p in enumerate(ds['main'].pages) if 'References' in p.extract_text())
case=next(i+1 for i,p in enumerate(ds['main'].pages) if 'Case Study: Applying' in p.extract_text())
for target in [R/'README.md',P/'README.md']:
    root=target==R/'README.md'
    paths={'main':'main.pdf' if root else 'pdf/main.pdf','supp':'supplement.pdf' if root else 'pdf/supplement.pdf'}
    doc='[本轮修订说明](docs/R23-纯SoK主文与附录案例.md)' if root else '[R23 校验记录](provenance/r23-appendix-case-study/verification.json)'
    text=f'''# Agent side-channel SoK — Defense Evidence Transfer

当前版本按 **SoK** 组织主文：82 家族地图、39 条结果记录的完整比较审计、配置级联合绑定、六轴 holdout 综合，以及复用决策表。原 Exp 1–4 已合并为附录 E 的一个 case study，不再作为主文贡献。

- 主稿 {pages['main']} 页，正文共 {refs-1} 页，第 {refs} 页进入 References。
- 单个案例位于第 {case} 页；主文不含独立实证章节、模型对照表或校准实验数字。
- 补充材料 {pages['supplement']} 页，保留原始实验全表、统计修正、S31 详细结果和新增 S32 的案例数据登记表。

## 核心系统化结果

全量比较覆盖 39 条记录的 741 对，其中 133 对属于相关问题，17 对支持来源限定的描述性比较；15 对同家族记录中有 8 对涉及不同原语、目标或成本对象。351 格记录级审计将推断、效用和成本绑定到同一配置；2/20 联合绑定来自 CachePrune 一个家族、一个配置的两个结果。82 家族的六轴 holdout 矩阵区分各类迁移证据，复用决策表据此明确需要补充的测量。

## 案例与数据保留

发射器、执行状态、校准和观察视图被压缩为一个审计应用案例。Sol 690、Luna 150、MiniMax 115、GLM 115、100 次实时 planner，以及 100 次校准重采样/46,000 次 TLS 捕获均按原协议和统计范围保留。R21 的多重比较和训练敏感性修正保持有效；案例不替代文献审计的证据。

## 复现与校验

在发布包目录运行 `python verify_package.py` 验证完整清单、历史数据与源码/PDF 绑定；当前文稿校验为 `provenance/r23-appendix-case-study/verify_revision.py`。原方法与作者编码未改变，本轮没有新增实验或模型请求。

当前匿名论文源码包为 `provenance/r23-appendix-case-study/anonymous-paper-source.zip`，包含当前论文与补充材料的源码闭包和 PDF；完整实验匿名托管仍需提供独立快照。

{doc}

[主稿]({paths['main']}) · [补充材料]({paths['supp']})
'''
    target.write_text(text,encoding='utf8',newline='\n')
print('R23_METADATA',pages,'body',refs-1,'case',case)
