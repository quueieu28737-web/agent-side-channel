"""Register the R33 source closure and current delivery documentation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,shutil
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
rev='r33-review-closure';s=load(P/'provenance/snapshot.json')
s['purpose']='R33: scoped SoK evidence reuse; granularity sensitivity, reconstructable joint queries, reporting cards and publication/source status; no new model or participant study'
for n in ['main','supplement']:
 s['documents'][n]['closure']=closure(M,n+'.tex');s['documents'][n]['pdf_sha256']=sha(M/(n+'.pdf'))
names={n for d in s['documents'].values() for n in d['closure']};s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':rev,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Original record/pair judgments and experimental observations preserved. New fixed-judgment coarsening, explicit query identities, source metadata and worked reporting cards. Applications are illustrative.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json');previous=a['current_verification'];current='provenance/'+rev+'/verify_revision.py'
if previous!=current and previous not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(previous)
a['current_verification']=current;a['current_publication']=list(dict.fromkeys(a['current_publication']+[current,'provenance/'+rev+'/verification.json']))
a['modules'][rev]={'description':s['purpose'],'paths':['provenance/'+rev+'/'+n for n in ['revision.json','revision-items.json','audit-check.json','verification.json','visual-check.json','anonymous-paper-check.json','source-checks.json']]}
save(P/'artifact-index.json',a)
v=load(O/'verification.json');mp=v['pdfs']['main'];sp=v['pdfs']['supplement']
for folder in [R,P]:
 prefix='manuscript/' if folder==P else ''
 text=f'''# Agent side-channel SoK — Reusing Defense Evidence

当前稿围绕三个可操作输出：来源限定的比较、同配置的保护/效用/成本组合、部署测量计划。R33 逐项处理 W1–W8，保持 SoK 定位。当前任务以 {prefix}docs/CURRENT-PLAN.md 为准，历史清单不自动恢复任务。

## 当前内容

- 82 家族提供背景地图；39 条记录中含 20 个家族的 33 条缓解记录。
- 133 个相关比较的计数按记录粒度解释；新增四种粒度投影，不将对象不同视为源论文缺陷率。
- 正文列全部正向联合绑定记录；同一 PDF 列 33 条记录的完整查询成员关系和 8 个家族的记录交叉表。
- Early Bird、TDXRay、CachePrune 填表示例与可编辑 reporting card 展示具体部署决策。
- 外部回溯和内部案例仅作使用示例；P5 前提失败不计有利证据，不用不显著性验证框架。
- 原始实验、39 条记录、351 格及历史 pair 判断不变。本轮新增模型调用和参与者数据均为 0。

## 当前交付

主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。根目录、manuscript 和发布包 pdf 中的 PDF 一致。

运行发布包的 python verify_package.py 核验清单、数据及源码/PDF 绑定。当前文稿核验为 provenance/{rev}/verify_revision.py。匿名源码包只包含论文与补充材料，完整实验托管仍需单独匿名快照。

[主稿]({'pdf/' if folder==P else ''}main.pdf) · [补充材料]({'pdf/' if folder==P else ''}supplement.pdf)
'''
 (folder/'README.md').write_text(text,encoding='utf8',newline='\n')
shutil.copyfile(M/'docs/CURRENT-PLAN.md',R/'docs/CURRENT-PLAN.md')
for f in [R/'docs/R33-W1-W8-逐项修订.md',M/'docs/R33-W1-W8-逐项修订.md']:
 t=f.read_text(encoding='utf8').replace('§3/§5；表12–14；S37','§3/§5；比较与粒度表；S37').replace('标题、摘要、§5、附录F','标题、摘要、§4–5、S37').replace('§4、§7.1、附录F','§4、§7.1、S37')
 if '## 本轮交付校验' not in t:t+=f'\n## 本轮交付校验\n\n主稿 {mp["pages"]} 页（正文至第 {mp["main_body_last_page"]} 页），补充材料 {sp["pages"]} 页。36 项审计检查、4 种粒度复算、5 类联合查询复算、82/39 来源元数据、引用闭包、编译日志及三处PDF副本一致性检查通过。视觉检查与完整包核验记录位于当前发布目录。\n'
 f.write_text(t,encoding='utf8',newline='\n')
print('R33_METADATA_REGISTERED')
