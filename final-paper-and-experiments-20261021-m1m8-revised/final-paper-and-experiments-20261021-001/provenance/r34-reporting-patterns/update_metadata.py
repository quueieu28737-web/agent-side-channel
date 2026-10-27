"""Register R34 manuscript and reporting-pattern delivery provenance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P));from verify_package import closure
def load(f):return json.loads(f.read_text(encoding='utf8'))
def h(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
rev='r34-reporting-patterns';v=load(O/'verification.json');checks=load(O/'reporting-check.json')
assert v['passed'] and checks['status']=='R34_REPORTING_ACCOUNTING_PASS'
s=load(P/'provenance/snapshot.json')
s['purpose']='R34: source-scoped SoK reporting patterns, status/applicability/removal sensitivities and deployment implications; fixed scientific judgments and raw data'
for name in ['main','supplement']:
 s['documents'][name]['closure']=closure(M,name+'.tex');s['documents'][name]['pdf_sha256']=h(M/(name+'.pdf'))
names={n for d in s['documents'].values() for n in d['closure']}
s['source_hashes']={n:h(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':rev,'main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'Reporting patterns foregrounded; pair census moved to appendix; all record/pair judgments and raw observations preserved.'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json');old=a['current_verification'];current='provenance/'+rev+'/verify_revision.py'
if old!=current and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']=current
a['current_publication']=list(dict.fromkeys(a['current_publication']+[current,'provenance/'+rev+'/verification.json']))
a['modules'][rev]={'description':s['purpose'],'paths':['provenance/'+rev+'/'+n for n in ['revision.json','revision-items.json','verify_reporting.py','reporting-check.json','verification.json','visual-check.json','anonymous-paper-check.json','standalone-reproduction.json']]}
save(P/'artifact-index.json',a)
for folder in [R,P]:
 prefix='manuscript/' if folder==P else ''
 pdf='pdf/' if folder==P else ''
 t=f'''# Agent side-channel SoK — Reusing Defense Evidence

当前R34围绕来源中可核查的报告实践、同配置证据和部署测量计划。任务以{prefix}docs/CURRENT-PLAN.md为准，历史清单不恢复已撤销任务。

## 当前综合

- 82家族地图；20家族的33条缓解记录，另6条背景记录。
- 明确推断16/17、效用4/17、匹配自适应2/11；接受P后17/17、6/17、2/11。统一14家族中推断/成本/效用为13/6/3，宽松14/10/5。
- Agent隐私/归因子集0/4明确、2/4部分效用；保护与成本明确绑定时5/8家族分属不同记录，P口径下为3/12。
- 33条缓解记录的执行型为14条；网络观察子集6执行/4变换/2位置未确认，避免误称回放占多数。
- 原记录、编码、pair判断和实验不变；新增确定性状态、适用性与成员排除敏感性。没有新增独立编码或模型实验。

## 当前交付

主稿{v['pdfs']['main']['pages']}页，正文至第{v['pdfs']['main']['main_body_last_page']}页；补充材料{v['pdfs']['supplement']['pages']}页。根目录、manuscript与包pdf副本一致。

`python tools/reporting_patterns.py`从manuscript内复算F1–F6；发布包`python verify_package.py`检查完整清单。当前文稿检查为`provenance/{rev}/verify_revision.py`，报告实践复算为`verify_reporting.py`。匿名源码包仅覆盖论文与补充材料；完整实验托管仍需单独匿名快照。

[主稿]({pdf}main.pdf) · [补充材料]({pdf}supplement.pdf)
'''
 (folder/'README.md').write_text(t,encoding='utf8',newline='\n')
for f in [R/'docs/R34-A1-F1-F6-报告实践修订.md',M/'docs/R34-A1-F1-F6-报告实践修订.md']:
 t=f.read_text(encoding='utf8')
 if '## 发布检查' not in t:t+=f'\n## 发布检查\n\n主稿{v["pdfs"]["main"]["pages"]}页（正文至13页）、补充{v["pdfs"]["supplement"]["pages"]}页。36项原审计检查、{checks["checks"]}项报告实践复算、引用与PDF副本检查通过；源记录与全部实验保留。视觉、独立目录复现和完整包清单结果分别存档。\n'
 f.write_text(t,encoding='utf8',newline='\n')
print('R34_METADATA_REGISTERED')
