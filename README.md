# agent-side-channel

论文审稿修订版（2026-10-21）：主稿、补充材料、本地复算实验及修订脚本。

当前定位：结果记录审计，加上实验前提交的迁移判断及其受控检验（E5 流式发射器、E6 随机化 cover、E7 加密 agent–tool 链路）。

## 第二轮修订（`test` 分支）

- 审稿意见、修改清单与实施步骤：[`docs/R2-SP2027-审稿与修改清单.md`](docs/R2-SP2027-审稿与修改清单.md)
- 新实验：`final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/experiments/sp2027-r2/`（README 内含复跑命令）
- 预注册：`experiments/sp2027-r2/PREREGISTRATION.json` 在 commit `16f6254` 提交，早于全部实验代码；7 条判断中 5 条证实、2 条部分证实、0 条被推翻。
- `main.pdf` / `supplement.pdf` 已重新编译（正文 13 页，第 8 节为新的 “Controlled Transfer Tests”）。
- 清单 B 类工具：`experiments/sp2027-r2/agent/`（自主 Agent 实验 E8，未含 LLM 结果）、`coding/`（盲法人工编码）、`release/`（匿名工件）、`search/`（第二检索框架）。
- 两个 `.zip` 仍是第一轮快照，未重新打包；以目录内容为准。

## 目录

| 路径 | 说明 |
| --- | --- |
| `main.pdf` / `supplement.pdf` | 修订后的主稿与补充材料 |
| `修订说明.txt` | 对两份审稿意见的逐条修订说明 |
| `final-paper-and-experiments-20261021-m1m8-revised/` | 完整修订包（稿件源码、实验、证据、来源记录），详见其中的 `README.md` |
| `final-paper-and-experiments-20261021-m1m8-revised.zip` | 上述修订包的压缩版 |
| `paper-review-revised-20261021.zip` | 审稿修订材料压缩包 |
| `*.py` | 生成本次修订的脚本（见下） |

## 修订脚本

脚本均以仓库根目录为基准，操作修订包内的 `manuscript/` 与 `experiments/reviewer-audit/`：

- `prepare_revision.py`：备份原稿并准备审稿实验目录
- `revise_manuscript.py`：修改主稿正文
- `build_revision_tables.py`：根据 TLS 实验结果生成表格
- `finish_retail_revision.py`：生成零售工具实验的表格与正文
- `finalize_text.py`：统一修正记录数、编码说明等文字
- `package_revision.py`：复制 PDF、保存编译日志并重新打包

## 校验与复算

进入修订包目录 `final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001/`：

```text
# 只读校验（仅需 Python 标准库）
python -B verify_package.py
python -B verify_revision.py

python -B experiments/sp2027-r2/verify_r2.py

# 重算实验（Python 3.10+，需 numpy、cryptography、pydantic；第二轮另需 scikit-learn、tiktoken）
python -B experiments/reviewer-audit/recompute.py tls
python -B experiments/reviewer-audit/recompute.py retail
python -B experiments/reviewer-audit/recompute.py scenarios
python -B experiments/sp2027-r2/e5_streaming.py
python -B experiments/sp2027-r2/e6_e7_retail_cover.py
python -B experiments/sp2027-r2/e67_eval.py
python -B experiments/sp2027-r2/resolve_predictions.py
```

重跑会更新输出文件，之后需要更新 SHA256 清单。

## 编译论文

LaTeX 使用 IEEEtran 1.8b（conference, compsoc）。在 `manuscript/` 中依次运行 `pdflatex`、`bibtex`，再运行两次 `pdflatex`。
