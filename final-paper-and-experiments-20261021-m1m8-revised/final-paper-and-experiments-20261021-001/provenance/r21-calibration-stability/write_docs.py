from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];D=P/'experiments/sp2027-r21-calibration-stability'
s=json.loads((D/'summary.json').read_text());v=json.loads((O/'verification.json').read_text())
names={'sp2027-r11-minimax':'MiniMax','sp2027-r12-glm':'GLM'}
def ci(v):return '['+', '.join(f'{100*x:.1f}' for x in v)+']'
text='''# R21：校准迁移的统计复核与本地重校准对照

## 对 M2 的判断

核心质疑成立：旧数据没有把校准来源差异与训练客户抽样敏感性分开；单个名义 bootstrap 区间不能支撑“退货方向已确认”的表述。非单调本身不否定迁移边界的概念，但也不是模型来源造成退化的证据。旧表实际是 **8 个目标级差值**（2 端点 × 2 对照 × 2 标签），不是 6 个。

## 完成的实验

- 100 次预先固定种子的训练客户 bootstrap，每次抽取 29 个训练客户并保留其全部任务；两校准来源使用同一客户抽样。
- 每次重新构建两来源的模板、供体和帧上限，作用于两个目标端点的 115 条已存轨迹；合计 **46,000 次新的本地 TLS 捕获**。
- 完整七攻击器套件包含受保护数据重训、解码、目标调用计数和总交换次数。
- 三类对照：只重采样校准；同时独立重采样攻击器训练客户；只重采样攻击器而保持原本地校准。
- 原 46 个测试任务 / 24 个测试客户固定，用于训练敏感性分布；另报告 100 × 20 的训练/测试嵌套抽样区间。单类测试抽样被记录为无效，不补抽。
- 原表 8 个差值各做 99,999 次客户级整套预测交换，重新选择套件最大 BA，并对全部 8 个 p 值做 Holm 校正。

这些都是事后分析。训练敏感性范围不是人口参数置信区间；重复采样没有增加独立客户或模型调用。

## 配对置换结果

|目标端点|干预|标签|原差值（百分点）|原始 p|Holm p|
|---|---|---|---:|---:|---:|
'''
for x in s['conditional_tests']:
    cond='导入联合校准' if x['condition']=='transferred_joint' else '仅写填充'
    text+=f"|{names[x['target']]}|{cond}|{x['label']}|{100*x['delta']:+.1f}|{x['permutation_p']:.5f}|{x['holm_p']:.3f}|\n"
text+='\n全部比较未达到 0.05，包括原来的 GLM return −17.3 点比较（原始 p=0.17389）。这不证明条件等效；论文撤回“resolved return reduction”，保留原始点估计与成本。\n\n## 本地训练敏感性\n\n固定原测试客户；下表是 BA 百分比的 2.5%–97.5% 经验范围。\n\n|端点|标签|只重采样校准|校准＋攻击器重采样|只重采样攻击器|\n|---|---|---|---|---|\n'
for n in names:
    for lab in ['cancel','return']:
        values=[next(x for x in s['stability'] if x['source']==n and x['target']==n and x['label']==lab and x['regime']==reg) for reg in ['calibration_only','calibration_and_attacker','attacker_only']]
        text+=f"|{names[n]}|{lab}|"+'|'.join(ci(x['percentiles95']) for x in values)+'|\n'
text+='\n## 导入减本地的重采样差值\n\n中位数及固定测试集 95% 敏感性范围，单位为百分点；不是显著性声明。\n\n|端点|标签|校准重采样|同时重采样攻击器|联合训练/测试探索性区间|\n|---|---|---|---|---|\n'
for n in names:
    for lab in ['cancel','return']:
        c=next(x for x in s['contrasts'] if x['target']==n and x['label']==lab and x['regime']=='calibration_only')
        j=next(x for x in s['contrasts'] if x['target']==n and x['label']==lab and x['regime']=='calibration_and_attacker')
        text+=f"|{names[n]}|{lab}|{100*c['fixed_test']['median']:+.1f} {ci(c['fixed_test']['percentiles95'])}|{100*j['fixed_test']['median']:+.1f} {ci(j['fixed_test']['percentiles95'])}|{ci(j['joint_train_test']['percentiles95'])}|\n"
text+='''
## 稿件修改

1. 摘要、引言、Exp 3 和结论撤回旧“方向性已确认”措辞；以来源、样本和攻击器拟合的匹配要求组织主线。
2. 主文校准迁移表保留原始 BA、字节和调用成本，并直接加入本地重校准和来源差值的敏感性范围。旧名义区间保留在补充材料和原始档案中。
3. 部署决策表增加“导入校准必须与重复本地校准比较”的步骤。
4. 新增补充章节给出全部 8 个置换检验、3 类敏感性对照、联合抽样区间、成本分布与来源校验。
5. 原作者复核与编码表述不变；没有加入独立双人编码或 κ 段落。

## 校验

'''
text+=f"- 原两个校准器与 84 组原攻击器预测逐项一致；全部 14,000 组新增预测用 scikit-learn 重新核验 BA。\n- 每次抽样均检查训练/测试客户分离、实际任务列表、供体训练来源、TLS 字节及调用总量。\n- {v['unchanged_scientific_and_prior_provenance_files']:,} 个历史科研数据和先前发布来源文件哈希保持不变。\n- 主稿 {v['pdfs']['main']['pages']} 页，References 从第 {v['pdfs']['main']['references_start']} 页开始；补充材料 {v['pdfs']['supplement']['pages']} 页。编译无未定义引用和溢出。\n"
text+='\n实验：`experiments/sp2027-r21-calibration-stability/`；发布核验：`provenance/r21-calibration-stability/verification.json`。新客户、固定权重模型及独立环境的确认性实验仍是更强外推结论所需的证据。\n'
(R/'docs/R21-校准迁移统计复核与重采样实验.md').write_text(text,encoding='utf8',newline='\n')
print('R21_REVIEW_RESPONSE_WRITTEN')
