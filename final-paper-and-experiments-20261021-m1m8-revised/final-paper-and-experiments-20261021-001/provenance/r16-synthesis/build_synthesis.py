"""Source-bound synthesis overlay; original family/record ledgers remain immutable.

Manual axis coding is conservative: H=reported held-out units/domain, V=variation
or calibration, X=explicit restriction/no such holdout in inspected scope,
?=unresolved in the archived extraction, -=conceptual work (not empirical).
H is not independent reproduction, successful transfer, or certification of all
grouping details. The source excerpts and locators accompany every row.
"""
from pathlib import Path
from collections import Counter
import csv,json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript'
F=P/'evidence/retained-release007/search-update/final-family-index.csv'
L=P/'experiments/reviewer-audit/combined_result_records.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def tex(s):
 for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
 return s.replace('–','--').replace('—','--').replace('×',r'$\times$')
# Six columns: task/input/user; model; harness/topology; hardware; network/load; time.
# A comparison among models is V, not H. A held-out prompt is H only in T.
CODING='''agentprint2025|??????|Random trace splits; prompt grouping unresolved
uitraces2026|VVV???|Cross-task/site comparisons; exact-question overlap remains
jeong2026wra|H?????|Prompt tests and synthetic persona split; version reconciliation open
wang2026fpagent|H?X???|Separate task holdout; visitor/host separation unresolved
weiss2024prompt|H?V?VV|OOD inputs; browser/API and day/night buffering controls
promptpeek2025|V???V?|Candidate-prior and simulated request-load sweeps
netecho2025|V?V???|Deployment/frontend scenarios; independent split binding unresolved
earlybird2025|?V????|Provider observations and candidate calibration; grouped split unresolved
inputsnatch2024|H?????|Held-out and generated target prompts; candidate-prior dependence
whisperleak2025|HV????|Unique target-prompt holdout; model/provider comparisons
spillbeans2025|V?????|Exposure/monitor sweeps; independent capture grouping unresolved
spliceleak2026|V?????|Bounded cloze tasks and chunk/candidate coverage
timewilltell2024|????VV|Concurrent network/load profiling; short-window recalibration
prompt_echo2026|HV????|Overlap-filtered prompts; models evaluated separately
gao2025iknow|HVVV??|Prompt overlap filtering; model/hardware/framework comparisons
wei2024speculation|H???V?|New traces and OOD paraphrases; remote/load conditions
gu2026behindbars|?V?V??|Model identification CV; additional hardware evaluation
gu2025promptcaching|?V???V|Provider survey over two months; historical exposure only
kang2026whoseagent|??????|Trial split; task/site/version independence unresolved
dangol2026workflow|??H???|Leave-composition-out; stored and live populations separated
abubakar2026contention|??V?V?|Serving-stack and interleaved-load controls
shahriar2026agenttell|V???V?|Secret rotation; cold/loaded and equal-completability controls
pouryousef2026traffic|??H???|Topology shift distinct from feature-view restriction
carlini2024remote|?V???V|Month-long observations; method/model changes confounded
song2026personafingerprint|??X???|Pooled sites; leave-site-out not verified
hornetz2026tdxray|??????|Tokenizer-localized LLM case; AES result separate
weiss2026detokenization|??X???|Explicit same-instance profiling restriction
roh2026spillage|V?????|Task-irrelevance and selected-site evaluation
yu2026plantwin|V?????|Template candidate pool; production transfer unresolved
xu2026sicc|??????|Authorized-view theorem; empirical shift binding unresolved
qiao2026topr|V?????|Benchmark and alignment populations differ
gan2026clawguard|??V??V|Carrier recollection and cycle drift; not zero-shot transfer
geng2026sigleak|V?????|Paired prompts; not physical-skill removal
oderinwale2026procgrep|H?V???|Task-grouped attribution under scaffold regimes
umar2025secemb|?X????|Single GPT-2 workload; DLRM result separate
wu2025mobileagents|??????|Direct leakage cases; holdout binding unresolved
mudryi2025hidden|??????|Content exfiltration/access-control cases
ukani2025browserprivacy|??V???|Browser/profile-state measurements; mixed leakage mechanisms
alhazbi2025rhythm|?V??HV|New captures and cross-network tests; overlapping windows caveat
ding2025moecho|HV??V?|Cross-template/dataset tests; contention/context conditions
nazari2024llmfin|?H????|Unseen variants within known architecture families
debenedetti2024privacy|?V????|Enumerative/filter probes across named models; no learned split
yona2024stealing|??????|Constructive word extraction in controlled shared batches
chaudhuri2025energon|?V????|Known-candidate CV; exploratory hardware not transfer proof
chu2025safekv|?V????|Named serving models; calibration/test separation unreported
anwar2026infernet|?V?V??|Same-label mixed-model and platform comparisons
weng2026archsnoop|?H?V??|Random-weight training to official/fine-tuned models; power modes
ghaleb2026codingfingerprint|X?X??X|PR CV; repository/time/human-mediated holdouts unreported
zhu2026turing|??X???|Offline/live humanization; website-transfer binding unresolved
wang2026dialogue|H?X???|User-disjoint cross-topic split; no verified cross-service test
george2025cycles|X?X??X|One application; no held-out split located
solomon2026lumimas|?VV???|Nonoverlap logs; backend/platform comparisons; task grouping open
cui2026symdiag|VV????|Domains/reasoners vary with inputs and feedback
majidi2026leakylms|?H?V??|Held-out architecture configurations; known-GPU calibration
addagada2026kvgov|???V??|Simulation, A100 timing and HMAC microcost separate
lahjouji2026datacentric|------|Conceptual synthesis; empirical holdout not applicable
scheinert2026rca|??X???|Single serving deployment with injected faults
shao2026zeroprint|?V????|Known-family provenance pairs; partition not re-extracted
leshin2026endpoint|??V??V|Controlled endpoint changes over matched time windows
zhu2026stepfinder|H?????|Task-disjoint subsets; denominator reconciliation unresolved
fayolle2026webagents|?V????|Six agents with human/scraper controls
park2026crosscampaign|V?V???|Crossed-style and regenerated conditions; execution stress subset
wang2026agentprov|?V????|Substituted checkpoints; system-prompt perturbation
wang2026lidar|?VV???|Enrollment-only identity; two harnesses and perturbations
jiao2025llmwfin|V?????|Site traces; loading versus query phases
revankar2026mirage|VV????|Encodings/models/scenarios; matched decoder-layer controls
chen2026routingmetadata|V?V???|Request domains and routers; exploratory sensitive-label gate
hadad2026shape|VVVV??|Geometry/model/cache/hardware conditions; padding estimate
politis2026splitdecoy|??????|Repeated seeds; forward/backward boundary, not a holdout
nazaraliyev2026page404|VV????|Architecture and prompt-length targets; transfer binding open
alhalawani2026physicaledge|H?????|Unseen-word test separate from profiled vocabulary recovery
chen2026sparleak|VVV???|Models/datasets/sparse mechanisms; per-phase outcomes
jo2026sparseety|VVV???|Models/datasets/implementations; oracle-conditioned extraction
lee2026otro|??????|Closed-corpus conditional leakage; epoch cost separately derived
wu2026cacheprune|VV????|Models/workloads and detector-miss stress; separate fits
kotevska2026privacyfoundations|------|Conceptual contract; cross-institution example illustrative
dpmemview2026|??????|Semantic response privacy; holdout binding not re-extracted
pricon2026|??????|Semantic cloud consultation; holdout binding not re-extracted
mondol2025scaar|??????|LLM EM/length test; other classifier results separate
pennas2026cachesolidarity|??????|Candidate-prefix timing gap; no scored inference error
zhou2026visionencoder|??????|Representation inversion; holdout binding not re-extracted
politis2026gradients|??????|Split-compute content inversion; holdout binding unresolved'''
codes={s.split('|')[0]:s.split('|')[1:] for s in CODING.splitlines()}
families=list(csv.DictReader(F.open(encoding='utf-8-sig')))
assert len(families)==len(codes)==82 and {r['citation_key'] for r in families}==set(codes)
axes=['task_input_user','model','harness_topology','hardware','network_load','time']
names='AgentPrint|UI Traces|WRA|FP-Agent|Prompt length|PromptPeek|NetEcho|Early Bird|InputSnatch|Whisper Leak|Spill the Beans|SpliceLeak|Time Will Tell|Prompt Echo|I Know What You Said|Speculation|Behind Bars|Prompt caching|Whose Agent|Workflow traffic|GPU contention|AgentTell|Traffic benchmark|Remote timing|Persona fingerprint|TDXRay|Detokenization|Spillage|PlanTwin|SICC|TOPR|ClawGuard|SIGLEAK|ProcGrep|SecEmb|Mobile agents|Hidden risks|Browser privacy|LLMs Have Rhythm|MoEcho|LLM-Fin|ML privacy channels|MoE stealing|Energon|SafeKV|InferNet|ArchSnoop|Coding fingerprints|AHB|WildAuth|Cycles|LumiMAS|SymDiag|LeakyLMs|KVGov|Data-centric survey|Serving RCA|ZeroPrint|Endpoint fingerprints|StepFinder|Web-agent detection|Cross-campaign|AgentProv|LiDAR|LLM-WFIN|MIRAGE|Routing metadata|Shape and Substance|SplitDecoy|PAGE404|Edge EM|SparLeak|Sparseety|OTRO|CachePrune|Privacy foundations|DP-MemView|PriCon|SCAAR|CacheSolidarity|Vision encoder|Split gradients'.split('|')
assert len(names)==82
rows=[]
for i,r in enumerate(families,1):
 k=r['citation_key'];c,n=codes[k];assert len(c)==6 and set(c)<=set('HVX?-')
 rows.append({'id':f'F{i:02d}','name':names[i-1],'citation_key':k,'classification':r['classification'],'axes':dict(zip(axes,c)),
 'interpretation':n,'source_url':r['source_url'],'source_version':r['source_version'],'source_locators':r['source_locators'],
 'archived_extraction':{f:r.get(f,'') for f in ['RQ3','system_sample_split','baselines_generalization','source_binding','source_sha256','source_access_scope']}})
summary={scope:{a:dict(Counter(r['axes'][a] for r in rows if scope=='all' or r['classification']==scope)) for a in axes} for scope in ['all','core','adjacent']}
save(O/'holdout-matrix.json',{'scope':'Manual synthesis of existing source-bound extraction; no new whole-paper recoding or absence census','states':{'H':'Explicit reported held-out unit/domain; details and success still scoped','V':'Condition comparison/variation/calibration; disjoint transfer not certified','X':'Explicit restriction or absent/unverified holdout in inspected scope (see note)','?':'Axis not resolved by archived extraction; never counted as absence','-':'Conceptual family: empirical holdout inapplicable'},'source_sha256':sha(F),'axes':axes,'rows':rows,'summary':summary})
with (O/'holdout-matrix.csv').open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=['id','citation_key','classification']+axes+['interpretation','source_url','source_locators']);w.writeheader()
 for r in rows:w.writerow({**{k:r[k] for k in ['id','citation_key','classification','interpretation','source_url','source_locators']},**r['axes']})
# Three compact, full-width matrices in the same submission PDF, after references.
out=[r'\section{Family-Level Holdout Evidence}\label{app:holdouts}',r'Tables~\ref{tab:holdouts1}--\ref{tab:holdouts3} cover all 82 indexed families. T: task/input/user; M: model; C: harness/topology; H: hardware; N: network/load; D: time. \textbf{H} records an explicitly reported held-out unit/domain, \textbf{V} a condition comparison or recalibration, \textbf{X} an explicit restriction or absent/unverified holdout in the inspected scope, and \textbf{?} an unresolved axis. A dash applies only to conceptual families. H does not certify all grouping details or successful transfer; V is not a holdout. Notes restrict each code. Core and adjacent families remain separate (C/A). The machine-readable matrix preserves the full source excerpts, locators and input hash; these tables synthesize that archived extraction rather than claim a new full-paper audit.']
for j in range(3):
 out += [r'\begin{table*}[p]\centering\footnotesize',rf'\caption{{Holdout evidence, families {j*28+1}--{min((j+1)*28,82)}. Codes and axes are defined in Appendix~\ref{{app:holdouts}}.}}\label{{tab:holdouts{j+1}}}',r'\setlength{\tabcolsep}{3pt}\begin{tabularx}{\textwidth}{@{}p{.20\textwidth}cccccccY@{}}\toprule',r'Family & Scope & T & M & C & H & N & D & Source locator and qualification\\\midrule']
 for r in rows[j*28:(j+1)*28]:
  # Citation is the unambiguous family identity; stable F-number permits CSV joins.
  loc=r['source_locators'].replace('§','Sec. ')
  if loc.startswith('['):loc='; '.join(json.loads(loc))
  # Retain first locator when archival source list is long; full locator stays CSV.
  if len(loc)>85:loc=loc.split(';')[0]+'; source index'
  out.append(rf"{r['id']} {tex(r['name'])}~\cite{{{r['citation_key']}}} & {r['classification'][0].upper()} & "+' & '.join(r['axes'].values())+' & '+tex(r['interpretation']+'. '+loc)+r'\\')
 out += [r'\bottomrule\end{tabularx}\end{table*}']
(M/'sections/56-holdout-matrix.tex').write_text('\n'.join(out)+'\n',encoding='utf8')
# Exhaustive mode inventory. Classification is about the record, never whole-paper quality.
groups={
 'Trace transformation':['UI-delay-offline','NET-dummy-padding-simulation','WHISPER-batching-replay','WHISPER-injection-replay','DANGOL-capture','AHB-offline'],
 'Simulation or derived estimate':['EARLY-K-calibration-oracle','TIME-padding-estimate','KVGOV-partialflush-sim','OTRO-epochpad','SHAPE-padding-estimate'],
 'Component or calibration measurement':['SPLICE-QCP-cost','KVGOV-hardware-gap','KVGOV-HMAC-cost','GAO-zero-copy-off','TDXRAY-oblivious-map','OTRO-unpadded'],
 'Placement unresolved':['SPEC-padding-REST','CARLINI-fixed-rate'],
 'Executed collection or prototype':['WRA-decoy-execution','NET-upstream-local','EARLY-semantic-deidentification','WHISPER-randompadding-capture','SPLICE-CTBF-signal','TIME-length-instruction','SIG-common-guardrail','SAFE-post-trigger','AHB-online-executed','TRAFFIC-prompt-reformulation','TRAFFIC-temperature','AGENTTELL-fixed-instruction','FP-CLOUDFLARE','BAR-co-running-noise','RHYTHM-VPN','DEB-filter-origin','CACHEPRUNE-selective','CACHEPRUNE-context','SPARLEAK-replacement','SHAPE-DUMMY']}
groups['Executed collection or prototype'].remove('SHAPE-DUMMY')
groups['Executed collection or prototype'].append('DANGOL-livebinding')
ledger=json.loads(L.read_text());records=ledger['baseline_records']+ledger['added_records'];ids=[i for g in groups.values() for i in g]
assert len(records)==len(ids)==39 and set(ids)=={r['unit_id'] for r in records}
inventory=[]
for r in records:
 g=next(g for g,v in groups.items() if r['unit_id'] in v)
 inventory.append({'record':r['unit_id'],'family':r['citation_key'],'mode_group':g,'source_mode':r.get('mode',''),'source_scope':r['scope'],'locator':r.get('source_locator',r['scope']),'source_sha256':r.get('source_sha256'),'source_url':r.get('source_url'),'boundary':r.get('evidence_boundary','')})
save(O/'record-mode-inventory.json',{'source_sha256':sha(L),'records':inventory,'counts':{g:len(v) for g,v in groups.items()},'rule':'One primary measurement mode per scoped record. Executed includes collected/prototype conditions and does not imply matched full-workflow utility. Mode-unresolved remains separate; simulation with empirical calibration is classified by its evaluated result.'})
t=[r'\begin{table}[t]\centering\footnotesize',r'\caption{Measurement modes of all 39 result records (26 families). Counts classify records, not paper quality or defense success.}\label{tab:record-modes}',r'\begin{tabularx}{\columnwidth}{@{}Yr@{}}\toprule Mode of scoped result & Records\\\midrule']
for g,v in groups.items():t.append(tex(g)+' & '+str(len(v))+r'\\')
t += [r'\bottomrule\end{tabularx}\end{table}']
(M/'tables/r16-record-modes.tex').write_text('\n'.join(t)+'\n')
s=[r'\section{Complete Record-Mode Synthesis}\label{app:record-modes}',r'Every record is classified once by its primary measurement mode. Executed collection/prototype includes separately collected conditions and does not imply paired full-workflow utility. A simulated or derived result remains in that category even when its parameters were measured. Two placement-unresolved records remain explicit. This exhaustive census supplies the denominator for the three explanatory lenses in the main paper; those lenses are retrospective illustrations, not a prevalence sample.',r'\begin{longtable}{@{}p{.30\textwidth}p{.25\textwidth}p{.38\textwidth}@{}}\toprule Record & Mode & Source locator\\\midrule\endhead']
for r in inventory:s.append(tex(r['record'])+rf"~\cite{{{r['family']}}} & "+tex(r['mode_group'])+' & '+tex(r['locator'])+r'\\')
s += [r'\bottomrule\end{longtable}',r'For OTRO-epochpad, the estimate category identifies the derived padding cost; it does not negate the reported conditional-leakage measurement. EARLY-K similarly combines measured calibration with a stochastic oracle result. These mixed records illustrate why the measured component must remain attached to the claim.']
(M/'sections/57-record-mode-synthesis.tex').write_text('\n'.join(s)+'\n')
save(O/'synthesis-check.json',{'passed':True,'families':82,'core':sum(r['classification']=='core' for r in rows),'adjacent':sum(r['classification']=='adjacent' for r in rows),'cells':492,'records':39,'record_families':len(set(r['family'] for r in inventory)),'mode_counts':{g:len(v) for g,v in groups.items()},'holdout_summary':summary})
print(json.dumps({'families':82,'modes':{g:len(v) for g,v in groups.items()},'axes':summary['all']}))
