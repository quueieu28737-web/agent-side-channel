"""Write one current release guide; preserve prior README editions separately."""
from pathlib import Path
import json,shutil
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,text):p.write_text(text.strip()+'\n',encoding='utf8',newline='\n')
for base,name in ((R,'prior-root-readme.md'),(P,'prior-package-readme.md')):
 if not (O/name).exists():shutil.copyfile(base/'README.md',O/name)
C=read(P/'experiments/sp2027-r7-crossfit/detailed_results.json')
A=read(P/'experiments/sp2027-r7-agent-extension/formal_validation.json')
assert A['complete'] and A['runs']==150
pages={n:len(PdfReader(P/'pdf'/(n+'.pdf')).pages) for n in ('main','supplement')}
def pair(condition):
 vals=[next(v for v in C['results'] if (v['prompt'],v['condition'],v['target'])==('baseline',condition,t)) for t in ('cancel','return')]
 return '/'.join(f"{v['suite_ba']*100:.1f}%" for v in vals)
pkg=P.relative_to(R).as_posix()
root=f'''# agent-side-channel

## 当前版本：R7 强化攻击、流量对照与逐项审稿修订

- [主稿](main.pdf)：正文不超过13页，全文{pages['main']}页；References在Appendix之前。
- [补充材料](supplement.pdf)：{pages['supplement']}页，S20为强化Timing攻击/经典WF适配/功效规划，S21为强化交叉拟合和写调用消融，S22为新增Luna研究。
- [逐项验收清单](docs/R7-逐项修改验收清单.md)：覆盖T1–T13全部40个子项，明确已完成工作与尚需外部资源的要求。
- [完整源码与数据包]({pkg}/README.md)：当前校验、环境、归档与复算入口。

### 当前证据

1. **SoK贡献**：82个研究族、39条结果记录、58族主文映射和20×9审计矩阵。可信度来自记录与原文定位符的绑定；κ明确为非独立的提取—作者复核一致性。公开来源复核修正3个状态，仍有11个未核实绑定。
2. **主描述性结果**：原690次Sol运行的客户五折交叉拟合，53客户。11攻击器union下，标准提示组未防御BA为{pair('undefended')}，联合恒定分帧为{pair('jointconstant')}，联合分桶为{pair('jointbucket1024')}。配对降幅仍明确；绝对阈值未获确认。两prompt与所有运行点完整保留。
3. **Timing与成本**：E13保留4,140个实测本地工具TLS会话。E14在同一轨迹上评估13种条件、52个prompt/目标单元，增加CNN与k-FP类攻击并保留旧suite。312个新学习器已另行重训，预测逐项一致。Tamaraw、FRONT、WTF-PAD、Walkie-Talkie提供明确的RPC适配。成本图以共同7攻击器作匹配比较，另保留完整攻击并集结果；实测RPC时延与离线调度跨度分面展示。
4. **新模型实采**：另有150次正式GPT-6 Luna/low运行（75个旧retail任务×2prompt），10次试点另列。58训练/92测试轨迹、10/24个不重叠客户；每prompt攻击训练29条、测试46条。正式reward逐次在新sandbox重算，原始模型证据以可核验归档提供。它是同厂商、同环境、旧客户的补充，不替代跨厂商或新环境验证。

### 解读范围

“实验与文件校验通过”不等于“绝对安全阈值通过”。模型名称是服务返回的别名。网络结果区分原始模型轨迹、本地TLS回放、live工具执行与离线WF变换；程序条件的reward复用不等于实测live-cover重规划。规则prompt是机械读序控制。

尚未获得：第二环境、固定开源权重、不同厂商模型、新增独立阳性客户、live cover下的LLM重规划对照、两位外部盲审编码者。这些要求逐项列入清单与前瞻协议，未用重复运行或AI复核替代。

### 校验与复算

在源码与数据包目录运行：

```text
python -B provenance/r7-review/verify_publication.py
python -B verify_package.py
python -B verify_revision.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

当前入口是`provenance/r7-review/`。较早`timing/`、`review-closure/`、`sok-restructure/`中的文稿校验器绑定旧版页数与表述，保留作历史记录。详细实验重算命令及依赖见包README和各实验目录README；均不需要重新调用LLM。

### 历史保存与投稿

原690运行、663快照、R2/R3/R5/R6数据和旧ZIP发布包保留原样；它们的页数、结果表与写作说明属于相应历史版本。旧根/包README保存在本轮provenance中，避免多个版本同时标为“当前”。当前交付以本提交的两份PDF、源文件、`SHA256SUMS.json`及校验收据为准。

[S&P 2027合规核对](docs/R7-SP2027-合规核对.md)列出页数、伦理、AI披露与Open Science事项。公开Git仓库不是匿名投稿快照；作者仍需准备匿名、不可变的审稿工件并完成HotCRP身份/COI与伦理字段。
'''
write(R/'README.md',root)
guide=f'''# Current R7 paper and reproducibility package

Current PDFs: `pdf/main.pdf` ({pages['main']} pages; main body at most 13) and `pdf/supplement.pdf` ({pages['supplement']} pages). LaTeX is in `manuscript/`. References precede the appendix. `artifact-index.json` resolves logical modules to preserved physical archives.

## Evidence and current analysis

- Original Sol cohort: 690 real runs, 115 tasks, 53 customers, two prompt arms, three repeats. The original 414/276 split and calibration remain unchanged.
- Primary E10 update: 11 attacks, complete customer five-fold cross-fitting, 60 fitted packs and 45,540 score checks. Standard-prompt BA: undefended {pair('undefended')}; joint constant {pair('jointconstant')}; joint buckets {pair('jointbucket1024')}. The paired decreases and absolute gate are separate outcomes.
- E13/E14: 4,140 saved live tool sessions; 13 measured/simulated conditions and 52 evaluation cells. All 312 new learned models were exactly refit and reloaded. The cost plot matches the seven common attacks and separately retains larger full-union maxima; unequal attack unions cannot establish matched dominance. Actual tool clocks and simulated WF schedules are not interchangeable.
- E12: a separately frozen stronger oracle write-call ablation in `sp2027-r7-localization`, retaining the original folds and full old attack union. Oracle filtering is diagnostic, not a deployable defense.
- Additional Luna collection: 150 formal runs, 75 existing tasks, two prompts, one repeat; 58 training and 92 test trajectories, 10/24 customers. Each prompt-specific attacker fits 29 training examples and tests 46. The 10 pilot runs are separate. These are same-provider model aliases and the same environment, not cross-vendor/open-weight/new-customer validation.
- Source audit: three publicly justified status corrections are an explicit overlay on preserved prior tables and coding columns; 11 bindings remain unverified. No independent-human reliability claim is made.

## Current checks

From this package directory:

```text
python -B provenance/r7-review/verify_publication.py
python -B verify_package.py
python -B verify_revision.py
python -B experiments/sp2027-r4-full-20261023/verify_release.py
```

The package check uses SHA-256 for every publication file and the live LaTeX closure. It excludes only the original local collector directory `experiments/sp2027-r4` and Python bytecode caches. Earlier document-specific verifiers retain earlier layouts and should not be applied to the current PDFs. Prior experiment verifiers remain valid for their immutable inputs.

## Local reproduction without LLM calls

```text
python -B experiments/sp2027-r7-robustness/verify.py
python -B experiments/sp2027-r7-robustness/run.py reproduce
python -B provenance/r7-review/retrain_robustness.py
python -B experiments/sp2027-r7-crossfit/verify.py
python -B experiments/sp2027-r7-localization/verify.py
python -B experiments/sp2027-r7-agent-extension/verify_public.py --network
```

Check each module's README for exact versions and command working-directory requirements. Experimental dependencies include NumPy, SciPy, scikit-learn, CPU PyTorch and cryptography; pypdf is needed for document checks and matplotlib for plot regeneration. Exact frozen runtime versions are saved in each experiment. Public raw evidence redacts only the local home-directory prefix with original/public hashes and replacement counts. Scientific observations, model names, decisions, actions and scores are retained. Luna public-ZIP verification additionally requires the hash-checked benchmark/tool sources in this checkout; the ZIP alone is not a standalone package. Tool counters distinguish registered-name dispatch attempts (including failed calls), unknown-name attempts and model calls.

Rebuild with standard IEEEtran 1.8b (conference, compsoc), pdfLaTeX and BibTeX:

```text
python -B provenance/r7-review/build_pdfs.py
```

The `--publish-copies` option additionally updates the root/package PDF copies and normalized compiler logs. It does not update the package manifest automatically; published checksums describe the delivered build. Rendering receipts record inspected PDF hashes. Plot/table generators support read-only `--check` as documented.

## Archive map and limits

The full Sol release and 663 snapshot, R2/R3/R5/R6 experiments, old coding records and prior ZIPs remain immutable. `provenance/r7-review/prior-package-manifest.json` and the history check verify preservation. `prior-root-readme.md` / `prior-package-readme.md` retain earlier guides. `reviewer-comments.txt`, the 40-item coverage index, author attestation, source overlay and current validation receipts explain each change.

Data validation is not an absolute-security certification. No configuration in E14 meets the original absolute criterion. Same-provider extra runs do not supply a second environment, fixed open weights, different-vendor data, new positive customers, live-cover planner utility or two external human coders. The prospective protocol specifies those remaining studies without claiming they have been run. Model archives use trusted Python serialization and should not be loaded from an untrusted source.
'''
write(P/'README.md',guide)
print('CURRENT_RELEASE_GUIDES_WRITTEN')
