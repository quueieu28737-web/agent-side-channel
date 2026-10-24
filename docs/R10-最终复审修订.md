# R10 最终复审修订

## 1. M/S 比较契约
摘要、引言、结论及 §8.4 同步修订。同为 M 的 per-call constant 与 serial shadow：3.92× / 15.11× 字节、16.6 / 26.2 ms RPC p95；同时呈现完整攻击套件下 68.6/62.7 与 61.4/53.4 BA，说明成本与推断的权衡。S 模式 WT 的 2.04× 字节仅用于共享七模型下的描述性候选筛选，不称为理论下界或在线优越性。原始数据和表格未改。

## 2. 排版
移除附录前强制分页。主稿 17 页，正文 13 页，参考文献第 13 页开始、附录第 16 页开始。标题顶部约 96.43 pt（3.40 cm），保留 IEEEtran 标准设置，无负间距或缩边距。依据官方 CFP https://sp2027.ieee-security.org/cfpapers.html 核对格式。

## 3. 参考文献
CachePrune 作者 Zhaohan li 修正为 Zhaohan Li。所有当前编译使用的 BibTeX 标题保护 LLM/LLMs、KV、GPU/GPUs、CPU、TDX、NVIDIA、MIG、ORAM、RAG、AI、UI、Intel 等原有大写专名；同步重编译主稿和补充材料。

## 校验
主稿 17 页、补充材料 52 页已渲染并目视检查。校验脚本检查源数据/表格/图件保持不变、发布副本一致、编译诊断、页数/附录位置、姓氏/缩写和比较契约。结果见 provenance/r10-review/validation.json。R9 记录作为历史校验保留；当前入口为 R10。无新增模型调用或实验。
