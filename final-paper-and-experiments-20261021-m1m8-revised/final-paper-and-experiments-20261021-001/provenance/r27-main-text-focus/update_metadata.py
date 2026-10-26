"""Register the editorial R27 publication while retaining R26 evidence receipts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
rev='r27-main-text-focus'
s=read(P/'provenance/snapshot.json');s['purpose']='R27: remove main Section 8.3 and condense source-record methodology; preserve the SoK evidence and appendix statistics'
for n in ['main','supplement']:
 s['documents'][n]['closure']=closure(M,n+'.tex');s['documents'][n]['pdf_sha256']=sha(M/(n+'.pdf'))
names={n for doc in s['documents'].values() for n in doc['closure']}
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':rev,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Editorial condensation of the main paper. Literature records, quantitative results and supplementary evidence unchanged.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=read(P/'artifact-index.json');old=a['current_verification'];cur='provenance/'+rev+'/verify_revision.py'
if old!=cur and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=cur;a['current_publication']=list(dict.fromkeys(a['current_publication']+[cur,'provenance/'+rev+'/verification.json']))
a['modules'][rev]={'description':s['purpose'],'paths':['provenance/'+rev+'/'+n for n in ['verification.json','visual-check.json','anonymous-paper-check.json']]}
save(P/'artifact-index.json',a)
v=read(O/'verification.json');m=v['pdfs']['main'];sp=v['pdfs']['supplement']
for dest in [R/'README.md',P/'README.md']:
 t=dest.read_text(encoding='utf8');t=t.replace('当前文稿核验为 `provenance/r26-source-reconciliation/verify_revision.py`','当前文稿核验为 `provenance/r27-main-text-focus/verify_revision.py`')
 start=t.index('主稿 ',t.index('## 当前交付'))
 end=t.index('。',start)
 t=t[:start]+f"主稿 {m['pages']} 页，正文止于第 {m['main_body_last_page']} 页；补充材料 {sp['pages']} 页"+t[end:]
 if 'R27 按用户要求' not in t:t=t.replace('## 当前交付','## 当前交付\n\nR27 按用户要求删除主稿 §8.3，将 §2.3 精简为三句来源说明。SoK 主线、审计数据和补充材料保持不变。',1)
 t=t.replace('docs/R26-RQ3与原文证据收敛.md','docs/R27-主文表述收敛.md').replace('[本轮修订与校验](provenance/r26-source-reconciliation/verification.json)','[本轮修订与校验](provenance/r27-main-text-focus/verification.json)')
 dest.write_text(t,encoding='utf8',newline='\n')
(R/'docs/R27-主文表述收敛.md').write_text(f"# R27：主文表述收敛\n\n- 删除主稿 §8.3 全节；第 8 节标题改为 Implications and Ethics。\n- §2.3 精简为三句话，说明来源版本与定位符、作者核验和记录索引。\n- 记录级比较、配置级联合绑定、部署决策三项 SoK 主线保持一致。\n- 审计数据、数值表格、附录统计和补充材料逐字节保留；未增加实验。\n- 主稿 {m['pages']} 页，正文止于第 {m['main_body_last_page']} 页。引用闭包、编译、PDF 副本与发布清单已检查。\n",encoding='utf8',newline='\n')
print('R27_METADATA_REGISTERED')
