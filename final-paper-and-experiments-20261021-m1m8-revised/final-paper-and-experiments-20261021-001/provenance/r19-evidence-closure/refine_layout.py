"""Keep actionable main-paper tables ahead of the bibliography."""
from pathlib import Path
O=Path(__file__).resolve().parent;M=O.parents[1]/'manuscript'
p=M/'sections/10-open-challenges.tex';s=p.read_text();s=s.replace('\\input{tables/r19-deployment-decisions}\n','').replace('Table~\\ref{tab:r7-deployment} states the corresponding visibility and trusted endpoint.','A host monitor may see process/IPC metadata; a VPC gateway sees ingress traffic, and a remote or cross-organization path can expose destinations and routing.').replace('\\input{tables/r7-deployment}\n','');p.write_text(s,newline='\n')
p=M/'sections/28-fingerprint-dependencies.tex';s=p.read_text();s+='\n\\input{tables/r19-deployment-decisions}\n';p.write_text(s,newline='\n')
p=M/'sections/39-shadow-deployment.tex';s=p.read_text();s=s.replace('\\subsection{What padding', '\\input{tables/r7-deployment}\n\n\\subsection{What padding',1);p.write_text(s,newline='\n')
print('DECISION_TABLE_MOVED_AHEAD_OF_EXPERIMENTS')
