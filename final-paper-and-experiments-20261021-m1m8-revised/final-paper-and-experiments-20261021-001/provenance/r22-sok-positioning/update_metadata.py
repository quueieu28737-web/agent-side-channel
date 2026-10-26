"""Register the editorial release without changing experimental evidence."""
from pathlib import Path
from datetime import datetime,timezone
from pypdf import PdfReader
import json,hashlib,sys,re
O=Path(__file__).resolve().parent; P=O.parents[1]; M=P/'manuscript'; R=P.parents[1]
sys.path.insert(0,str(P)); from verify_package import closure
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
s=load(P/'provenance/snapshot.json')
s['purpose']='R22: defense-evidence-transfer SoK, strengthened whole-ledger synthesis and condensed supporting studies'
for name in ['main','supplement']:
    s['documents'][name]['closure']=closure(M,name+'.tex')
    s['documents'][name]['pdf_sha256']=sha(P/'pdf'/(name+'.pdf'))
names=set(n for d in s['documents'].values() for n in d['closure'])
s['source_hashes']={n:sha(M/n) for n in sorted(names)}
s['current_manuscript']={'revision':'R22-sok-positioning','main':'pdf/main.pdf','supplement':'pdf/supplement.pdf',
    'scope':'Editorial restructuring: record/holdout synthesis leads, controlled studies support deployment decisions; no new experiments and no changes to scientific records'}
s['updated_utc']=datetime.now(timezone.utc).isoformat(); save(P/'provenance/snapshot.json',s)
a=load(P/'artifact-index.json')
a['modules']['r22-sok-positioning']={'description':s['purpose'],'paths':['provenance/r22-sok-positioning/verification.json','provenance/r22-sok-positioning/visual-check.json','provenance/r22-sok-positioning/anonymous-paper-check.json','manuscript/sections/61-synthesis-study-details.tex']}
old=a['current_verification']
if old!='provenance/r22-sok-positioning/verify_revision.py' and old not in a['historical_document_verifiers']:a['historical_document_verifiers'].append(old)
a['current_verification']='provenance/r22-sok-positioning/verify_revision.py'
a['current_publication']=list(dict.fromkeys(a['current_publication']+['provenance/r22-sok-positioning/verify_revision.py','provenance/r22-sok-positioning/verification.json']))
save(P/'artifact-index.json',a)
pages={n:len(PdfReader(M/(n+'.pdf')).pages) for n in ['main','supplement']}
refs=next(i+1 for i,p in enumerate(PdfReader(M/'main.pdf').pages) if 'References' in p.extract_text())
for p in [P/'README.md',R/'README.md']:
    text=p.read_text(encoding='utf8')
    text=text.replace('防御效果的迁移边界','防御证据迁移')
    text=re.sub(r'主稿 \d+ 页',f"主稿 {pages['main']} 页",text)
    text=re.sub(r'补充材料 \d+ 页',f"补充材料 {pages['supplement']} 页",text)
    text=re.sub(r'正文在第 \d+ 页进入 References',f'正文在第 {refs} 页进入 References',text)
    text=text.replace('最新 R21','R21')
    text=text.replace('provenance/r21-calibration-stability/anonymous-paper-source.zip','provenance/r22-sok-positioning/anonymous-paper-source.zip')
    note='最新 R22 明确定位为“以防御证据迁移为主线、由受控实验支撑的 SoK”。摘要、贡献声明、Table 1 与结论统一为证据识别、受控测量和部署决策；§8 源文本压缩约 43%，七组详细结果在补充 S31 中收录或索引。39 条记录审计、联合绑定与六轴 holdout 的系统综合得到扩充，原始数据、统计结果及编码保持不变。\n\n'
    if '最新 R22 明确定位' not in text:text=text.replace('## 复现与校验',note+'## 复现与校验')
    if p==R/'README.md' and '[R22 定位与篇幅修订]' not in text:
        text=text.replace('[R19 逐项修订与验收说明]', '[R22 定位与篇幅修订](docs/R22-证据迁移SoK定位与篇幅重构.md)\n\n[R19 逐项修订与验收说明]')
    p.write_text(text,encoding='utf8',newline='\n')
print('R22_METADATA_UPDATED',pages,refs)
