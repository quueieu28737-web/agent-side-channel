# R13 修订：Exp 4 广域网延迟抖动对照实验（WAN netem 扩展）

## 1. 修订背景与审稿意见
评审意见指出：Exp 4（Live Tool Timing）原测试基于本地回环链路（Loopback），缺乏网络传输抖动，时序攻击结论可能偏乐观。建议使用 `tc netem` 机制在相同流程中注入 20/50 ms 延迟和 5–10 ms 抖动，重新测试 serial shadow、per-call constant、2 ms tunnel，检验 flush 检测和 intent BA 是否保持。

## 2. 实验设计与仿真拓扑 (`sp2027-r13-wan-timing`)
* **网络仿真**：在 TLS 中继层实现 `NetemRelay`，高精度双向模拟 Linux `tc netem` 的正态时延与抖动，保证 TCP/TLS 的严格 FIFO 时序与单调性：
  * **WAN Mild**：单向 20 ms 延迟，5 ms 正态抖动（标称 40 ms RTT）；
  * **WAN Realistic**：单向 50 ms 延迟，10 ms 正态抖动（标称 100 ms RTT）。
* **真工具闭环反馈**：真实等待每个工具调用的解密响应后放行后续动作，保持多轮任务依赖与后端数据库状态一致性（`resp_eq=True`, `db_eq=True`）。
* **评测规模**：覆盖全部 276 个客户留出测试轨迹（138 baseline，138 rules），每个 WAN 条件采集 1,104 个 TLS 会话，两组 WAN 条件累计新增 **2,208 个测得 TLS 会话**。

## 3. 核心实验结论
1. **Flush 阶段检测：强稳健保持（Robustness Holds）**
   * 回环链路冻结检测器 $D_{\text{loop}}$ 直接零样本迁移到 WAN：
     * WAN 20ms / 5ms 抖动：Point BA = **89.4%**（95% CI: [87.2%, 91.7%]），AUROC = **0.962**；
     * WAN 50ms / 10ms 抖动：Point BA = **89.4%**（95% CI: [87.3%, 91.7%]），AUROC = **0.963**；
   * 本地 5 折交叉验证自适应重训（Adapted $D_{\text{WAN}}$）：Point BA 保持在 **89.0%–89.2%**，AUROC > 0.957；
   * 说明从依赖反馈的真实调用切换到无栅极填充排放时，宏观记录密度与时长的跃迁能够穿越 5–10 ms 抖动。
2. **意图分类（Intent BA）：抖动成为天然噪声**
   * 回环链路上微秒级执行差异使攻击套件对 `shadow_serial` 的 Cancel BA 达到 61.4%；
   * 在广域网抖动下，细粒度时钟差异被彻底掩盖，Cancel BA 降回 **50.0%（纯随机水平）**（WAN 20ms）与 **54.0%**（WAN 50ms）。
3. **隧道防御（Tunnel）：诚实的操作边界（The Honest Boundary）**
   * 训练集拟合的 133 槽位（266 ms）定长恒率隧道（2 ms 槽长）在回环链路上 100% 完成；
   * 在广域网链路下，网络 RTT 使多步轨迹耗尽 133 槽位仍无法收到响应，**WAN 20ms 下 69.2% 会话失败，WAN 50ms 下 98.2% 会话失败（Horizon Exhaustion）**；
   * 对比之下，串行影子调度与常数分块保持 100% 任务完成与 100% 状态一致性，延迟随网络 RTT 平滑线性扩展。

## 4. 论文与交付文件更新
* 主论文 `manuscript/sections/42-live-timing-main.tex`：新增 `\paragraph{Robustness under WAN transit delay and jitter}` 段落；
* 补充材料 `manuscript/sections/41-live-timing.tex`：新增 `\subsection{Evaluation under WAN transit delay and jitter (Exp 4 Extension)}` 完整分析；
* LaTeX 数据表格：`manuscript/tables/r13-wan-flush.tex` 与 `manuscript/tables/r13-wan-controls.tex`；
* 重新编译主论文与补充材料 PDF，同步至根目录 `main.pdf`、`supplement.pdf` 及 `pdf/` 目录；
* 完整实验代码、捕获数据与重跑脚本封装于 `experiments/sp2027-r13-wan-timing/`。
