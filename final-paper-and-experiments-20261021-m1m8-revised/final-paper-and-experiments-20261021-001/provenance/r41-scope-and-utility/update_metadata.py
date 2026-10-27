"""Register the R41 source frame, R8 outcome scopes and document closure."""
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
assert v['status']=='R41_SCOPE_UTILITY_PDFS_PASS'
s=load(P/'provenance/snapshot.json')
s['purpose']='R41: C1-C5 attack-evaluation source frame and outcome-specific functional-quality applicability'
for name in ('main','supplement'):
    s['documents'][name]['closure']=closure(M,name+'.tex')
    s['documents'][name]['pdf_sha256']=sha(M/(name+'.pdf'))
names={n for doc in s['documents'].values() for n in doc['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':'r41-scope-and-utility','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
                         'scope':'Mitigation results in C1-C5 attack-evaluated studies; narrow quality preservation is separate from executed-task outcomes. Existing matched attacker examples and the incomplete WRA pilot retain their stated scope.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat()
save(P/'provenance/snapshot.json',s)

a=load(P/'artifact-index.json')
old=a['current_verification']
new='provenance/r41-scope-and-utility/verify_r41.py'
if old!=new and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=new
a['current_publication']=list(dict.fromkeys(a['current_publication']+[new,'provenance/r41-scope-and-utility/verification.json']))
a['modules']['r41-scope-and-utility']={'description':s['purpose'],
 'paths':['provenance/r41-scope-and-utility/'+n for n in ('verification.json','verify_r41.py','update_metadata.py','metadata-registration.json','visual-check.json','anonymous-paper-check.json')]+[
     'manuscript/data/r41-utility-scopes.json',
     'manuscript/data/r41-current-census.json',
     'manuscript/tools/r41_utility_scope.py',
     'manuscript/sections/78-utility-scope.tex',
     'manuscript/tables/r41-reporting-patterns.tex',
     'manuscript/tables/r41-family-audit.tex',
     'manuscript/tables/r41-positive-joins.tex',
     'manuscript/tables/r41-fit-sensitivity.tex',
     'manuscript/tables/r41-removal.tex',
     'manuscript/tables/r41-utility-records.tex',
     'manuscript/tables/r41-reconstruction.tex',
     'manuscript/docs/R41-P0范围与效用适用性修正.md']}
save(P/'artifact-index.json',a)

for folder in (R,P):
    pdf='pdf/' if folder==P else ''
    src='manuscript/' if folder==P else P.relative_to(R).as_posix()+'/manuscript/'
    doc='manuscript/docs/' if folder==P else 'docs/'
    text=f'''# Agent side-channel SoK — Defense Evidence

R41 将统计范围明确限定为 C1–C5 纳入、含经验攻击推断评估的研究中所报告的缓解结果，并按干预实际改变的功能重新确定 R8 适用性。本轮新增模型请求为 0。

- 在这一来源框架的 52 个 Type I/II 核心家族中，19 家族关联 31 条缓解记录；33 家族在本次抽取中没有关联的合格缓解记录。这不是全部防御文献的普查；纳入来源既有攻击导向研究，也有防御导向研究。
- 对窄范围内容或逻辑功能质量，8 个适用家族中有 3 个明确绑定测量，接受部分证据后为 4/8；另 11 个家族对该质量查询不适用。保持内容的 framing、精确计算及隔离返回路径不能据此获得时限、超时或端到端任务完成保证。
- UI Traces、WRA、Dangol 和 cloud benchmark 四个 agent-associated 家族中，没有关联同条件端到端任务评分（0/4）；这不是四个都会改变执行的隐私 cover。WRA 的原始回答路径可支持窄内容保持，其新增诱饵执行的同条件任务评分仍未绑定（0/1）。Cloud 的 prompt/temperature 干预属于生成质量适用子集，明确测量为 0/1，接受部分证据为 1/1。
- 15/16 适用来源家族明确绑定推断结果，11/18 绑定成本，2/10 绑定匹配的受保护数据拟合对照；这些项目各自保留其适用分母。
- 同一受保护测试视图中，缓冲分桶从未适应攻击的 50.0% 升至重新拟合后的 70.8%；流式分批从 50.0% 升至 100.0%，恒定事件数对照保持 50.0%。结果限定于已有运输层示例。
- 补充材料保留 WRA/GLM 两轮探索及其截断：它们没有简单/适应性攻击的配对对照，不能据此声称 WRA 的适应性恢复或在线防御效果。原始记录和历史实验保留。

主稿 {v['pdfs']['main']['pages']} 页、正文至第 13 页；补充材料 {v['pdfs']['supplement']['pages']} 页。R8 当前分母、联合查询和来源删除敏感性由 `{src}tools/r41_utility_scope.py` 复算，记录级适用性和定位符见 `{src}data/r41-utility-scopes.json`，修订说明见 `{doc}R41-P0范围与效用适用性修正.md`。原 351 格审计及此前实测结果仍可追溯。

[主稿]({pdf}main.pdf) · [补充材料]({pdf}supplement.pdf)
'''
    (folder/'README.md').write_text(text,encoding='utf8',newline='\n')

save(O/'metadata-registration.json',{'revision':'r41-scope-and-utility','base_commit':load(O/'revision.json')['base_commit'],
 'goal':'Limit mitigation reporting to the C1-C5 attack-evaluation source frame and distinguish narrow functional quality from executed-task outcomes',
 'selection_scope':'Mitigation results in empirically attack-evaluated LLM and agent studies, including attack-oriented and defense-oriented sources; not all defense literature',
 'quality_applicability':{'explicit_bound':3,'partial_accepted':4,'applicable_families':8,'exempt_families':11},
 'agent_task_score_inventory':{'bound':0,'families':4,'scope':'UI Traces, WRA, Dangol and the cloud benchmark; not four execution-changing covers'},
 'wra_executed_task_score':{'bound':0,'applicable_families':1,'narrow_real_output_preservation':True},
 'cloud_generation_quality':{'explicit_bound':0,'partial_accepted':1,'applicable_families':1},
 'incomplete':['Online WRA protection/utility/cost evaluation','WRA matched attack-adaptation contrast'],
 'new_experiments_requested':False,'archived_source_cells_preserved':True,
 'new_applicability_overlay':True,'new_model_calls':0})
print('R41_METADATA_REGISTERED')
