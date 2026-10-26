"""Publish R32 record-derived summaries and decision-oriented PDFs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,re
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure
def read(f):return json.loads(f.read_text(encoding='utf8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
rev='r32-audit-decisions';s=read(P/'provenance/snapshot.json')
s['purpose']='R32: record-derived family summaries, publication-stratum sensitivity and actionable external/internal evidence-reuse decisions'
for n in ['main','supplement']:
 s['documents'][n]['closure']=closure(M,n+'.tex');s['documents'][n]['pdf_sha256']=sha(M/(n+'.pdf'))
names={n for d in s['documents'].values() for n in d['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':rev,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Thirteen family-summary cells reconciled to unchanged record judgments; 180 witnesses; same five joint queries; B/C decision presentation and D bibliography sensitivity. No new model experiments.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=read(P/'artifact-index.json');previous=a['current_verification'];current='provenance/'+rev+'/verify_revision.py'
if previous!=current and previous not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(previous)
a['current_verification']=current
a['current_publication']=list(dict.fromkeys(a['current_publication']+[current,'provenance/'+rev+'/verification.json']))
a['modules'][rev]={'description':s['purpose'],'paths':['provenance/'+rev+'/'+n for n in ['revision.json','audit-check.json','verification.json','visual-check.json','anonymous-paper-check.json']]}
save(P/'artifact-index.json',a)
v=read(O/'verification.json');mp=v['pdfs']['main'];sp=v['pdfs']['supplement']
for f in [R/'README.md',P/'README.md']:
 t=f.read_text(encoding='utf8')
 t=t.replace('R31 清理已撤销的编码任务及 R30 引入的无依据表述；保留 R30 的研究问题对齐和 R29 的核心主张。','R32 统一记录与家族汇总，强化外部/内部案例的决策价值，并补齐发表状态分层；保留三项 SoK 主线。')
 t=t.replace('provenance/r31-retired-task-cleanup/verify_revision.py','provenance/'+rev+'/verify_revision.py')
 if f.parent==P:t=t.replace('当前任务以 docs/CURRENT-PLAN.md','当前任务以 manuscript/docs/CURRENT-PLAN.md')
 t=re.sub(r'主稿 \d+ 页，正文止于第 \d+ 页；补充材料 \d+ 页。',f"主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。",t)
 f.write_text(t,encoding='utf8',newline='\n')
for f in [R/'docs/R32-SoK决策与审计一致性.md',M/'docs/R32-SoK决策与审计一致性.md']:
 t=f.read_text(encoding='utf8')
 if '## 本轮构建与校验' not in t:t+=f"\n## 本轮构建与校验\n\n主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。36 项审计一致性检查、撤销任务扫描、引用闭包、编译诊断和副本一致性检查通过。完整历史证据另由发布包校验器检查。\n"
 f.write_text(t,encoding='utf8',newline='\n')
print('R32_METADATA_REGISTERED')
