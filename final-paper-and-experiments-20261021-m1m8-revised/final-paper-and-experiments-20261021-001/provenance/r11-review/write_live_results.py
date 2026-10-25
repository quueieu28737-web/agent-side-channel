"""Publish R15 text only after all saved live runs pass reconstruction."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';D=P/'experiments/sp2027-r15-live-planner'
assert json.loads((D/'verification.json').read_text())['passed']
a=json.loads((D/'live_analysis.json').read_text());s=a['summary'];b=s['baseline'];j=s['joint']
delta=100*a['paired_reward_difference'];lo,hi=[100*x for x in a['customer_bootstrap_ci95']]
short=(r'\paragraph{Test live planner utility at its own boundary}'+'\n'+f"A paired 50-task GLM study runs 100 fresh planner episodes with real isolated prefix-cover execution and emulated response deadlines. Baseline and prefix-shadow succeed on {b['successes']}/50 and {j['successes']}/50 tasks (difference {delta:+.1f} points, customer interval [{lo:.1f},{hi:.1f}]). Withheld executed-tool responses trigger subsequent planner actions. This measures the prefix scheduler's utility under injected delays; terminal flush and TLS framing belong to a different mechanism. The supplement retains every request, fault and outcome.\n\n")
p=M/'sections/37-transfer-tests.tex';t=p.read_text();anchor=r'\textbf{Finding.} Better read-order compliance'
if r'\paragraph{Test live planner utility' not in t:t=t.replace(anchor,short+anchor)
p.write_text(t)
header=r'''\section{Live Planner Utility with Prefix Shadow Execution}\label{sec:live-planner-utility}
This exploratory paired study selects 50 existing task IDs by a frozen SHA-based ordering before new collection, with two fresh GLM planner episodes per task. Both agent and user contexts issue new model requests; cached decisions are used only to resume the same episode after transport failure. The 100 episodes use the served GLM alias, native single-tool actions, a 16,384-token budget and ten workers. They share known tasks with earlier studies and are not a new-customer confirmation. Arm order alternates by task parity.

\paragraph{Execution and deadline contract}
The baseline executes real actions in the retail environment. The prefix-shadow arm additionally executes at most one training-template deficit call on isolated state after each real call; its response is hidden from the planner. Both arms delay each real response by 20\,ms, with another 20\,ms for cover. For task IDs divisible by five, the first tool response receives another 200\,ms delay. The 120\,ms deadline is evaluated against this configured delay, not OS scheduling noise. The real operation can already have executed when its response is replaced by a timeout warning; the next planner request sees that warning and can inspect or retry the state. This tests reaction to a controlled execution/observation mismatch. There is no terminal flush, constant TLS framing or actual WAN path in this utility diagnostic.

\begin{center}\small\begin{tabular}{lrr}\toprule
Outcome & Baseline & Prefix shadow\\\midrule
'''
lines=[]
for label,key in [('Episodes','episodes'),('Native successes','successes'),('Terminal protocol failures','protocol_errors'),('Real tool calls','real_calls'),('Isolated cover calls','cover_calls'),('Injected response timeouts','timeouts'),('Tool actions following timeout','post_timeout_actions')]:
 lines.append(f'{label} & {b[key]} & {j[key]}'+r'\\')
lines.append(f"Final-pass response-wait p95 (ms) & {1000*b['tool_response_p95_seconds']:.1f} & {1000*j['tool_response_p95_seconds']:.1f}"+r'\\')
tail=r'''\bottomrule\end{tabular}\end{center}

\paragraph{Interpretation and verification}
'''+f"The paired native-success difference is {delta:+.1f} percentage points, with a 2,000-draw customer-bootstrap interval [{lo:.1f},{hi:.1f}] over {a['customers']} customers. All protocol failures remain in the denominator. Subsequent actions demonstrate live reactions to timeout observations; their count alone does not establish correct recovery. "+r'''The verifier rebuilds actual and reference tool states, checks output requirements and native rewards, matches model-request counts, and checks all live-metric rows. Recorded response waits are from the final execution pass: cache recovery deterministically replays completed action prefixes and their delays. The frozen Windows monotonic clock has 15.625\,ms resolution, so sub-tick differences are not resolved. These waits exclude LLM generation and WAN transit, and are not original uninterrupted end-to-end latencies. Reward is measured on the actual model decisions, rather than inherited from an undefended trajectory.

\paragraph{Transport recovery provenance}
An import-order bug selected the shared endpoint adapter, which honored a 180\,s caller timeout despite the live protocol's intended 600\,s transport wait. After 97 completed episodes, explicit adapter resolution selected the local 600\,s implementation; request bodies, model settings, parsing and all cached decisions remained unchanged. The amendment preserves the old adapter, hashes, logs and no-progress stop, and permits bounded recovery after the identified code fix. This infrastructure wait is separate from the experimentally injected 120\,ms tool-response deadline. Failed model outputs are terminal outcomes, not transport retries. The utility estimate applies to this prefix scheduler and fault model; it cannot supply a reward value for the full joint framing/flush replay rows in Exp~3.
'''
(M/'sections/55-live-planner-utility.tex').write_text(header+'\n'.join(lines)+'\n'+tail)
p=M/'supplement.tex';t=p.read_text();anchor=r'\clearpage\input{sections/54-transfer-boundaries}'
if '55-live-planner-utility' not in t:t=t.replace(anchor,anchor+'\n'+r'\clearpage\input{sections/55-live-planner-utility}')
p.write_text(t)
p=M/'sections/10-open-challenges.tex';t=p.read_text().replace('and unmeasured live defended-planner utility. Local RPC timing excludes LLM generation, WAN transit and timing-dependent replanning.','and measured prefix-shadow planner utility under injected response deadlines. Full framing/flush deployment utility remains unmeasured. Local RPC timing excludes LLM generation and WAN transit.').replace('The additional Luna study has 29 training episodes per prompt. Fresh independent customers, fixed open weights, cross-vendor and cross-environment tests, provider-backend measurements and live replanning are the next validation axes.','Luna has 29 training episodes per prompt; MiniMax and GLM each use 69 training tasks. The two-endpoint matrices and live prefix-shadow study reuse known customers. Fresh customers, fixed open weights, verified cross-vendor identities, new environments and provider-backend measurements are the next validation axes.')
p.write_text(t)
p=M/'sections/01-introduction.tex';t=p.read_text().replace('Deployment-wide security and live defended-planner utility require the additional validation specified in','A separate 100-episode live study measures prefix-shadow utility under injected deadlines. Deployment-wide security and full joint utility require the validation specified in');p.write_text(t)
print('LIVE_TEXT_WRITTEN',delta,lo,hi)
