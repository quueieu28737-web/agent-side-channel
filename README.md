# Agent side-channel SoK — R10

当前 R10 修订：[最终复审修订清单](docs/R10-最终复审修订.md)，区分实测与离线比较、紧凑附录并修正参考文献。历史 R9 校验记录保留。

当前论文突出 **source-bound result records**、三类证据转移错误和四个实验演示。

- [主稿](main.pdf)：17页，包含完整58族地图、R1–R9规则、20族审计矩阵、39记录与实验索引。
- [补充材料](supplement.pdf)：52页，保留完整方法与结果。
- [逐项修改清单](docs/R9-主文自洽与贡献呈现修改清单.md)。
- [可复现发布包](final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/README.md)。

本轮未新增模型实验或更改旧结果。原Sol 690运行、Luna 150运行及后续分析保持原始来源与样本范围。当前版本以正文四模块组织阅读，以附录历史E键定位复现代码。

## 核验

进入发布包目录，使用具有pypdf/pdfplumber的Python环境：

    python provenance/r10-review/verify_publication.py
    python verify_package.py

数值、来源、链接、版式及历史字节核验收据在 provenance/r9-review/。LaTeX构建入口为 manuscript/main.tex 与 manuscript/supplement.tex，使用IEEEtran v1.8b的conference,compsoc选项。

匿名论文源包位于发布包 provenance/r9-review/anonymous-paper-source.zip；正式投稿的完整实验匿名托管和注册披露由作者按投稿流程完成。
