# Agent side-channel SoK — R13

当前 R13 修订：根据审稿意见在 Exp 4（Live Tool Timing）中新增 WAN 20ms/5ms 与 50ms/10ms 延迟抖动实验（`experiments/sp2027-r13-wan-timing/`），重跑 276 个测试轨迹共 2,208 个新测 TLS 会话，检验 Flush 阶段检测稳健性、影子时序掩蔽及固定恒率隧道在网络 RTT 下的时隙耗尽（Horizon Exhaustion）边界。历史 R10 及以前校验记录保留。

当前论文突出 **source-bound result records**、三类证据转移错误和四个实验演示。

- [主稿](pdf/main.pdf)：17页，包含完整58族地图、R1–R9规则、20族审计矩阵、39记录与实验索引，以及 Exp 4 WAN 延迟抖动实验。
- [补充材料](pdf/supplement.pdf)：53页，保留完整方法与结果。
- [逐项修改清单](provenance/r9-review/docs/R9-主文自洽与贡献呈现修改清单.md)。
- [WAN 实验套件说明](experiments/sp2027-r13-wan-timing/README.md)。
- 当前源码与来源绑定：artifact-index.json、provenance/snapshot.json、SHA256SUMS.json。

原Sol 690运行、Luna 150运行及后续分析保持原始来源与样本范围。当前版本以正文四模块组织阅读，以附录历史E键定位复现代码。

## 核验

进入发布包目录，使用具有pypdf/pdfplumber的Python环境：

    python provenance/r10-review/verify_publication.py
    python verify_package.py

数值、来源、链接、版式及历史字节核验收据在 provenance/r9-review/。LaTeX构建入口为 manuscript/main.tex 与 manuscript/supplement.tex，使用IEEEtran v1.8b的conference,compsoc选项。

匿名论文源包位于发布包 provenance/r9-review/anonymous-paper-source.zip；正式投稿的完整实验匿名托管和注册披露由作者按投稿流程完成。
