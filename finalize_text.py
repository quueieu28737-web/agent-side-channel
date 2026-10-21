from pathlib import Path
import csv,json,re
P=Path(__file__).resolve().parent/'final-paper-and-experiments-20261021-m1m8-revised/final-paper-and-experiments-20261021-001';M=P/'manuscript';A=P/'experiments/reviewer-audit'
def update(f,fn):
 p=M/f;p.write_text(fn(p.read_text()),encoding='utf-8')
update('main.tex',lambda s:s.replace('including 39 intervention result records from 20 mitigation families','retaining 39 scoped result records and auditing 20 mitigation families'))
update('sections/01-introduction.tex',lambda s:s.replace('with 39 intervention records and 78 utility/cost field positions from the 20 mitigation families','with 39 scoped records and 78 utility/cost field positions from 26 families, including mitigation and contextual comparison records. The reporting audit covers 20 mitigation families'))
update('sections/03-methodology.tex',lambda s:re.sub(r'Across the \\FinalCore\{\} core families, 20 evaluate mitigations.*?\n',r'Across the \\FinalCore{} core families, 20 evaluate mitigations (16 snapshot families plus four additions). The result ledger is broader: 33 baseline records from 22 families, including six contextual comparators, plus six records from the four added mitigation families. Thus the 39-record ledger spans 26 families and 78 utility/cost field positions; the reporting-audit denominator is 20.\n',s))
update('sections/03-methodology.tex',lambda s:re.sub(r'\\begin\{enumerate\}\n\\item \\textbf\{Screening.*?\\end\{enumerate\}',r'''The saved screening sample has 93/100 three-class agreement ($\kappa=0.886$); the nine-item baseline audit has 134/144 cell agreement across 16 families ($\kappa=0.876$); and the 50-pair sample has 141/150 judgment agreement ($\kappa=0.916$). The latter covers all 13 same-family pairs plus 37 other within-cohort pairs. Full intervals and source locators remain in Supplement S8 and the annotation files.'''.replace('\\','\\\\'),s,flags=re.S))
update('sections/03-methodology.tex',lambda s:s.replace('We recompute agreement from those saved columns.','We retain the recorded agreement summaries and supply their source columns.'))
update('sections/31-result-audit.tex',lambda s:s.replace('In addition to deterministic rule aggregation, a domain-expert human annotator independently dual-coded the audit cells and pairwise judgments', 'The supplied second-coder columns are retained for agreement analysis; coder independence and blinding are not verified by these files').replace('Independent expert dual-coding','Supplied two-column coding').replace('independent two-coder agreement','recorded two-column agreement').replace('independent expert dual-coding','supplied two-column coding').replace('and independent dual-coding','and supplied coding records'))
update('sections/31-result-audit.tex',lambda s:s.replace('Table~\\ref{tab:six-check-audit} splits Check~4 into \\textbf{4a ($D_1$ protected-condition fitting/calibration)} and \\textbf{4b ($D_2$ matched clean-versus-adapted test comparison)}, and splits Check~6 into \\textbf{6a (defended inference outcome)}, \\textbf{6b (task or component utility)} and \\textbf{6c (mechanism or protocol cost)}', 'Table~\\ref{tab:six-check-audit} uses R4 for defended fitting, R5 for a matched adaptation contrast, R7 for inference, R8 for utility and R9 for cost').replace('Check~4a','R4').replace('Check~6b','R8').replace('summarizes the two informative subsets:', 'summarizes two nested informative subsets (the 13 are included in the 102):'))
update('sections/34-search-update.tex',lambda s:s.replace('Independent human/expert dual-coding','Supplied second-coder annotations'))
update('sections/04-scope.tex',lambda s:s.replace(r'($D_0$ vs.\ $D_1/D_2$)',r'($D_0$ vs.\ $D_2$)'))
update('tables/receiver-intervention-matrix.tex',lambda s:s.replace('D1 is not automatically D2.','defended fitting alone does not establish a matched adaptation contrast.'))
update('tables/six-check-audit.tex',lambda s:s.replace('AHB D1-code without verified Table~1 D1-run','AHB refit code without verified Table~1 run binding'))
update('sections/26-corpus-map.tex',lambda s:s.replace('Rather than extracting private user content, Type~II studies identify','Type~II groups studies by an attribution target:').replace('produced a trace.','produced a trace; such attribution can also raise Type~I confidentiality concerns.'))
update('sections/11-discussion.tex',lambda s:s.replace("Discussions of agent privacy often group WRA's decoy requests", "A comparison that groups WRA's decoy requests").replace('together as ``cover traffic,\'\' creating an apparent paradox:', 'together as ``cover traffic\'\' can create an apparent paradox:'))
# Avoid silently inventing unequal denominators inferred only from rounded source rates.
update('sections/11-discussion.tex',lambda s:s.replace("Indeed, AHB's own non-Fake \\texttt{History+Long} configuration (which adjusts timing/trajectory history without fake GUI touches) retains 0.7143 task success (vs.\\ 0.75 Raw).", "The non-Fake \\texttt{History+Long} configuration changes timing/trajectory history. These source-reported condition rates are not treated as a matched effect: condition-specific sample denominators were not independently recovered in this revision."))
update('sections/30-reproducibility-guide.tex',lambda s:s.replace('and \\path{experiments/revision-m1-m8/} containing all scripts, CSVs and JSON summaries for the M1--M8 revisions.', 'and the current replay/analysis artifacts in \\path{experiments/reviewer-audit/}. Historical summaries in \\path{experiments/revision-m1-m8/} are retained for provenance; corrected current tables use the reviewer-audit outputs.'))

# Make the six previously prose-only additions explicit records using existing source-bound family rows.
basepath=P/'evidence/retained-release007/history-release006/evidence-release004/literature/interventions/intervention-result-units.csv'
base=list(csv.DictReader(basepath.open(encoding='utf-8-sig')))
fam={r['citation_key']:r for r in csv.DictReader((P/'evidence/retained-release007/search-update/final-family-index.csv').open(encoding='utf-8-sig'))}
new=[]
for key,uid,scope,boundary in [
 ('wu2026cacheprune','CACHEPRUNE-selective','Selective sharing: marked-token recovery, downstream quality and serving performance','Scope to the tested model/workload/operating point; do not pool contextual guessing.'),
 ('wu2026cacheprune','CACHEPRUNE-context','Contextual exact/semantic guessing after selective sharing','Distinct inference target from direct marked-token recovery; not a paired effect against the selective record.'),
 ('lee2026otro','OTRO-unpadded','Unpadded TTFT and memory footprint','Access-count padding is explicitly excluded from the TTFT cost.'),
 ('lee2026otro','OTRO-epochpad','Access-count padding and conditional leakage','Epoch-padding latency is a derived cost, not a measured padded total TTFT.'),
 ('chen2026sparleak','SPARLEAK-replacement','Sparse-token random replacement and generation quality','Attack overhead is not defense runtime cost; operating points must remain paired.'),
 ('hadad2026shape','SHAPE-padding-estimate','Constant-work padding proposal and latency estimate','Proposed mechanism and cost estimate, not an executed paired defense or measured task utility.')]:
 f=fam[key];new.append({'unit_id':uid,'citation_key':key,'scope':scope,'source_url':f['source_url'],'source_sha256':f['source_sha256'],'source_path':f['source_file'],'source_locator':f['source_locator'],'utility_source_statement':f['utility'],'cost_source_statement':f['cost'],'defense_source_statement':f['defense'],'evidence_boundary':boundary,'record_origin':'Revision recordization of supplied family extraction; no fresh source-independent recoding'})
allrec={'baseline_source':str(basepath.relative_to(P)).replace('\\','/'),'baseline_records':base,'added_records':new,'total_records':len(base)+len(new),'total_families':len(set(r['citation_key'] for r in base+new)),'reporting_audit_families':20,'utility_cost_field_positions':78}
(A/'combined_result_records.json').write_text(json.dumps(allrec,indent=2,ensure_ascii=False),encoding='utf-8')
update('sections/31-result-audit.tex',lambda s:s+'\nThe current \\path{combined_result_records.json} makes the six expansion records explicit alongside the 33 preserved baseline records: 39 records from 26 distinct families, while the reporting audit covers 20 mitigation families. The six additions are recordizations of the supplied source-bound extraction, not a new independent coding pass.\n')

# Utility intervals in the rendered supplement, not just a machine-readable file.
u=json.loads((A/'retail_utility.json').read_text())
s=r'''\begin{table*}[t]\centering\footnotesize
\caption{Reference-relative state equality on 97 eligible retail tasks. Entries are percentages with conditional 95\% task-bootstrap intervals. No-cover, discard, shadow, read-only and address-write conditions are 100 [100,100] for all three scopes.}
\begin{tabularx}{\textwidth}{@{}Ylll@{}}\toprule
Policy / position & Database equality & Full-account equality & Reference-changed-object equality\\\midrule
'''
names={'live_idempotent_item_swap':'Item self-write','live_instruction_aware':'Instruction aware','live_decoy_account':'Other-account cancellation','live_mutation':'Blind cancellation'}
for r in u:
 if r['policy'] not in names:continue
 cells=[]
 for k,c in [('eligible_native_reward','eligible_native_reward_ci95'),('eligible_user_orders_equal','eligible_user_orders_ci95'),('eligible_gold_touched_equal','eligible_gold_touched_ci95')]:
  cells.append(f"{100*r[k]:.2f} [{100*r[c][0]:.2f}, {100*r[c][1]:.2f}]")
 s+=names[r['policy']]+' '+r['position']+' & '+' & '.join(cells)+r'\\'+'\n'
s+=r'\bottomrule\end{tabularx}\end{table*}'
update('sections/36-tau-cover-details.tex',lambda txt:txt+'\n'+s+'\n')
print('Result ledger families:',allrec['total_families'])
