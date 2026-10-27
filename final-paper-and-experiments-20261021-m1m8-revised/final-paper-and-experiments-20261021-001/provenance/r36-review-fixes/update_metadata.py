"""Register the R35 document closure and source-scoped results."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

O=Path(__file__).resolve().parent
P=O.parents[1]
R=P.parents[1]
M=P/'manuscript'
sys.path.insert(0,str(P))
from verify_package import closure

def load(f):return json.loads(f.read_text(encoding='utf8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

v=load(O/'verification.json')
assert v['status']=='R36_APPLICABILITY_AND_PDFS_PASS'
s=load(P/'provenance/snapshot.json')
s['purpose']='R36: applicability, source-bound sensitivity and bounded retrieval accounting'
for name in ('main','supplement'):
    s['documents'][name]['closure']=closure(M,name+'.tex')
    s['documents'][name]['pdf_sha256']=sha(M/(name+'.pdf'))
names={n for doc in s['documents'].values() for n in doc['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':'r36-review-fixes','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
                         'scope':'Privacy/attribution mitigation cohort; preserved historical evasion and contextual records.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat()
save(P/'provenance/snapshot.json',s)

a=load(P/'artifact-index.json')
old=a['current_verification']
new='provenance/r36-review-fixes/verify_r36.py'
if old!=new and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=new
a['current_publication']=list(dict.fromkeys(a['current_publication']+[new,'provenance/r36-review-fixes/verification.json']))
a['modules']['r36-review-fixes']={'description':s['purpose'],
 'paths':['provenance/r36-review-fixes/'+n for n in ('verification.json','verify_r36.py','visual-check.json','anonymous-paper-check.json')]}
save(P/'artifact-index.json',a)

for folder in (R,P):
    pdf='pdf/' if folder==P else ''
    src='manuscript/' if folder==P else P.relative_to(R).as_posix()+'/manuscript/'
    doc='manuscript/docs/' if folder==P else 'docs/'
    text=f'''# Agent side-channel SoK — Defense Evidence

R36 将隐私与归因的防御机制、覆盖和来源限定的部署证据作为主线。历史的 Type III 规避与背景记录保留为边界。

- 在 52 个 Type I/II 核心家族中，19 家族关联 31 条缓解记录；33 家族在本次抽取中没有关联的合格缓解记录。
- 15/16 适用家族明确绑定推断结果，3/16 绑定效用，2/10 绑定匹配的受保护数据拟合对照。接受部分证据后依次为 16/16、5/16、2/10。
- OpenAlex 查询覆盖历史 20 家族，但索引不完整；5 篇施引论文的 6 条语境经过核查，不计算误用率。形式证明状态未逐篇审定。
- 原始记录与实验保留，三个实例使用各自已有来源和实验，不作跨研究受控性能比较。

主稿 {v['pdfs']['main']['pages']} 页、正文至第 13 页；补充材料 {v['pdfs']['supplement']['pages']} 页。审计口径与输入哈希由 `{src}tools/r35_privacy_census.py` 复算，敏感性核查见 `{doc}R36-统计口径与检索核查.md`。

[主稿]({pdf}main.pdf) · [补充材料]({pdf}supplement.pdf)
'''
    (folder/'README.md').write_text(text,encoding='utf8',newline='\n')

save(O/'revision.json',{'revision':'r36-review-fixes','base_commit':'57bf7f124f24474c7e9f56d0a5d64db4d06c243a',
 'goal':'B2–B6: applicability sensitivity, heterogeneous costs and bounded retrieval',
 'incomplete':['Broader adaptive-attacker source recoding','Remaining adjacent defense source adjudication','Full formal-proof classification','Representative forward-citation analysis'],
 'source_recoding':False,'new_model_calls':0})
print('R36_METADATA_REGISTERED')
