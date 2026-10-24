"""Write one current R8 release guide; preserve prior guides."""
from pathlib import Path
import shutil
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
def write(p,s):p.write_text(s.strip()+'\n',encoding='utf8',newline='\n')
for folder,name in [(R,'prior-root-readme.md'),(P,'prior-package-readme.md')]:
 if not (O/name).exists():shutil.copyfile(folder/'README.md',O/name)
pages={n:len(PdfReader(P/'pdf'/(n+'.pdf')).pages) for n in ['main','supplement']}
pkg=P.relative_to(R).as_posix()
write(R/'README.md',f"""
# agent-side-channel

## 当前版本：R8 证据迁移、构念有效性与公平对照

- [主稿](main.pdf)：正文不超过13页，全文{pages['main']}页；References在Appendix之前。
- [补充材料](supplement.pdf)：{pages['supplement']}页。S23集中呈现本轮客户敏感性、自身效用审计、匹配成本对照、适用性审计和同操作商品属性分析。
- [逐项修改与未解决问题](docs/R8-逐项修改与未解决问题.md)：逐项区分已完成、部分解决与需要新数据的事项。
- [投稿文件与AI披露](docs/R8-投稿文件与AI披露.md)：论文源码匿名包与正式投稿尚需完成的事项。
- [源码和数据包]({pkg}/README.md)：当前校验、冻结数据、分析协议与复算入口。

### 本轮实质改动

1. **SoK贡献**：82研究族、58核心族主文映射、39条来源绑定记录及20×9审计矩阵。三类具体跨记录误用是前端重新发射、读掩护跨到状态写入、不同机制间借用效用/成本。R1–R9评价复用证据条件，不给原论文打质量分。
2. **实验目标核查**：cancel/return来自参考操作，写调用消融是操作类别定位，不是隐含商品属性的新发现。新属性实验固定同为单商品退货：15客户、20独立订单商品实例，冻结语义映射，沿用客户五折，150模型和600分数通过独立重载校验。结果不足以建立稳定的非操作属性泄漏，完整负面和对照结果保留。
3. **公平比较与自审**：共同7攻击器和最强可用union分列；WT适配在部分点以约2倍字节匹配或优于约15倍shadow。主文展开90.4/92.3% flush检测及剥离后攻击。逻辑状态一致性不再被当成防御下LLM效用实测。
4. **客户影响**：12单元、192次逐阳性客户删除。690运行只代表53客户，14/18阳性客户；客户等权与删除范围不冒充重训置信区间。
5. **数字口径**：E9/E10/E13的观察面、攻击套件及15.39/19.76/15.11倍字节分母分别标明。旧数据、旧表和旧收据保留。

### 当前结论与校验

文件复算通过不等于安全准则通过。未获得新客户确认性安全结论；新环境、不同厂商/固定权重、真实闭环防御下LLM重规划和独立人类重编码仍需新资源。

在数据包目录运行：

~~~text
python -B provenance/r8-review/verify_publication.py
python -B verify_package.py
python -B verify_revision.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
~~~

当前稿件入口是R8。旧版本专属PDF检查脚本保留其历史页数/措辞要求；旧实验验证入口仍有效。匿名论文源码ZIP不是完整实验artifact匿名托管，也不表示已经投稿。
""")
write(P/'README.md',f"""
# Current R8 paper and reproducibility package

Current PDFs: pdf/main.pdf ({pages['main']} pages, body at most 13), pdf/supplement.pdf ({pages['supplement']} pages). Standard IEEEtran conference/compsoc; references precede the appendix. Current closure and hashes are in provenance/snapshot.json, SHA256SUMS.json and artifact-index.json.

## Evidence hierarchy

The SoK contributes 82 families and 39 source-bound result records, with a 58-family map and 20-by-9 applicability-aware main-paper audit. Concrete transfer errors concern re-emission, execution/state and mismatched evaluation/utility/cost objects. R1–R9 are reuse-evidence conditions rather than paper-quality scores.

The original Sol collection is 690 runs, 115 tasks and 53 customers. E9 freezes calibration before test collection; development had the full population. E10–E14 are exploratory known-cohort extensions. The prior 150-run Luna study is same-provider and same-environment. R8 adds no LLM calls or customers.

## New analysis

- experiments/sp2027-r8-cluster-sensitivity: 12 fixed-prediction cells, 192 positive-customer deletions and customer-class-equal weighting. These measure influence, not refitting uncertainty or new confidence intervals.
- experiments/sp2027-r8-sensitive-attributes: exact call/record alignment, same-operation/single-item strata, fixed researcher-defined semantic grouping, old customer folds, repeat aggregation and negative controls. Each prompt has 20 instances and 15 customers; there are not 138 independent calls. Frozen fitting and independent score reloading do not provide stable above-chance evidence for the selected attribute.
- provenance/r8-review/defense-self-audit.json: matched seven-model costs, full unions, flush removal and our own utility evidence boundary.
- provenance/r8-review/family-status-overlay.csv: per-family applicability. Unverified source bindings are separate from negative experiments.
- provenance/r8-review/all-citations-form-labels.csv: all 77 cited forms, including 49 arXiv-only and 21 venue-labelled (five also with preprints). These labels do not independently certify peer review.

## Validation and rebuilding

~~~text
python -B provenance/r8-review/verify_publication.py
python -B provenance/r8-review/make_tables.py --check
python -B experiments/sp2027-r8-cluster-sensitivity/verify.py
python -B experiments/sp2027-r8-sensitive-attributes/verify.py
python -B verify_package.py
~~~

The attribute module records runtime dependencies and a frozen plan. Its verifier reloads trusted serialized models and recomputes scores; never load such models from an untrusted source. No API key or model call is needed. R7 dependency closures and receipts remain bound to their original experiments.

Rebuild using Python provenance/r8-review/build_pdfs.py --publish-copies with pdfLaTeX and BibTeX. This updates root/package PDFs and current logs but not release metadata/manifest automatically. Delivered hashes describe the completed publication build.

## Preservation and submission

The prior-package-manifest in provenance/r8-review records all 7,252 prior files; the prior manuscript snapshot and old experiments are byte-checked. R8 permits explicit current manuscript/PDF changes while preserving old experiment code, protocols, data and receipts.

The current checklist records missing external studies: new customers, cross-vendor/open-weight and second-environment transfer, live planner utility under defense, real provider backends, independent human recoding. Neither paired reduction nor state equality certifies security.

provenance/r8-review/anonymous-paper-source.zip contains paper PDFs, LaTeX closure and standard class/style files without Git history or machine logs. It is not the separately hosted anonymous experimental artifact. Conference registration, final author review, conflicts and AI-use declarations remain author submission actions.
""")
print('R8_CURRENT_GUIDES_WRITTEN')
