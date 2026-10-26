"""Register a wording-only claim alignment; preserve all R28 evidence and receipts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure
def read(f):return json.loads(f.read_text(encoding='utf8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
rev='r29-claim-alignment'
s=read(P/'provenance/snapshot.json')
s['purpose']='R29: align the central SoK claim around traceable comparisons, configuration-bound outcomes and deployment measurement requirements; no new data'
for n in ['main','supplement']:
 s['documents'][n]['closure']=closure(M,n+'.tex');s['documents'][n]['pdf_sha256']=sha(M/(n+'.pdf'))
names={n for d in s['documents'].values() for n in d['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':rev,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
 'scope':'Editorial alignment only. External retrospective cases and internal judgments illustrate use; all R28 and earlier empirical evidence is preserved.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=read(P/'artifact-index.json');previous=a['current_verification'];current='provenance/'+rev+'/verify_revision.py'
if previous!=current and previous not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(previous)
a['current_verification']=current
a['current_publication']=list(dict.fromkeys(a['current_publication']+[current,'provenance/'+rev+'/verification.json']))
a['modules'][rev]={'description':s['purpose'],'paths':['provenance/'+rev+'/'+n for n in ['verification.json','visual-check.json','anonymous-paper-check.json']]}
save(P/'artifact-index.json',a)
v=read(O/'verification.json');mp=v['pdfs']['main'];sp=v['pdfs']['supplement']
doc=f'''# R29：统一 SoK 核心主张

## 采用的主张

框架将分散的防御证据转化为可追溯的比较、配置绑定和部署测量要求，并通过外部案例与内部判断展示其使用价值。

## 文稿修改

- 摘要、引言、三项贡献、Table 1、结论和补充材料导语均围绕这一主张组织。
- 三项产出依次为：有来源与适用条件的比较，同一配置下可联合解释的结果，以及部署变化需要补充的测量。
- 外部 B 为结局可见的回溯案例；七条 C 为已有内部判断。保留方法、来源和完整结果，使用“展示使用价值”的论断，不新增预测准确性或优于普通阅读的主张。
- 82 家族、39 记录、351 审计格及全部历史实验、统计和 R28 收据保持不变；本轮新增实验、模型调用、客户均为 0。
- 主稿 {mp['pages']} 页，正文结束于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。根目录与发布包 PDF 同步。

## 校验

发布包 provenance/r29-claim-alignment/verify_revision.py 检查主张一致性、历史证据保留、引用闭包及 PDF 副本；verify_package.py 检查全部清单和来源绑定。PDF 编译诊断和视觉检查随发布包保存。
'''
for f in [R/'docs/R29-核心主张统一.md',M/'docs/R29-核心主张统一.md']:f.write_text(doc,encoding='utf8',newline='\n')
for f in [R/'README.md',P/'README.md']:
 text=f.read_text(encoding='utf8')
 before='当前稿以记录级比较、配置级联合绑定和部署决策为主线。R28 增加外部回溯核验和七条内部判断，保留 R26 原文复核及 R27 主文收敛。'
 after='当前稿的核心主张：框架将分散的防御证据转化为可追溯的比较、配置绑定和部署测量要求，并通过外部案例与内部判断展示其使用价值。R29 统一摘要、引言、贡献、Table 1、结论和补充材料导语；R28 案例及全部历史证据保持不变。'
 if before in text:text=text.replace(before,after)
 text=text.replace('provenance/r28-framework-utility/verify_revision.py','provenance/r29-claim-alignment/verify_revision.py')
 import re
 text=re.sub(r'主稿 \d+ 页，正文止于第 \d+ 页；补充材料 \d+ 页。',f"主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。",text)
 f.write_text(text,encoding='utf8',newline='\n')
print('R29_METADATA_REGISTERED')
