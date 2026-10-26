"""Prepare revision-local build/release/check tools without editing historical tools."""
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parents[1];OLD=P/'provenance/r24-three-sok-contributions'
for name in ['build_pdfs.py','release_ops.py','render_review.py','update_metadata.py','verify_revision.py']:
 s=(OLD/name).read_text(encoding='utf8').replace('r24-three-sok-contributions','r25-audit-sensitivity').replace('r24-delivery','r25-delivery').replace('R24','R25')
 if name=='verify_revision.py':
  s=s.replace("BASE='d6533c9374c1a118b4b1f139e74de16d5e410a83'","BASE='5db4235ed1e8e9d152c7cb9b98587ebf5ca5d916'")
  s=s.replace("'sections/03-methodology.tex',","").replace("'sections/27-intervention-contracts.tex',","").replace("'tables/r19-joint-bindings.tex',","")
  s=s.replace("n!='manuscript/tables/r9-rq-findings.tex'","n not in {'manuscript/tables/r9-rq-findings.tex','manuscript/tables/r19-joint-bindings.tex'}")
  s=s.replace("['82 study families','39 result records','741','133','17','CachePrune','six-axis']","['82 study families','39 result records','CachePrune','six-axis']")
  s=s.replace("'R25-three-sok-contributions'","'R25-audit-sensitivity'")
  s=s.replace("report={'revision':","subprocess.run([sys.executable,str(O/'verify_analysis.py')],check=True)\nassert 'sections/65-audit-sensitivity.tex' in supp_cl\nreport={'revision':")
  s=s.replace("'coding_changed':False,","'coding_changed':False,'new_deterministic_audit_sensitivity':True,")
 if name=='render_review.py':
  # Changed first six main pages and the appended supplementary section.
  s=s.replace("('main',[1,2,6,7,8,9,10,13,14,15,16]),('supplement',[1,57,58,59,60,61,62,63,64,65,66])",
              "('main',[1,2,3,6,7,8,9,10,14,15,16]),('supplement',[65,66,67,68,69,70])")
 if name=='update_metadata.py':
  s=s.replace("R25-三项SoK贡献与统计解释.md","R25-审计分母与判断敏感性.md")
  s=s.replace("R25: record-level comparison, configuration-level joint binding and deployment decisions; empirical nonsignificance is not evidence of framework validity","R25: explicit joint-query denominators, archived-label sensitivity and complete family-deletion accounting")
  s=s.replace("'scope':'Three literature-derived SoK contributions; one appendix worked case with all original statistical results retained in the supplement.'",
              "'scope':'Three literature-derived SoK contributions; explicit 33-record query masks and archived-label/family sensitivity; historical experiments unchanged.'")
  s=s.replace("'verification.json','visual-check.json','anonymous-paper-check.json'","'verification.json','visual-check.json','anonymous-paper-check.json','analysis.json','data-verification.json'")
  s=s.replace("## 案例与统计范围","## 审计分母与敏感性\\n\\nTable 10 从共同的 33 条缓解记录展开排除、适用和绑定计数。S33 保留全部 165 个查询成员判断、六类相关记录对、26 次家族剔除及状态规则敏感性。全部原始标签不变；这些检查不等同于独立编码一致性。\\n\\n- 推断—效用—成本的一个 CachePrune 配置在接受 P/? 的压力检查中保持不变，但剔除该家族后无正例。\\n- 匹配适应—推断的计数由严格 B 的 2/17 变为接受 P/? 时的 16/17，定位了需进一步核验的拟合／测试绑定。\\n- 同家族 8 个不兼容对分布于 6/11 个多记录家族；不把记录对当作独立样本。\\n\\n## 案例与统计范围")
 (O/name).write_text(s,encoding='utf8',newline='\n')
print('R25_TOOLS_PREPARED')
