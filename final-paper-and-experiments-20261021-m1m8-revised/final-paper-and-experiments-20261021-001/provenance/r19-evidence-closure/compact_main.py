"""Remove duplicated exposition while retaining measured results and scope."""
from pathlib import Path
M=Path(__file__).resolve().parents[2]/'manuscript'
p=M/'sections/10-open-challenges.tex';s=p.read_text();a=s.index('Table~');b=s.index('\\subsection{Ethics',a)
s=s[:a]+r'''Table~\ref{tab:r19-decisions} specifies the missing measurement for each changed boundary. A passive observer may be an access-network operator, VPC monitor or inter-organization relay. Remote paths expose destinations even with Encrypted ClientHello \cite{rfc9849}; our measurements use one ingress endpoint. Host instrumentation and downstream commit logs require different protection.

Shadow state can use authorized reads/verified no-ops, provider isolation (Kubernetes dry-run, Stripe sandboxes, transactional rollback), or a trusted gateway routing marked writes to an isolated executor \cite{kubernetesdryrun,stripesandboxes,postgresrollback}. Idempotence alone is insufficient, and sequence changes can survive rollback \cite{postgressequences}. We measure the gateway path; provider integrations remain designs. The gateway can identify cover and is trusted. Ingress shaping competes with transport controls; restricted dispatch protection additionally requires hidden markers/routing. Quotas, backpressure and separate credentials must prevent overload and live side effects. The supplement details these deployment contracts.

''' +s[b:];p.write_text(s,newline='\n')
p=M/'sections/42-live-timing-main.tex';s=p.read_text();a=s.index('\\textbf{Finding.}')
s=s[:a]+r'''\textbf{Finding.} The same-capture timing contrast establishes schedule leakage missed by length-only evaluation. Exp~3's 50.0/50.0\% and Exp~4's 61.4/53.4\% also differ in attacker and collection scope. Within measured conditions, cheaper per-call framing leaves higher full-union inference; offline WF adapters identify lower-byte candidates under the common seven. Selecting between transport shaping and dispatch isolation therefore requires both the receiver boundary and the matched cost object.
''';p.write_text(s,newline='\n')
p=M/'sections/37-transfer-tests.tex';s=p.read_text();a=s.index('\\paragraph{Synthesis}')
s=s[:a]+r'''\paragraph{Synthesis}
The decision table joins the four demonstrations to the record audit: re-measure the changed emitter, executed state, calibration or observation boundary, while retaining evidence whose operating point still matches.
''';p.write_text(s,newline='\n')
print('DUPLICATED_EXPOSITION_COMPACTED')
