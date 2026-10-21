from pathlib import Path
import json,shutil,zipfile,difflib,datetime,sys,hashlib
ROOT=Path(__file__).resolve().parent
P=ROOT/'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001'
sys.path.insert(0,str(P));sys.dont_write_bytecode=True
import verify_package as v
prov=P/'provenance';logs=prov/'build-logs';logs.mkdir(exist_ok=True)
for name in ['main','supplement']:
    oldroot=prov/f'root-original-{name}.pdf'
    if not oldroot.exists():shutil.copy2(ROOT/(name+'.pdf'),oldroot)
    shutil.copy2(P/'manuscript'/(name+'.pdf'),P/'pdf'/(name+'.pdf'))
    shutil.copy2(P/'pdf'/(name+'.pdf'),ROOT/(name+'.pdf'))
    shutil.copy2(P/'manuscript'/(name+'.log'),logs/(name+'.log'))
    shutil.copy2(P/'manuscript'/(name+'.blg'),logs/(name+'.blg'))
old=prov/'pre-review-snapshot.json'
if not old.exists():shutil.copy2(prov/'snapshot.json',old)

diff=[]
with zipfile.ZipFile(prov/'pre-review-manuscript.zip') as z:
    oldfiles={n:z.read(n).decode('utf-8-sig') for n in z.namelist() if n.startswith('manuscript/') and n.endswith(('.tex','.bib'))}
for f in sorted((P/'manuscript').rglob('*')):
    if f.suffix not in ['.tex','.bib']:continue
    rel=f.relative_to(P).as_posix();before=oldfiles.get(rel,'');after=f.read_text(encoding='utf-8-sig')
    diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before/'+rel,tofile='after/'+rel))
(prov/'manuscript.patch').write_text(''.join(diff),encoding='utf-8')

(P/'README.md').write_text('''# 审稿意见修订版（2026-10-21）

本包已按两份意见重写主稿、同步补充材料，并从保存输入重跑本地 TLS 和零售工具实验。

- 阅读：`pdf/main.pdf`（18页：13正文＋1附录＋4参考文献）；`pdf/supplement.pdf`（14页）。
- 修订说明：`REVISION-RESPONSE.txt`，逐条对应 A1–A16、B1–B21，并列出没有补做的研究。
- 编辑：`manuscript/main.tex`、`manuscript/supplement.tex`。
- 当前实验：`experiments/reviewer-audit/`；脚本、逐单位结果、预测、区间及混淆矩阵均保留。
- 文本差异：`provenance/manuscript.patch`；原稿备份：`provenance/pre-review-manuscript.zip`。
- 历史证据：`evidence/retained-release007/`和`experiments/revision-m1-m8/`保持历史内容，不能用其中旧摘要覆盖本轮修正。

## 关键改动

T2/T3匹配成本为2.30×/1.43×；训练集定cap为2.18×。旧0.87×/0.91×跨工作负载分母已撤回。
工具测试多数类基线77.55%；取消计数及已知插入位置攻击为100%，撤回隐私—效用前沿主张。
DB、完整账户和reference-changed对象指标分列。39记录覆盖26个家族；20是报告审计家族数。
24场景仅作作者构造示例，不再宣称独立有效性或64.6pp优势。

## 校验与复算

只读校验（Python标准库，不调用模型、不重跑实验）：

```text
python -B verify_package.py
python -B verify_revision.py
```

当前实验重算需要Python 3.10+、numpy、cryptography、pydantic；只运行本地socket和公开模拟数据。

```text
python -B experiments/reviewer-audit/recompute.py tls
python -B experiments/reviewer-audit/recompute.py retail
python -B experiments/reviewer-audit/recompute.py scenarios
```

零售重跑约数分钟，保存6210条任务/种子/位置/策略记录；TLS随机padding包含首次socket及其余49次记录核算。
重跑会更新输出，随后需要更新SHA256清单；原始交付清单是本次保存版本的凭据，不是未来重跑的通用哈希。

LaTeX使用IEEEtran 1.8b conference,compsoc。进入manuscript，分别运行pdflatex、bibtex、pdflatex两次。
当前PDF已编译并检查，无未定义引用/标签和overfull box。日志保存在provenance/build-logs。

## 证据范围

没有自主Agent联合实验、TLS1.3/QUIC/时序攻击、外部独立场景、真实MCP/API普查或新增人工编码。
本包是本地可复查材料，不是匿名线上发布凭据，也不保证论文录用。匿名仓库及作者级来源确认仍需完成。
''',encoding='utf-8')
(P/'experiments/reviewer-audit/README.txt').write_text('''CURRENT REVISION ARTIFACTS

recompute.py tls: local TLS1.2 framing replay and topic-cluster statistics.
recompute.py retail: pinned retail tool replay plus task-cluster observer statistics.
recompute.py scenarios: confusion matrices from supplied author-scenario annotations.
retail_replay.py: instrumented copy of the historical suite used as an import library.

tls_records.json: per-output observed framing, splits, labels, hashes; 24 regime/policy conditions.
tls_gradient.json: absolute bytes/counts and workload-matched cost ratios.
tls_cap.json: training-only length parameter and overflow definition. socket_connections describes the gradient replay cache before additional adaptive first draws.
tls_adaptive*.json: summaries and per-topic/output/draw correctness; 50 stochastic draws.
retail_units.json: 6210 rows, 115 tasks, 3 seeds, 2 positions, 9 policies; ordered dispatch names and response lengths include failures.
retail_utility.json: three reference-state scopes; native_reward is a historical field name for DB equality, not the full evaluator.
retail_observers.json: task-bootstrap accuracy/BA, conditional AUROC, unit confusion matrices, paired gain; 48/49 task split.
retail_predictions.json: every held-out prediction and label, including rules.
retail_diagnostics.json: exact class counts, split task IDs, tool errors and preserved-state unit counts.
same_item_price_check.json: zero-price-difference check on initially successful same-item selections.
combined_result_records.json: 33 historical scoped records plus six explicit expansion records (39 records, 26 families); distinct from the 20-family reporting audit.
scenario_confusions.json: author-constructed scenario illustration; no external-validity claim.

Reproducibility is conditional on the saved source/data and scripts. No fresh model call or production API is made. Historical summaries under revision-m1-m8 remain unchanged and may differ from corrected values. No independence or human-review attestation is inferred from supplied annotation columns.
''',encoding='utf-8')

# Remove only generated build/cache/certificate files in explicitly checked workspace subdirectories.
for directory in [P/'manuscript',P/'__pycache__',P/'experiments/reviewer-audit/__pycache__',P/'experiments/reviewer-audit/local-cert']:
    assert directory.resolve().is_relative_to(P.resolve())
    if directory.exists():
        for f in directory.iterdir():
            if f.is_file() and (directory.name in ['__pycache__','local-cert'] or f.suffix in ['.aux','.out','.log','.blg'] or f.name.endswith('-build.txt') or f.name.endswith('-bib.txt')):f.unlink()

snapshot=json.loads(old.read_text())
snapshot['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
snapshot['purpose']='Reviewer correction: local revised manuscript, saved observations, and conditional statistics; no public hosting or independent human verification claim'
for name in ['main','supplement']:
    snapshot['documents'][name]={'entry':name+'.tex','closure':v.closure(P/'manuscript',name+'.tex'),'pdf':'pdf/'+name+'.pdf','pdf_sha256':v.digest(P/'pdf'/(name+'.pdf'))}
snapshot['source_hashes']={f.relative_to(P/'manuscript').as_posix():v.digest(f) for f in (P/'manuscript').rglob('*') if f.is_file() and f.suffix in ['.tex','.bib']}
snapshot['reviewer_revision']={'retail_rows':6210,'tls_test_topics':12,'new_model_calls':0,'record_count':39,'record_families':26,'audit_families':20}
(prov/'snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
manifest={'algorithm':'SHA-256','files':{f.relative_to(P).as_posix():v.digest(f) for f in sorted(P.rglob('*')) if f.is_file() and f!=P/'SHA256SUMS.json'}}
(P/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Prepared',len(manifest['files']),'manifest files')
