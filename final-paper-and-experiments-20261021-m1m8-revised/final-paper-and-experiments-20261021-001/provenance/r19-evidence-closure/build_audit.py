"""R19 record-local coding and full 39-record pair census.

Historical inputs are immutable. Codes are explicit scoped judgments, not a
classifier, an independent human review, or a measurement of defense failure.
Run --check to recompute every generated JSON/CSV/TeX output byte-for-byte.
"""
from pathlib import Path
from collections import Counter
import csv,io,itertools,json,hashlib,sys

O=Path(__file__).resolve().parent; P=O.parents[1]; M=P/'manuscript'
read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
ledger=P/'experiments/reviewer-audit/combined_result_records.json'
d=read(ledger); records=d['baseline_records']+d['added_records']; by={r['unit_id']:r for r in records}
oldroot=P/'evidence/retained-release007/history-release006/decision-audit'
oldcode=read(oldroot/'coding.json')
oldpairs=list(csv.DictReader((oldroot/'pair-inventory.csv').open(encoding='utf-8-sig')))
oldlookup={frozenset((r['left_unit'],r['right_unit'])):r for r in oldpairs}
assert len(records)==39 and len(oldpairs)==528

# Order: R1,R2,R3,R4,R5,R6,R7,R8,R9. A dash means inapplicable
# to this record's stated outcome, never a failed experiment.
# B utility is local task OR component utility, consistently across papers.
coding=[
('UI-delay-offline',                'BPBBBBBU-', 'Offline protected identity prediction; no live task outcome or executed delay cost.'),
('WRA-decoy-execution',             'BPB--PBPU', 'Decoy inference and separately judged usefulness are not a same-condition task-utility pair.'),
('NET-upstream-local',             'BBBB?BBUU', 'Scenario-fitted inference; matched clean/refitted protected-test rows not bound.'),
('NET-dummy-padding-simulation',   'BBB??BBUP', 'Replay inference; insertion budget is a partial cost object, not measured live transport.'),
('EARLY-K-calibration-oracle',     'BBBB?BBUP', 'K-conditioned calibrated oracle recovery; query cost is not protected service cost.'),
('EARLY-semantic-deidentification','BBB--B-UB', 'Semantic processor cost; no protected token-recovery outcome in this record.'),
('WHISPER-randompadding-capture',  'BBB??BBUU', 'New padded captures; protected-fit/matched-test run binding unresolved.'),
('WHISPER-batching-replay',        'BBB??BBUU', 'Grouped traces bind AUPRC, not executed delay or task utility.'),
('WHISPER-injection-replay',       'BBB??BBUP', 'Synthetic volume estimate lacks a complete placement-specific resource binding.'),
('SPLICE-CTBF-signal',             'BBB--BBUU', 'CTBF timing-gap outcome; QCP costs are a different component.'),
('SPLICE-QCP-cost',                'BBB--B-UB', 'QCP token/TTFT cost; CTBF signal suppression is not attached to this record.'),
('TIME-length-instruction',        'BBB??BBUU', 'Input-conditioned attack thresholds exist; protected refitting and test pairing remain unverified.'),
('TIME-padding-estimate',          'BBP--B-UB', 'Analytical plaintext padding cost; no independently evaluated protected inference here.'),
('SPEC-padding-REST',              'BBP??BB-B', 'Accuracy and token-payload ratio share the REST padding condition; live/wire interpretation is unresolved.'),
('DANGOL-capture',                 'BBBBBB BUB'.replace(' ',''), 'Capture-scoped matched adaptation, accuracy and transformed byte cost.'),
('DANGOL-livebinding',             'BBB??BBUB', 'Live loopback recovery and wire/latency cost; capture refit cannot be inherited.'),
('SIG-common-guardrail',           'BBB--BBPU', 'Contextual common-instruction control; skill-use proxy is not a paired protected task outcome.'),
('SAFE-post-trigger',              'BBB--BBUP', 'Post-trigger inference and separately reported service costs have no matched operating-point join.'),
('AHB-online-executed',            'BBBP?BBBU', 'Online detectability and objective task accuracy share the executed wrapper; refit code alone is partial.'),
('AHB-offline',                    'BBB??BBU-', 'Offline detectability; online task harm and execution cost do not carry to replay.'),
('KVGOV-partialflush-sim',          'BBB--BBUU', 'Protected simulated inference; HMAC microcost is not its deployment cost.'),
('KVGOV-hardware-gap',             'BBB--B-U-', 'Unprotected hardware timing calibration; no protected-inference or incremental defense cost claim.'),
('KVGOV-HMAC-cost',                'BBB--B-UB', 'Key derivation microcost; neither protected recovery nor lost cache reuse is measured here.'),
('TRAFFIC-prompt-reformulation',   'BPB??PBPU', 'Prompt-intervention inference; semantic preservation asserted rather than task-scored.'),
('TRAFFIC-temperature',            'BPB??PBUU', 'Temperature-conditioned identity inference; protected fit and common test binding unresolved.'),
('CARLINI-fixed-rate',             'BBP--B-UB', 'Rate-curve bandwidth/per-token-delay cost, with live placement unresolved.'),
('GAO-zero-copy-off',              'BBB--P--B', 'Loading/memory cost; structural argument is not measured defended ASR.'),
('TDXRAY-oblivious-map',           'BBB--B-BB', 'Vocabulary coverage and lookup cost are component utility/cost; no measured defended recovery.'),
('AGENTTELL-fixed-instruction',    'BBB--BBPU', 'Loaded/cold instruction context; task-completing controls are not a guardrail-on/off effect.'),
('FP-CLOUDFLARE',                  'BBB--BBBU', 'Contextual access-control and task-completion result, not an audited privacy mitigation.'),
('BAR-co-running-noise',           'BBB--BBUU', 'Contextual channel-capacity result under interference; no task-cost frontier.'),
('RHYTHM-VPN',                     'BBBUUBBUU', 'Contextual VPN test uses a baseline-trained attacker; route cost is unreported.'),
('DEB-filter-origin',              'BBB--BBUU', 'Contextual filter-created membership view; no mitigation of that channel is evaluated.'),
('CACHEPRUNE-selective',           'BBB--BBBB', 'Default selective-sharing configuration links direct recovery, local generation quality and serving cost.'),
('CACHEPRUNE-context',             'BBB--BBBB', 'Contextual recovery uses the same selective-sharing defense; shared quality/cost evidence is counted once at configuration level.'),
('OTRO-unpadded',                  'BBB--B--B', 'Measured unpadded TTFT/memory; padded leakage is a different operating condition.'),
('OTRO-epochpad',                  'BBB--BB-P', 'Conditional leakage with a derived per-epoch cost; full measured padded TTFT remains unbound.'),
('SPARLEAK-replacement',           'BBB??BBBU', 'Table 4 pairs ASR and ROUGE at each model/intensity; attack overhead is not defense cost.'),
('SHAPE-padding-estimate',         'BBPUUBPUP', 'Proposed constant-work defense with derived cost; protected-fit and matched adaptation unreported.'),
]
assert [r[0] for r in coding]==list(by)
context={'SIG-common-guardrail','AGENTTELL-fixed-instruction','FP-CLOUDFLARE','BAR-co-running-noise','RHYTHM-VPN','DEB-filter-origin'}
rows=[]
for rid,codes,note in coding:
 assert len(codes)==9 and set(codes)<=set('BPU?-'),(rid,codes)
 s=by[rid]
 rows.append({'record_id':rid,'family':s['citation_key'],'scope':'contextual' if rid in context else 'mitigation',
              **{f'R{i}':v for i,v in enumerate(codes,1)},
              'configuration_group':'CACHEPRUNE-default' if rid.startswith('CACHEPRUNE-') else rid,
              'rationale':note,'source_url':s['source_url'],'source_locator':s.get('source_locator',s['scope']),
              'source_sha256_as_archived':s['source_sha256']})

# Complete the existing mechanism-question cohorts. This is an explicit
# retrospective expansion, not an assertion that every possible comparison
# across cohorts is meaningless.
cohorts={k:list(v) for k,v in oldcode['cohorts'].items()}
cohorts['cache-service']+=['CACHEPRUNE-selective','CACHEPRUNE-context']
cohorts['local-memory']+=['OTRO-unpadded','OTRO-epochpad','SPARLEAK-replacement','SHAPE-padding-estimate']
cohort={x:k for k,v in cohorts.items() for x in v};assert set(cohort)==set(by)
newjudgments={}
def add(a,b,verdict,reason):
 key=frozenset((a,b)); assert key not in newjudgments
 newjudgments[key]=(verdict,reason)
# Cache-service extension: do not convert missing bridges to incompatibility.
for a in ['CACHEPRUNE-selective','CACHEPRUNE-context']:
 for b in oldcode['cohorts']['cache-service']:
  if b in ['EARLY-semantic-deidentification','SPLICE-QCP-cost','KVGOV-HMAC-cost']:
   v='INCOMPATIBLE';reason='A recovery outcome and a separate processor/padding/key-derivation microcost are different measurement objects.'
  elif b in ['SPLICE-CTBF-signal','KVGOV-hardware-gap']:
   v='INCOMPATIBLE';reason='Token/content recovery is distinct from a raw timing-gap endpoint; the recorded gap cannot replace the recovery metric.'
  elif b=='EARLY-K-calibration-oracle' and a=='CACHEPRUNE-selective':
   v='COMPATIBLE';reason='Both address direct sensitive-token recovery through cache-reuse probes; retain oracle/live configuration and differing cost objects, with no pooled efficacy ranking.'
  elif b=='EARLY-K-calibration-oracle':
   v='INCOMPATIBLE';reason='Contextual guessing from recovered nonsensitive content is a different target/observer contract from direct K-prefix probe recovery.'
  else:
   v='UNRESOLVED';reason='A precise token-recovery versus membership/probe-outcome alignment is not established by these scoped records; shared cache terminology is insufficient.'
  add(a,b,v,reason)
add('CACHEPRUNE-selective','CACHEPRUNE-context','INCOMPATIBLE','Direct token recovery and contextual exact/semantic guessing use distinct inference contracts, even though their defense configuration and its quality/cost evidence are shared.')
# Local-memory/resource extension. Named cost objects differ; two inference
# endpoints remain unresolved rather than being ranked by their metric labels.
local=cohorts['local-memory']
objects={'GAO-zero-copy-off':'model-loading delay and memory','TDXRAY-oblivious-map':'token lookup microcost',
         'OTRO-unpadded':'unpadded serving TTFT and memory','OTRO-epochpad':'conditional access-count information and derived epoch-padding cost',
         'SPARLEAK-replacement':'query/token reconstruction under sparse replacement','SHAPE-padding-estimate':'vision-workload constant-work latency estimate'}
for a,b in itertools.combinations(local,2):
 if frozenset((a,b)) in oldlookup:continue
 if {a,b}=={'OTRO-epochpad','SPARLEAK-replacement'}:
  add(a,b,'UNRESOLVED','Conditional access-count information and reconstruction success have no source-bound common inference scale or receiver bridge.')
 else:add(a,b,'INCOMPATIBLE',f'The requested same-object comparison substitutes {objects[a]} for {objects[b]}; component-wise description remains valid.')
assert len(newjudgments)==31

pairs=[]
for n,(a,b) in enumerate(itertools.combinations(records,2),1):
 ai,bi=a['unit_id'],b['unit_id'];key=frozenset((ai,bi));same=a['citation_key']==b['citation_key'];related=cohort[ai]==cohort[bi]
 if key in oldlookup:
  r=dict(oldlookup[key]);r['historical_pair_id']=r['pair_id'];r['judgment_origin']='retained historical pair judgment'
 else:
  verdict,reason=newjudgments.get(key,('NOT_APPLICABLE','Outside the stated mechanism-question cohorts; no comparison is asserted.'))
  assert related==(key in newjudgments)
  r={'left_unit':ai,'right_unit':bi,'left_family':a['citation_key'],'right_family':b['citation_key'],
     'related_subset':str(related).lower(),'same_family':str(same).lower(),'cohort':cohort[ai] if related else 'NOT_APPLICABLE',
     'descriptive':verdict,'paired_effect':'NOT_APPLICABLE',
     'transfer_left_to_right':'UNRESOLVED' if related else 'NOT_APPLICABLE',
     'transfer_right_to_left':'UNRESOLVED' if related else 'NOT_APPLICABLE',
     'transfer_pair':'UNRESOLVED' if related else 'NOT_APPLICABLE','rule':'R19_explicit_extension' if related else 'R0_outside_scope',
     'descriptive_reason':reason,'paired_effect_reason':'No paired subtraction of common outcomes/test units is supplied by this record pair.',
     'transfer_reason':'A source-bound bridge for unchanged numerical reuse is not established; this is not an observed transfer failure.',
     'left_source':a['source_url'],'left_scope':a.get('source_locator',a['scope']),'left_source_sha256':a['source_sha256'],
     'right_source':b['source_url'],'right_scope':b.get('source_locator',b['scope']),'right_source_sha256':b['source_sha256'],
     'historical_pair_id':'','judgment_origin':'R19 scoped extension'}
  if same:
   r['transfer_left_to_right']=r['transfer_right_to_left']=r['transfer_pair']='INCOMPATIBLE'
   r['transfer_reason']=reason+' Copying the numerical endpoint unchanged across this distinction is unsupported by the positive object mismatch.'
 r['pair_id']=f'F{n:03d}';pairs.append(r)
assert len(pairs)==741
related=[r for r in pairs if r['related_subset']=='true'];same=[r for r in pairs if r['same_family']=='true']
assert len(related)==133 and len(same)==15

joint={}
for name,fields in [('inference_utility',['R7','R8']),('inference_cost',['R7','R9']),
                    ('adapted_inference',['R4','R5','R7']),('inference_utility_cost',['R7','R8','R9']),
                    ('adapted_inference_utility_cost',['R4','R5','R7','R8','R9'])]:
 selected=[r for r in rows if r['scope']=='mitigation' and all(r[k]=='B' for k in fields)]
 eligible=[r for r in rows if r['scope']=='mitigation' and all(r[k]!='-' for k in fields)]
 joint[name]={'fields':fields,'bound_records':[r['record_id'] for r in selected],
              'bound_record_count':len(selected),'bound_families':sorted({r['family'] for r in selected}),
              'distinct_configuration_groups':sorted({r['configuration_group'] for r in selected}),
              'applicable_records':len(eligible)}
summary={'revision':'R19','records':39,'mitigation_records':33,'contextual_records':6,'families':26,'all_pairs':741,
         'related_pairs':len(related),'outside_scope_pairs':741-len(related),'same_family_pairs':15,
         'related_descriptive':dict(Counter(r['descriptive'] for r in related)),
         'same_family_descriptive':dict(Counter(r['descriptive'] for r in same)),
         'same_family_paired_effect':dict(Counter(r['paired_effect'] for r in same)),
         'related_cohorts':dict(Counter(r['cohort'] for r in related)),'record_cells':351,
         'record_status_distributions':{k:dict(Counter(r[k] for r in rows)) for k in [f'R{i}' for i in range(1,10)]},
         'joint':joint,'historical_pairs_preserved':528,'new_related_judgments':31,
         'interpretation':'Joint bindings count within-record configuration-linked evidence, not same-request paired effects. CachePrune direct/context rows share one configuration-level quality/cost package. Cost retains its payload/replay/live object. Contextual controls are excluded from mitigation joint denominators.',
         'sources':{str(f.relative_to(P)):sha(f) for f in [ledger,oldroot/'coding.json',oldroot/'pair-inventory.csv']}}

def j(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def c(v):
 s=io.StringIO(newline='');w=csv.DictWriter(s,list(v[0]),lineterminator='\n');w.writeheader();w.writerows(v);return s.getvalue()
def esc(s):return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_')
outputs={O/'record-audit.json':j(rows),O/'record-audit.csv':c(rows),O/'pair-inventory.csv':c(pairs),O/'summary.json':j(summary)}
labels={'inference_utility':'Inference + utility','inference_cost':'Inference + cost','adapted_inference':'Matched adaptation + inference',
        'inference_utility_cost':'Inference + utility + cost','adapted_inference_utility_cost':'All five bindings'}
t=[r'\begin{table}[t]\centering\footnotesize',r'\caption{Joint evidence within the same mitigation record. Contextual controls are excluded. Counts never combine cells from different records.}\label{tab:r19-joint}',r'\begin{tabularx}{\columnwidth}{@{}Yrrr@{}}\toprule',r'Binding & Records & Families & Configs\\\midrule']
for k,v in joint.items():t.append(f"{labels[k]} & {v['bound_record_count']}/{v['applicable_records']} & {len(v['bound_families'])} & {len(v['distinct_configuration_groups'])}"+r'\\')
t += [r'\bottomrule\end{tabularx}',r'\par\smallskip\raggedright A bound join links the same intervention/workload configuration; it does not require identical sampled requests or establish a paired effect. CachePrune direct/context records share one quality/cost package. Cost includes scoped token-payload and capture bytes, not automatically live wire cost. Full row identities and 351 item judgments are in the supplement.',r'\end{table}']
outputs[M/'tables/r19-joint-bindings.tex']='\n'.join(t)+'\n'
t=[r'\begin{longtable}{@{}p{.25\textwidth}*{9}{c}p{.40\textwidth}@{}}',r'\caption{All 39 record-local judgments. B/P/U/?/-- retain the main-paper meanings; six contextual controls ($\dagger$) are not mitigation denominators.}\label{tab:r19-record-cells}\\',r'\toprule Record & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 & 9 & Source scope and join rationale\\\midrule\endfirsthead',r'\toprule Record & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 & 9 & Source scope and join rationale\\\midrule\endhead',r'\bottomrule\endfoot']
for r in rows:
 rid=esc(r['record_id']).replace('-',r'-\allowbreak{}')
 mark=r'$\dagger$' if r['scope']=='contextual' else ''
 t.append(rid+mark+r'~\cite{'+r['family']+'} & '+' & '.join(r[f'R{i}'] for i in range(1,10))+' & '+esc(r['source_locator'])+'. '+esc(r['rationale'])+r'\\')
t += [r'\end{longtable}']
outputs[M/'tables/r19-record-audit.tex']='\n'.join(t)+'\n'
for f,s in outputs.items():
 if '--check' in sys.argv:assert f.read_text(encoding='utf8')==s,str(f)
 else:f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf8',newline='\n')
print(j(summary))
