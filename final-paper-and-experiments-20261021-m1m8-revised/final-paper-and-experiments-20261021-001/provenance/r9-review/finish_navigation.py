from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
# Preserve a visual-review receipt for the 70 inspected pages before final navigation correction.
render=R/'revision-preview/r9-final-render';manifest=json.loads((render/'render_manifest.json').read_text())
receipt={}
for name,v in manifest.items():
 receipt[name]={'pdf_sha256':v['pdf_sha256'],'pages':v['pages'],'page_raster_sha256':[hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in v['page_images']]}
(O/'visual_review_before_navigation.json').write_text(json.dumps({'status':'70_PAGES_VISUALLY_INSPECTED','documents':receipt,'inspection':'All 12 contact sheets inspected; no clipped tables or overlapping text. Final navigation correction will be rendered and differing pages reinspected.'},indent=2)+'\n',encoding='utf8')
p=M/'sections/40-evidence-concordance.tex';s=p.read_text()
s=s.replace('We retain artifact identifiers for reproducibility; their numeric values are not a count of newly independent studies. No separately reported E4 is bound to the retained artifact. This unused identifier contributes no data or claim.','The archived identifiers resolve protocols, predictions and verifiers. The main paper organizes these records into four demonstrations; the table maps each key to its current location.')
s=s.replace('E4 & Unused identifier & No reported experiment\\\\\n','')
s=s.replace('E7 & Agent--tool TLS composition & Main 8.3;', 'E7 & Agent--tool TLS composition & Main 8.2;')
s=s.replace('E9 & Real agents; pretest-frozen calibration & Main 8.4;', 'E9 & Real agents; pretest-frozen calibration & Main 8.3;')
s=s.replace('Main 8.5; original suite S15, expanded suite S21','Main 8.3; original suite S15, expanded suite S21')
s=s.replace('Main 8.6; S19','Main 8.4; S19').replace('Main 8.7; S20','Main 8.4; S20').replace('Main 8.8; S22','Main Appendix C; S22')
s=s.replace('E10--E12 & Post hoc cross-fitting, selection, localization','E10/E12 & Cross-fitting and oracle localization')
s=s.replace('E13 & Live tool timing',r'E11 & Retrospective operating-point selection & Main Appendix C; S15\\'+'\n'+'E13 & Live tool timing')
s=s.replace('\\bottomrule\\end{tabularx}\\end{table}\n\n\\subsection{Absolute',r'E16 & Same-operation attribute diagnostic & Main Appendix C; S23.8\\'+'\n'+'\\bottomrule\\end{tabularx}\\end{table}\n\n\\subsection{Absolute')
p.write_text(s,encoding='utf8',newline='\n')
p=M/'sections/50-r9-experiment-index.tex';s=p.read_text().replace('Attribute supplement','S23.8');p.write_text(s,encoding='utf8',newline='\n')
print('FINAL_NAVIGATION_SYNCHRONIZED')
