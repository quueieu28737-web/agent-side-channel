# R7 Agent 补充实验：最终事实与可行性

已真实完成同厂商第二模型 gpt-6-luna/low 的150条正式 retail Agent 轨迹（3072次模型决策），另有不混入正式统计的10条试点与2次连通调用。Codex CLI实际登录状态为“Logged in using ChatGPT”；请求及返回模型别名逐项一致。规划器与用户模拟器均为Luna，使用分开的新上下文；结构化决策由既有公开retail sandbox派发。没有把旧Sol轨迹当成Luna输出，也没有跨厂商、新环境或独立人工验证。

正式75任务是方便子集：继承train顺序前29项（排除试点0–4）＋全部46项原test，不是随机新客户。涉及34个既有客户，train/test分别10/24且无交集。两个prompt各75次、一次重复；攻击器每prompt分别29条train、46条test。test取消/退货阳性为6/11任务、5/7客户。原115任务/53客户早已用于此前开发，不能把重复prompt当成新客户。

| 正式结果 | baseline | rules |
|---|---:|---:|
| native reward | 32/75 | 33/75 |
| test native reward | 21/46 | 18/46 |
| episode p50/p95（秒） | 92.516/158.975 | 92.516/175.503 |
| 模型决策数 | 1530 | 1542 |
| 已知名称派发尝试 | 498 | 505 |
| 全部派发/未知名称 | 506/8 | 509/4 |
| 错误observation/协议拒绝episode | 36/3 | 37/4 |

基础设施错误、timeout、自动重试均为0；全部任务失败和7个协议拒绝均保留。采集总墙钟7736.33秒（含等待试点）。原冻结formal_summary/formal_validation的遗留real_tool_calls字段实际表示全部1015次派发；corrected收据和compact字段才表示1003次已知名称派发。二者都不是成功执行数，已知名称派发也含env.step错误。不得把这次实验写成“零错误”。

追加D2分析的writes-only suite BA为0.666–0.892，reads-only为0.500–0.573；四个reads-only上置信界都超过0.60。reads-only只保留get_/find_/list_前缀，不等于Sol E12的完整no_writes补集。各view保留/排除名称及数量单列。固定GB的min_samples_leaf=20，在每arm仅29训练行时无法分裂；92组GB预测全部常数，低功效已披露。客户bootstrap每draw重选suite最大值：取消1994/2000有效draw，退货2000/2000。区间是固定拟合预测条件下的描述性结果。

网络补充只增加本地TLS1.2回放，不增加LLM请求。防御仅以58条训练轨迹校准；每攻击器仍为每arm29训练/46测试。算法/配置在44/150且test输出前冻结；校准参数是在150全部采集后仅用train拟合，不能声称参数在测试采集前冻结。联合shape_const网络BA分别为：取消baseline0.604、rules0.592；退货baseline0.570、rules0.500。前三项inconclusive，仅rules退货满足已评估suite判据。派发记录比3.9108/3.9502、wire比15.5685/15.5809；这些比率含unknown、error和cover。不宣称联合方案统一优于padding，也不把shadow-cover回放说成live重新规划或provider链路实测。

全部自动一致性/重算检查已PASS：150个reward、3072个决策的事件/答案/角色前缀/派发顺序/长度/user交互/usage对齐，公共ZIP对应重算，12个独立D2 suite cell及36组逐模型预测精确匹配，32个完整网络/dispatch suite cell匹配。它们是自动复算，不是独立人工审查。完整数值与哈希见实验目录compact_manifest.json、COMPACT_TABLES.md和compact_validation.json。

公共归档raw-evidence-public.zip为45,059,872 bytes，SHA256为2fd62289279968042c5c7088aa06624a8c472e293ebcbdd43e9be44ec082de7c。首轮精确HOME匹配脱敏fail-closed后，保留冻结脚本并追加v2与修订记录；仅发布副本替换Windows HOME前缀/别名并保留原始/发布SHA。原始科学输出未改。ZIP本身不自足，仍需固定checkout的公开vendor/tasks/tool/helper源码及依赖；24项代码/数据闭包与R4/既有manifest权威链匹配。

connectivity、pilot、formal三原始私有目录已移出发布包P，保存在工作区revision-preview/r7-agent-originals-20261024；19,819个原件逐项SHA与原始清单一致。原始进程日志也保存在其process-logs内，发布副本只脱敏HOME路径。移动后公开验证入口仍是verify_public.py --network、verify_public_decisions.py、verify_public_d2.py（均无LLM请求，须固定checkout；建议在复现副本中运行以保留发布收据快照）。native本地raw入口不再以P/formal目录直接运行。

compact所列30项artifact与原formal/追加分析冻结源均未变；最终compact SHA256为7688a4e3bcb0d75272fafe59bcd6517e260dfbf9cc9c412fd801fd11378176c3。未修改主稿、旧实验数据、旧协议或旧manifest。
