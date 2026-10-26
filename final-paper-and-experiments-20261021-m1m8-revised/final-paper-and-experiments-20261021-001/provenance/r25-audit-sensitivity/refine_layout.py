"""Keep the decision table in the body and the appendix case on one page."""
from pathlib import Path
import subprocess,json
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]
f=M/'sections/11-discussion.tex';s=f.read_text()
token=r'\input{tables/r19-deployment-decisions}'
assert s.count(token)==1
s=s.replace(token+'\n','');first,rest=s.split('\n',1)
f.write_text(first+'\n'+token+'\n'+rest,encoding='utf8',newline='\n')
f=M/'sections/62-appendix-case-study.tex';s=f.read_text();assert s.startswith(r'\newpage')
f.write_text(s.replace(r'\newpage',r'\clearpage',1),encoding='utf8',newline='\n')
# Preserve historical mixed line endings outside the inserted S33 input.
rel=(M/'supplement.tex').relative_to(R).as_posix()
s=subprocess.check_output(['git','show','5db4235ed1e8e9d152c7cb9b98587ebf5ca5d916:'+rel],cwd=R)
token=br'\input{sections/64-case-study-register}'
assert s.count(token)==1
(M/'supplement.tex').write_bytes(s.replace(token,token+b'\n\\clearpage\\onecolumn\n\\input{sections/65-audit-sensitivity}',1))
names=dict(zip(
['addagada2026kvgov','alhazbi2025rhythm','carlini2024remote','chen2026sparleak','chu2025safekv','dangol2026workflow','debenedetti2024privacy','earlybird2025','gao2025iknow','geng2026sigleak','gu2026behindbars','hadad2026shape','hornetz2026tdxray','jeong2026wra','lee2026otro','netecho2025','pouryousef2026traffic','shahriar2026agenttell','spliceleak2026','timewilltell2024','uitraces2026','wang2026fpagent','wei2024speculation','whisperleak2025','wu2026cacheprune','zhu2026turing'],
['KVGov','LLMs Have Rhythm','Remote timing','SparLeak','SafeKV','Dangol workflow','ML privacy channels','Early Bird','I Know What You Said','SIGLEAK','Behind Bars','Shape and Substance','TDXRay','WRA','OTRO','NetEcho','Cloud traffic benchmark','AgentTell','SpliceLeak','Time Will Tell','UI Traces','FP-Agent','Speculative decoding','Whisper Leak','CachePrune','AHB']))
f=M/'sections/65-audit-sensitivity.tex';s=f.read_text()
for key,name in names.items():
 token=r'\cite{'+key+'} &';assert s.count(token)==1,key
 s=s.replace(token,name+'~'+token)
f.write_text(s,encoding='utf8',newline='\n')
print('R25_LAYOUT_REFINED')
