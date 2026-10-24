# Agent side-channel SoK — R13

当前 R13 修订：[Exp 4 广域网延迟抖动对照实验说明](docs/R13-Exp4-WAN网络抖动与时序鲁棒性实验.md)。根据审稿意见针对回环链路时序偏乐观的问题，在 276 个测试轨迹上补充了 WAN 20ms/5ms 抖动与 WAN 50ms/10ms 抖动测试，验证 Flush 检测稳健性、影子时序掩蔽及固定隧道时隙耗尽边界。历史 R10 及以前校验记录保留。

当前论文突出 **source-bound result records**、三类证据转移错误和四个实验演示。

- [主稿](main.pdf)：17页，包含完整58族地图、R1–R9规则、20族审计矩阵、39记录与实验索引，以及 Exp 4 WAN 延迟抖动实验。
- [补充材料](supplement.pdf)：53页，保留完整方法与 WAN 详细攻防对比。
- [逐项修改清单](docs/R9-主文自洽与贡献呈现修改清单.md)。
- [可复现发布包](final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/README.md)。
- [WAN 实验套件说明](final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/experiments/sp2027-r13-wan-timing/README.md)。

原Sol 690运行、Luna 150运行及后续分析保持原始来源与样本范围。新增广域网对照实验包含 2,208 个新测 TLS 会话（已归档在 `experiments/sp2027-r13-wan-timing/captures/`）。当前版本以正文四模块组织阅读，以附录历史E键定位复现代码。

## 核验

进入发布包目录，使用具有pypdf/pdfplumber的Python环境：

    python provenance/r10-review/verify_publication.py
    python verify_package.py

数值、来源、链接、版式及历史字节核验收据在 provenance/r9-review/。LaTeX构建入口为 manuscript/main.tex 与 manuscript/supplement.tex，使用IEEEtran v1.8b的conference,compsoc选项。

匿名论文源包位于发布包 provenance/r9-review/anonymous-paper-source.zip；正式投稿的完整实验匿名托管和注册披露由作者按投稿流程完成。
