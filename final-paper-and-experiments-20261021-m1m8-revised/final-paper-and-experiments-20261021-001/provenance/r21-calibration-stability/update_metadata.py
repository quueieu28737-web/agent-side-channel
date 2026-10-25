from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,re
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
sys.path.insert(0,str(P));from verify_package import closure
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=read(P/'provenance/snapshot.json');s['purpose']='R21 calibration stability, eight-contrast permutation/Holm analysis and revised transfer attribution'
for name in ['main','supplement']:
    s['documents'][name]['closure']=closure(M,name+'.tex');s['documents'][name]['pdf_sha256']=sha(P/'pdf'/(name+'.pdf'))
source_names=set(n for d in s['documents'].values() for n in d['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(source_names)}
s['current_manuscript']={'revision':'R21-calibration-stability','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf','scope':'100 training-customer calibration resamples, 46000 local TLS captures, full seven-attack refits and corrected conditional contrasts; all original experiments/coding retained'}
s['updated_utc']=datetime.now(timezone.utc).isoformat();save(P/'provenance/snapshot.json',s)
a=read(P/'artifact-index.json');a['modules']['r21-calibration-stability']={'description':s['purpose'],'paths':['experiments/sp2027-r21-calibration-stability/protocol.json','experiments/sp2027-r21-calibration-stability/summary.json','experiments/sp2027-r21-calibration-stability/verification.json','provenance/r21-calibration-stability/verification.json','provenance/r21-calibration-stability/visual-check.json','provenance/r21-calibration-stability/anonymous-paper-check.json']}
previous=a['current_verification']
if previous!='provenance/r21-calibration-stability/verify_revision.py' and previous not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(previous)
a['current_verification']='provenance/r21-calibration-stability/verify_revision.py'
a['current_publication']=list(dict.fromkeys([x for x in a['current_publication'] if not x.startswith('provenance/r10-review/')]+['provenance/r21-calibration-stability/verify_revision.py','provenance/r21-calibration-stability/verification.json']));save(P/'artifact-index.json',a)
pages={n:len(PdfReader(M/(n+'.pdf')).pages) for n in ['main','supplement']}
for p in [P/'README.md',R/'README.md']:
    t=p.read_text(encoding='utf8');t=re.sub(r'主稿 \d+ 页',f"主稿 {pages['main']} 页",t);t=re.sub(r'补充材料 \d+ 页',f"补充材料 {pages['supplement']} 页",t)
    t=t.replace('最新 R20','R20').replace('provenance/r20-claim-conditioned-audit/anonymous-paper-source.zip','provenance/r21-calibration-stability/anonymous-paper-source.zip')
    t=t.replace('配对变化区间分别为 [-12.6,35.3]/[-38.2,-5.3] 个百分点，','历史名义配对区间分别为 [-12.6,35.3]/[-38.2,-5.3] 个百分点；R21 的客户配对置换检验与八重 Holm 校正未确认方向性差异，')
    note='最新 R21 补做 100 次训练客户重采样与 46,000 次实际本地 TLS 捕获，区分校准、攻击器重训及联合波动。原表八个目标级对比各进行 99,999 次客户配对置换，Holm 校正后均未显著；撤回“退货降低已确认”表述。主文保留原始成本/点估计并加入本地校准稳定性，完整分布与统计代码在 `experiments/sp2027-r21-calibration-stability/`。\n\n'
    if '最新 R21 补做' not in t:t=t.replace('## 复现与校验',note+'## 复现与校验')
    p.write_text(t,encoding='utf8',newline='\n')
print('R21_METADATA',pages)
