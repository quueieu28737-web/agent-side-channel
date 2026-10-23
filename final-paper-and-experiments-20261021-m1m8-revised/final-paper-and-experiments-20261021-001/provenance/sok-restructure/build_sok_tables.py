"""Render the 58-family map and 20 x 9 audit from archived source records.

The layer normalization below is a documented presentation mapping of existing
descriptions, not a new source-reading or independent coding claim.
"""
from pathlib import Path
from collections import Counter
import csv,hashlib,json,re,sys
P=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
INDEX=P/'evidence/retained-release007/search-update/final-family-index.csv'
AUDIT=P/'experiments/revision-m1-m8/m6_split_checks.csv'
NAMES=dict(x.split('|') for x in '''agentprint2025|AgentPrint
uitraces2026|UI Traces
jeong2026wra|WRA
wang2026fpagent|FP-Agent
weiss2024prompt|Remote keylogging
promptpeek2025|PromptPeek
netecho2025|NetEcho
earlybird2025|Early Bird
inputsnatch2024|InputSnatch
whisperleak2025|Whisper Leak
spillbeans2025|Spill the Beans
spliceleak2026|SpliceLeak
timewilltell2024|Time Will Tell
prompt_echo2026|Prompt Echo
gao2025iknow|I Know What You Said
wei2024speculation|Speculative decoding
gu2026behindbars|Behind Bars
gu2025promptcaching|Prompt-cache audit
kang2026whoseagent|Whose Agent?
dangol2026workflow|Dangol workflow
abubakar2026contention|Cache contention
shahriar2026agenttell|AgentTell
pouryousef2026traffic|Cloud traffic benchmark
carlini2024remote|Remote timing
song2026personafingerprint|PersonaFingerprint
hornetz2026tdxray|TDXRay
weiss2026detokenization|Detokenization Leaks
gan2026clawguard|ClawGuard
geng2026sigleak|SIGLEAK
oderinwale2026procgrep|ProcGrep
alhazbi2025rhythm|LLMs Have Rhythm
ding2025moecho|MoEcho
debenedetti2024privacy|ML privacy channels
yona2024stealing|MoE prompt stealing
chaudhuri2025energon|Energon
chu2025safekv|SafeKV
weng2026archsnoop|ArchSnoop
zhu2026turing|AHB
george2025cycles|Cycle detection
solomon2026lumimas|LumiMAS
majidi2026leakylms|Leaky Language Models
addagada2026kvgov|KVGov
scheinert2026rca|LLM-serving RCA
fayolle2026webagents|Web-agent unmasking
park2026crosscampaign|Campaign attribution
wang2026agentprov|AgentProv
wang2026lidar|Lidar
jiao2025llmwfin|LLM-WFIN
revankar2026mirage|MIRAGE
chen2026routingmetadata|Routing metadata
hadad2026shape|Shape and Substance
politis2026splitdecoy|SplitDecoy
nazaraliyev2026page404|PAGE404
alhalawani2026physicaledge|Edge EM leakage
chen2026sparleak|SparLeak
jo2026sparseety|SparSEEty
lee2026otro|OTRO
wu2026cacheprune|CachePrune'''.splitlines())
OVERRIDES={
 'fayolle2026webagents':('3,7','3,7','Network/protocol/browser fingerprints observed at website protocol and JavaScript surfaces.'),
 'park2026crosscampaign':('5,6,8','6,8','Action-order and timing structure from asynchronous tool-use campaign logs.'),
 'wang2026agentprov':('5,6','6','Tool-use policy distributions observed by the active auditor.'),
 'wang2026lidar':('5,6','6','Harness action roles, tool commands and recovery observed by the verifier.'),
 'jiao2025llmwfin':('1,2','1,3','Loading-phase interrupt activity and serving-query packet traces.'),
 'revankar2026mirage':('2,5','2','Generation and planning activity measured through privileged residual-stream hooks.'),
 'chen2026routingmetadata':('2','4','Serving router choices visible to the gateway/log observer.'),
 'hadad2026shape':('1,2','1','Dynamic-resolution compute and LLC contention measured by a local co-tenant.'),
 'politis2026splitdecoy':('2','2','Split-training backward gradient support visible to the untrusted compute node.'),
 'nazaraliyev2026page404':('1','1','Hardware page-migration effects observed through shared migration resources.'),
 'alhalawani2026physicaledge':('1','1','Physical EM emanation and a proximate passive receiver.'),
 'chen2026sparleak':('1,2','1','Sparse KV access observed through shared GPU cache/TLB activity.'),
 'jo2026sparseety':('1,2','1','Sparse-neuron page access observed by a privileged hypervisor.'),
 'lee2026otro':('1,2','1','Tokenizer memory accesses and ORAM counts observed by an untrusted hypervisor.'),
 'wu2026cacheprune':('2','4','KV reuse timing observed through a cross-user TTFT query oracle.'),
 'scheinert2026rca':('1,2','2','Hardware/resource and serving telemetry visible to the operator.'),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=[r for r in csv.DictReader(INDEX.open(encoding='utf-8-sig')) if r['classification']=='core']
    assert len(rows)==58 and {r['citation_key'] for r in rows}==set(NAMES)
    derived=[]
    for r in rows:
        k=r['citation_key'];g=','.join(sorted(set(re.findall(r'P([1-8])',r['signal_origin']))));o=','.join(sorted(set(re.findall(r'P([1-8])',r['observation_layer']))))
        note='Layer codes retained from archived signal_origin and observation_layer.'
        if k in OVERRIDES:g,o,note=OVERRIDES[k]
        assert g and o,k
        typ={'content_or_hidden_property_inference':'I','identity_provenance_attribution':'II','authorized_integrity_diagnostic':'IV'}[r['target_relation']]
        if k=='zhu2026turing':typ='III'
        if k=='fayolle2026webagents':typ='II,III'
        if k in ('agentprint2025','pouryousef2026traffic'):typ='I,II'
        derived.append({'citation_key':k,'label':NAMES[k],'generator_layers':g,'observer_layers':o,'type':typ,'archived_target_relation':r['target_relation'],'archived_signal_origin':r['signal_origin'],'archived_observation_layer':r['observation_layer'],'source_version':r['source_version'],'source_locators':r['source_locators'],'presentation_mapping_note':note})
    a=list(csv.DictReader(AUDIT.open(encoding='utf-8-sig')))
    ids=['1','2','3','4a','4b','5','6a','6b','6c'];keys=list(dict.fromkeys(x['citation_key'] for x in a))
    assert len(a)==180 and len(keys)==20
    cells={(x['citation_key'],x['check_id']):x['status'] for x in a};assert len(cells)==180
    symbols={'Bound':r'$\bullet$','Partial':r'\auditpartial','NR-R':r'$\circ$','NR-V':'?','NA':'--'}
    lines=[r'\begin{table}[t]\centering\footnotesize',r'\caption{Per-family evidence bindings for all 20 evaluated-mitigation families. R1--R9 are scoped reuse items, not overall paper scores.}\label{tab:family-audit}',r'\setlength{\tabcolsep}{2.2pt}',r'\begin{tabularx}{\columnwidth}{@{}Y*{9}{c}@{}}\toprule',r'Family & R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9\\\midrule']
    for k in keys:lines.append(NAMES[k]+r'~\cite{'+k+'} & '+' & '.join(symbols[cells[k,i]] for i in ids)+r'\\')
    counts={i:dict(Counter(cells[k,i] for k in keys)) for i in ids}
    lines += [r'\midrule Bound & '+' & '.join(str(counts[i].get('Bound',0)) for i in ids)+r'\\',r'Applicable & '+' & '.join(str(20-counts[i].get('NA',0)) for i in ids)+r'\\',r'\bottomrule\end{tabularx}',r'\par\smallskip\raggedright $\bullet$: bound; \auditpartial: partial; $\circ$: unreported in inspected scope; ?: unverified binding; --: inapplicable. R1 target/polarity; R2 receiver; R3 placement/execution; R4 defended-condition fit; R5 matched adaptation; R6 workload/generator shifts; R7 inference; R8 utility; R9 cost. A bound cell is supported by at least one scoped record. Dangol R5 concerns stored capture; its live-refit binding remains unverified. CachePrune jointly binds R7--R9 at one operating point.',r'\end{table}']
    audit='\n'.join(lines)+'\n'
    d=sorted(derived,key=lambda r:(min(int(x) for x in r['generator_layers'].split(',')),r['generator_layers'],r['label'].lower()))
    def cell(r):return r['label']+r'~\cite{'+r['citation_key']+'} & $'+r['generator_layers']+r'\!\to\!'+r['observer_layers']+'$ & '+r['type']
    lines=[r'\begin{table*}[t]\centering\footnotesize',r'\caption{Complete map of the 58 core study families. Each family appears once; multiple layer/type labels describe different components or objectives within the family.}\label{tab:core-family-map}',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabularx}{\textwidth}{@{}Ycc@{\hspace{1.5em}}Ycc@{}}\toprule',r'Core family & $G\!\to\!O$ & Type & Core family & $G\!\to\!O$ & Type\\\midrule']
    for x,y in zip(d[:29],d[29:]):lines.append(cell(x)+' & '+cell(y)+r'\\')
    lines += [r'\bottomrule\end{tabularx}',r'\par\smallskip\raggedright $G$ denotes signal-generation layers and $O$ the receiving observation layers. Layer indices: 1 hardware; 2 serving/runtime; 3 transport; 4 application/API; 5 orchestration; 6 tools; 7 browser/environment; 8 multi-agent communication. Types: I confidentiality/privacy; II attribution; III human--agent distinction/evasion; IV authorized diagnostics. These are objectives and observer roles, not mutually exclusive security guarantees. Privileged operator receivers and physical receivers are marked by the layer they inspect. Source versions, locators and the normalization of prose-only layer descriptions are in the artifact.',r'\end{table*}']
    mapping='\n'.join(lines)+'\n'
    outputs={'tables/core-family-map.tex':mapping,'tables/family-audit-matrix.tex':audit}
    metadata={'source_index_sha256':sha(INDEX),'source_audit_sha256':sha(AUDIT),'families':derived,'audit_rows':a,'audit_counts':counts,'scope':'Presentation mapping of archived version-bound records. Manual layer normalizations are documented per family; no new independent source review is claimed.'}
    if '--check' in sys.argv:
        for n,s in outputs.items():assert (P/'manuscript'/n).read_bytes()==s.encode(),n
        assert json.loads((HERE/'table_sources.json').read_text())==metadata
    else:
        for n,s in outputs.items():(P/'manuscript'/n).write_text(s,encoding='utf-8',newline='\n')
        (HERE/'table_sources.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('58_CORE_FAMILIES_AND_180_AUDIT_CELLS_MATCH')
if __name__=='__main__':main()
