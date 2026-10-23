# Shadow Cover：现实部署与观察者边界修订

日期：2026-10-24。基于 `35d43a8d4866737571faf4cc3f91581bdd4dc144`。

## 本轮主线

Shadow Cover 的价值在于：在需要塑造调用级可见轨迹时，把掩护调用与真实状态修改分离。主稿 §8.2、§8.3、§8.4 和 §9.1 已加入对应论证；补充 S17 给出三条实现路径、架构对比和观察者边界表。

正文仍为 13 页，References 从第 13 页开始，Appendix 在第 17 页，主稿共 17 页。补充材料共 29 页，S17 位于第 24–25 页。

## 证据与解释

- **E7/E9 反驳逐调用填充充分性。** E7 无 cover 的分桶方案退货 BA 为 73.9%；E9 基线轨迹仅 padding 为 66.1%/55.5%。长度填充保留调用次数、方向和序列结构。
- **这些实验没有比较完整恒定速率隧道。** RFC 9347 使用固定长度、恒定发送速率、聚合/分片及填充包隐藏内部流量形态。若同时处理会话起止、持续时间和其他暴露链路，纯链路观察者的防护可以在传输层实现，无需执行工具 dummy call。因此删除“任何网络观察者都必须依靠虚拟工具调用”的过强推论。
- **调用级观察的边界决定 Shadow Cover 的作用。** 隧道解封装后的中继可能看到工具名、RPC 或转发事件；掩护必须到达该观察点，且 marker、模式、可识别参数与路由不能暴露真实分支。E6/E9 支撑指定的名字/长度/网络投影，不能升级成对任意中继视图的保证。

## 三条工程路径

| 路径 | 作用 | 必要边界 |
|---|---|---|
| 合法只读查询与已核实 no-op | 可复用真实后端，本地丢弃返回值 | 权限、配额和副作用需明确；幂等不等于无状态变化；读调用不能覆盖观察者能识别的写类型 |
| API 原生隔离 | Kubernetes server dry-run；Stripe 独立 sandbox；事务回滚 | 三者语义不同。sandbox 会维护测试状态；rollback 不覆盖所有效果。提供方知道模式，模式字段不得泄漏给目标观察者 |
| 可信 MCP/Tool 网关 | 固定长度认证加密标记，真实请求透传，shadow 请求进入隔离模拟器 | 网关本身可信；错误不能回落为真实写入；延迟和响应大小需通过共同调度/分帧处理，不能假设 mock 自然等于生产流量 |

网关本地 cover 可以保护客户端到网关的观测面。若网关之后只转发真实调用，下游链路必须单独保护；能查看 marker、分支路由或真实提交记录的主体不在同一保护范围内。对半诚实中继的扩展是有条件的部署设计。

## 官方来源

- [RFC 9347：IP Traffic Flow Security](https://www.rfc-editor.org/rfc/rfc9347)
- [Kubernetes API dry-run](https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run)
- [Stripe Sandboxes](https://docs.stripe.com/sandboxes)
- [PostgreSQL 18 ROLLBACK](https://www.postgresql.org/docs/18/sql-rollback.html)
- [PostgreSQL 18 Sequence Manipulation Functions](https://www.postgresql.org/docs/18/functions-sequence.html)

以上五条为部署参考，不改变原 82 个研究族的文献口径。逐条支持范围记录在包内 `provenance/shadow-deployment/sources.json`。

## 校验与交付范围

未新增 LLM 请求、生产 API 操作或实验测量。完整 690 次模型轨迹、原冻结参数、攻击预测、R5 交叉拟合结果及此前归档保持原样；未把架构可行性写成部署效果已获验证。

当前校验器为 `provenance/shadow-deployment/verify_manuscript.py`，核对全部未授权变更的历史文件、原表格、数值、引用键、PDF 页数、编译警告与成品副本。包级校验仍使用 `verify_package.py`、`verify_revision.py` 和完整队列 `verify_release.py`。旧 `provenance/sok-restructure/` 中的文稿收据和校验器对应上一版排版，作为历史记录保留。

新增增量包 `paper-shadow-deployment-20261024.zip` 以本页所列基线提交为起点，配套 JSON 记录每个文件的 SHA-256；不复制实验原始数据。
