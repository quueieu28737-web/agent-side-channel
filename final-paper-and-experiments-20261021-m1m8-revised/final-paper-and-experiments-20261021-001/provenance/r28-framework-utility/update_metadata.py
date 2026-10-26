"""Register the R28 documentary check without changing earlier evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,shutil
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/"manuscript"
sys.path.insert(0,str(P));from verify_package import closure
def read(f):return json.loads(f.read_text(encoding="utf8"))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8",newline="\n")
rev="r28-framework-utility"
s=read(P/"provenance/snapshot.json")
s["purpose"]="R28: retrospective external evidence-routing check and current reassessment of seven time-ordered internal judgments"
for n in ["main","supplement"]:
 s["documents"][n]["closure"]=closure(M,n+".tex");s["documents"][n]["pdf_sha256"]=sha(M/(n+".pdf"))
names={n for d in s["documents"].values() for n in d["closure"]}
s["source_hashes"]={n:sha(M/n) for n in sorted(names)}
s["current_manuscript"]={"revision":rev,"main":"pdf/main.pdf","supplement":"pdf/supplement.pdf",
 "scope":"15 external measurement records, not blinded prediction validation; seven existing judgments reassessed. Original literature audit and experiments retained."}
s["updated_utc"]=datetime.now(timezone.utc).isoformat();save(P/"provenance/snapshot.json",s)
a=read(P/"artifact-index.json");old=a["current_verification"];cur="provenance/"+rev+"/verify_revision.py"
if old!=cur and old not in a["historical_document_verifiers"]:a["historical_document_verifiers"].append(old)
a["current_verification"]=cur
a["current_publication"]=list(dict.fromkeys(a["current_publication"]+[cur,"provenance/"+rev+"/verification.json"]))
a["modules"][rev]={"description":s["purpose"],"paths":["provenance/"+rev+"/"+n for n in ["verification.json","visual-check.json","anonymous-paper-check.json"]]+["experiments/sp2027-r28-validation/README.md","experiments/sp2027-r28-validation/verify.py"]}
save(P/"artifact-index.json",a)
v=read(O/"verification.json");mp=v["pdfs"]["main"];sp=v["pdfs"]["supplement"]
text=f"""# R28：框架有用性核验与七条判断回写

## 本轮完成

- 主文 §7.6 新增外部回溯核验 B，覆盖 DF、WFDefProxy、Mathews 三项重评估中的 15 条测量记录、14 个防御—研究组合；包含四个保留效果的对照。
- B 的可操作产出是区分保护结果、执行边界与成本，说明哪些结果保留、哪些测量补做。此次为可见结局的文献回溯，不是原提案中的独立盲评预测实验；未声称命中率、显著预测优势或独立编码。
- 主文 §7.7 和 Table 14 展示全部七条内部判断。重新核验后：4 条支持，1 条部分支持，P5 源保护前提不成立，P7 未确立。没有沿用旧的“五条证实”。
- 核验登记提交在结果提交之前、登记内容未变、早期树中无实验结果。此证据证明仓库顺序，不冒充独立执行时间戳。
- 补充 S35 提供完整外部记录、定位符、比较规则和修订理由。附录 E 与原统计保留，不用 Holm p=1.000 论证框架有效。
- 39 条记录、351 格、180 家族格、741 对及原实验不变。R3 184 组预测及区间重算通过；外部来源哈希/数值检查、引用闭包、匿名源码包检查通过。
- 主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充 {sp['pages']} 页。根目录与发布包 PDF 一致。

## 复现入口

完整实验工件位于 agent-side-channel 仓库发布包的 experiments/sp2027-r28-validation。
运行 analyze.py 重建外部账本和 Git 顺序收据，verify.py 检查结果。
本轮未调用新模型，也未新增独立客户。B 的独立盲评预测版本仍需另行执行，不能用本次回溯替代。
"""
(R/"docs/R28-框架有用性与七条判断.md").write_text(text,encoding="utf8",newline="\n")
(M/"docs").mkdir(exist_ok=True);(M/"docs/R28-框架有用性与七条判断.md").write_text(text,encoding="utf8",newline="\n")
summary=f"""# Agent side-channel SoK — Defense Evidence Transfer

当前稿以记录级比较、配置级联合绑定和部署决策为主线。R28 增加外部回溯核验和七条内部判断，保留 R26 原文复核及 R27 主文收敛。

## 关键结果

- 文献审计：82 家族、39 记录、741 对库存；133 个相关对中 17 个描述性匹配。
- 原文复核的 11 个待核家族格调整为 4 P、7 U；联合绑定计数不变。
- 新增 B：三项外部重评估、15 条测量记录、四个正面对照；属于可见结局的回溯核验，尚非独立盲评预测验证。
- C 当前汇总：4 支持、1 部分支持、1 源前提不成立、1 未确立。登记/结果的 Git 顺序已核对。
- 本轮新增模型调用和客户均为 0。原始实验与完整统计保留。

## 当前交付

主稿 {mp['pages']} 页，正文止于第 {mp['main_body_last_page']} 页；补充材料 {sp['pages']} 页。根目录、manuscript 和发布包 pdf 中的 PDF 一致。

运行发布包的 python verify_package.py 核验清单、数据及源码/PDF 绑定。当前文稿核验为 provenance/r28-framework-utility/verify_revision.py。匿名源码包只包含论文与补充材料，完整实验托管仍需单独匿名快照。

[主稿](main.pdf) · [补充材料](supplement.pdf)
"""
for f in [R/"README.md",P/"README.md"]:f.write_text(summary,encoding="utf8",newline="\n")
print("R28_METADATA_REGISTERED")
