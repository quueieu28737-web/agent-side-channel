from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
f=O/'checklist-coverage.json';j=json.loads(f.read_text(encoding='utf8'))
idx={x['id']:x for x in j['items']}
for k in ['4a','4b']:
 idx[k]['status']='COMPLETED';idx[k]['action']=idx[k]['action'].split(' Main text now reports')[0]+' Main text now reports customer-equal and deletion values; S23 contains the full table and checks.'
 idx[k]['remaining']='Fixed-prediction sensitivity omits attacker-refitting uncertainty and does not create new customers.'
idx['5a']['action']=idx['5a']['action'].split(' E16 is now integrated')[0]+' E16 is now integrated into the main text and S23 with all negative controls and exact score validation.'
idx['5a']['remaining']='Only 15 customers/20 instances; no stable non-action-attribute result or new-population confirmation.'
idx['5a']['evidence']=list(dict.fromkeys(idx['5a']['evidence']+['manuscript/sections/48-r8-attributes.tex','experiments/sp2027-r8-sensitive-attributes/verification.json']))
idx['11a']['status']='COMPLETED';idx['11a']['action']='Created and independently scanned 101-member anonymous paper/source ZIP, including current main and supplement PDFs, source closure and IEEE class/style; excluded Git history and machine logs.'
idx['11a']['evidence']=['provenance/r8-review/anonymous-paper-source.zip','provenance/r8-review/anonymous-paper-check.json']
idx['11a']['remaining']='This is not the complete experimental artifact or anonymous hosting; author final review is still needed.'
idx['12b']['status']='COMPLETED';idx['12b']['action']='Drafted an explicit AI-use submission statement and its factual author-review prerequisites in the R8 submission document; no HotCRP statement submitted.'
idx['12b']['remaining']='Final author inspection, registration and attestation are author actions, not completed by PDF validation.'
idx['13a']['remaining']='Final rendered-page and release checks are separately bound to the delivered PDF hashes.'
mapping={'1a':[9],'1b':[9],'1c':[9],'1d':[10],'1e':[10],'2a':[11],'2b':['writing/self-containment'],'2c':[11],'2d':[11],'3a':[1],'3b':[4,7],'4a':[4],'4b':[4],'5a':[1,8],'5b':[1],'6a':[3],'6b':[3],'7a':[5],'7b':[5],'8a':[6],'8b':[6],'9a':[8],'9b':[8],'10a':['writing/preprints'],'10b':['writing/preprints'],'11a':['writing/anonymity'],'11b':['writing/anonymity'],'12a':['writing/AI'],'12b':['writing/AI'],'13a':['writing/numbers','writing/terminology'],'13b':[2],'13c':[7]}
for x in j['items']:x['user_problem']=mapping.get(x['id'],x.get('user_problem',[]))
extra=[
 ('14a',[5],'Observer placement and the trusted gateway boundary need an explicit deployment argument.','Added operator/VPC/relay access assumptions and excluded the marker-aware executor/commit logs; these are visibility assumptions, not prevalence measurements.','COMPLETED',['manuscript/sections/10-open-challenges.tex','manuscript/tables/r7-deployment.tex'],'No measured deployment prevalence or production deployment.'),
 ('14b',[5],'Provider sandboxes, dry-run and rollback were only proposed, not measured.','Labeled the provider-specific options as feasibility examples; only the local gateway was measured.','REQUIRES_NEW_DATA',['manuscript/sections/10-open-challenges.tex'],'Real provider-backend integration and execution measurement remain absent.'),
 ('14c',[5,6],'Database equality and planner-visible equivalence are constructed invariants.','Reclassified state/response results as implementation-conformance checks, separated from independent empirical utility.','COMPLETED',['manuscript/sections/37-transfer-tests.tex','manuscript/sections/10-open-challenges.tex'],'No live defended-planner utility claim.'),
 ('14d',[3,5],'Per-call padding must not be conflated with full traffic-flow confidentiality.','Distinguished per-call frames from complete fixed-horizon transport cover; dummy tunnel cells execute no tools, and passive-link protection does not require application-layer shadow calls.','COMPLETED',['manuscript/sections/37-transfer-tests.tex','manuscript/sections/42-live-timing-main.tex'],'No tuned minimum-cost tunnel or blanket shadow advantage.'),
 ('15a',[2,4,7],'The author-chosen absolute gate is unconfirmed, and paired reduction is not security.','Retained the frozen gate, labeled it an engineering screen and made unsupported security certification explicit. SoK claims use record-specific transfer failures.','PARTIALLY_ADDRESSED',['manuscript/sections/37-transfer-tests.tex','manuscript/main.tex'],'A new, adequately powered customer cohort and defensible deployment-risk target would be needed for a security-efficacy claim.'),
 ('15b',[3],'WF adaptations are not full reproductions of original algorithms and guarantees.','Main text states missing symmetric WT pairing, training-IAT WTF-PAD, simulated-versus-measured clocks and common-suite versus larger-union differences.','PARTIALLY_ADDRESSED',['manuscript/sections/42-live-timing-main.tex','manuscript/tables/r8-controls.tex'],'Full original-protocol WF reproduction and equal live planner utility are not established.'),
 ('15c',[4],'Saved-prediction intervals omit attacker training uncertainty.','Explained this in main/supplement and preserved all fitted-conditional intervals; added only explicitly deterministic influence analyses.','PARTIALLY_ADDRESSED',['manuscript/sections/47-r8-empirical-audit.tex','manuscript/sections/10-open-challenges.tex'],'Nested refitting uncertainty and independent population replication remain unmeasured.'),
 ('15d',['writing/numbers'],'Distinct BA effects and byte multipliers appear contradictory without cohorts.','Added the E9/E10/E13 denominator table, fixed TLS1.2 2.18 versus TLS1.3 2.19 explanation, and retained historical numbers only in their original scope.','COMPLETED',['manuscript/tables/r8-cohorts.tex','provenance/r8-review/numerical-review.json'],'No pooling of incompatible observation/attacker/serialization estimands.')
]
for i,pro,issue,act,status,ev,rem in extra:
 if i not in idx:j['items'].append(dict(id=i,user_problem=pro,issue=issue,action=act,status=status,evidence=ev,remaining=rem))
j['scope']='R8 response to all 11 research/SoK criticisms and writing/submission details; source verification does not imply security efficacy.'
j['unresolved_resources']=[v for v in j['unresolved_resources'] if v['resource']!='Anonymous source ZIP verification']
for name in ['real provider-backend measurements','attacker-refitting uncertainty','full original-protocol WF reproduction']:
 if name not in {v['resource'] for v in j['unresolved_resources']}:j['unresolved_resources'].append({'resource':name,'status':'REQUIRES_NEW_DATA','reason':'Not established by this revision; the corresponding evidence boundary is explicit.'})
f.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
lines=['# R8 逐项修改与未解决问题','','本轮按用户11类问题及写作细项逐一核对。COMPLETED表示所列修订/核查完成，不表示该领域的外部实验证明已经补齐。PARTIALLY_ADDRESSED与REQUIRES_NEW_DATA保留尚缺的实质证据。','','## 本轮完成的工作','','- SoK主线重新集中于39条来源绑定结果记录、58核心族全景、20×9适用性矩阵及三类具体证据迁移错误。','- 新增同操作商品属性诊断及客户权重/删除敏感性分析；没有把负结果包装为阳性贡献。','- 公平比较使用共同7攻击器并保留最强union；正面呈现WT的成本点值优势、flush可辨识性和本文自身未测live LLM utility。','- 主文统一各套实验的分母、后验性质和安全阈值含义；正文13页，当前编译结果与最终视觉校验分别存档。','- 两份PDF、源码匿名包、来源/数值/历史保留检查已准备；完整数据匿名托管与正式投稿仍是后续作者操作。','','## 逐项清单','','“对应”中的数字直接对应用户本轮编号；writing对应写作与可审性意见。完整证据路径见同名machine-readable JSON。','','| ID | 对应 | 状态 | 问题与已做修改 | 仍缺证据/边界 |','|---|---|---|---|---|']
for x in j['items']:
 clean=lambda s:str(s).replace('|','/').replace('\n',' ')
 lines.append('| '+' | '.join([x['id'],clean(x['user_problem']),x['status'],clean(x['issue']+' '+x['action']),clean(x['remaining'])])+' |')
lines+=['','## 重要结论','','690次Sol运行只有53客户。属性诊断的15客户、20实例不提供新的大样本或独立确认。固定三模型原向BA为30.3%，标签打乱对照65.2%；这既不确证属性泄漏，也不证明无泄漏。没有在看到结果后反转分数或替换目标。','','新客户、真实闭环防御下LLM效用、第二环境/不同厂商或固定权重、真实提供商后端及独立人工盲审均未宣称完成。该稿通过的是数据与交付校验，不是绝对安全认证。']
(R/'docs/R8-逐项修改与未解决问题.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
print('CHECKLIST_UPDATED',len(j['items']))
