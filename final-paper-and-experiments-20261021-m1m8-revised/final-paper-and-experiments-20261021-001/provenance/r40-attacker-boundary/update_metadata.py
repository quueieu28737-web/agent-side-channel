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
assert v['status']=='R40_ATTACKER_BOUNDARY_PDFS_PASS'
s=load(P/'provenance/snapshot.json')
s['purpose']='R40: attacker-conditioned protection, existing matched recovery examples and WRA pilot disclosure'
for name in ('main','supplement'):
    s['documents'][name]['closure']=closure(M,name+'.tex')
    s['documents'][name]['pdf_sha256']=sha(M/(name+'.pdf'))
names={n for doc in s['documents'].values() for n in doc['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':'r40-attacker-boundary','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
                         'scope':'Privacy/attribution SoK with existing matched attacker examples and separately disclosed incomplete WRA pilot.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat()
save(P/'provenance/snapshot.json',s)

a=load(P/'artifact-index.json')
old=a['current_verification']
new='provenance/r40-attacker-boundary/verify_r40.py'
if old!=new and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=new
a['current_publication']=list(dict.fromkeys(a['current_publication']+[new,'provenance/r40-attacker-boundary/verification.json']))
a['modules']['r40-attacker-boundary']={'description':s['purpose'],
 'paths':['provenance/r40-attacker-boundary/'+n for n in ('verification.json','verify_r40.py','visual-check.json','anonymous-paper-check.json')]+['manuscript/data/r40-wra-glm-summary.json','manuscript/tools/r40_check.py','manuscript/sections/77-attacker-boundary.tex']}
save(P/'artifact-index.json',a)

for folder in (R,P):
    pdf='pdf/' if folder==P else ''
    src='manuscript/' if folder==P else P.relative_to(R).as_posix()+'/manuscript/'
    doc='manuscript/docs/' if folder==P else 'docs/'
    text=f'''# Agent side-channel SoK — Defense Evidence

R40 在隐私与归因防御 SoK 中突出攻击者能力的迁移边界，沿用已有实验，本轮新增模型请求为 0。

- 在 52 个 Type I/II 核心家族中，19 家族关联 31 条缓解记录；33 家族在本次抽取中没有关联的合格缓解记录。
- 15/16 适用家族明确绑定推断结果，3/16 绑定效用，2/10 绑定匹配的受保护数据拟合对照。接受部分证据后依次为 16/16、5/16、2/10。
- OpenAlex 查询覆盖历史 20 家族，但索引不完整；5 篇施引论文的 6 条语境经过核查，不计算误用率。形式证明状态未逐篇审定。
- 同一受保护测试视图中，缓冲分桶从未适应攻击的 50.0% 升至重新拟合后的 70.8%；流式分批从 50.0% 升至 100.0%，恒定事件数对照保持 50.0%。结果限定于已有运输层示例。
- 补充材料保留 WRA/GLM 两轮探索及其截断：它们没有简单/适应性攻击的配对对照，不能据此声称 WRA 的适应性恢复或在线防御效果。原始记录和历史实验保留。

主稿 {v['pdfs']['main']['pages']} 页、正文至第 13 页；补充材料 {v['pdfs']['supplement']['pages']} 页。审计口径与输入哈希由 `{src}tools/r35_privacy_census.py` 复算，敏感性核查见 `{doc}R40-攻击者能力与迁移边界.md`。

[主稿]({pdf}main.pdf) · [补充材料]({pdf}supplement.pdf)
'''
    (folder/'README.md').write_text(text,encoding='utf8',newline='\n')

save(O/'metadata-registration.json',{'revision':'r40-attacker-boundary','base_commit':load(O/'revision.json')['base_commit'],
 'goal':'Write existing evidence around attacker-conditioned protection and disclose WRA scope',
 'incomplete':['Online WRA protection/utility/cost evaluation','WRA matched attack-adaptation contrast'],
 'new_experiments_requested':False,'source_recoding':False,'new_model_calls':0})
print('R40_METADATA_REGISTERED')
