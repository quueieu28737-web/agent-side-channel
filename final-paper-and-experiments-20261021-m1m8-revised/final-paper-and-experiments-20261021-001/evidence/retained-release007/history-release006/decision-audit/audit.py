"""Deterministic aggregation of explicitly coded source judgments; no model/fits/network."""
import argparse
import csv
import hashlib
import io
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_RELEASE = REPO / 'artifacts/sok-anonymous-review-20261020-005/evidence-release004'
STATUS = {'SAT','PARTIAL','NR-R','NR-V','NA'}
VERDICTS = {'COMPATIBLE','INCOMPATIBLE','UNRESOLVED','NOT_APPLICABLE'}
CHECKS = [
    'Hidden target and protection relation',
    'Receiver fields and linkage permissions',
    'Protection placement and action dispatch',
    'Protected fitting and matched test when adaptation is at issue',
    'Workloads and generator shifts actually tested',
    'Inference, objective/policy utility and applicable cost bound together',
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def encode_csv(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode('utf-8')

def count(rows, field):
    return dict(sorted(Counter(r[field] for r in rows).items()))

def derive(release):
    inputs = {
        'units': release / 'literature/interventions/intervention-result-units.csv',
        'families': release / 'literature/interventions/current-core-intervention-status.csv',
        'ledger': release / 'literature/final-inclusion-ledger.csv',
        'dispositions': release / 'empirical/derived-001/all33-dispositions.csv',
        'utility_cost': release / 'empirical/derived-001/all66-utility-cost-fields.csv',
    }
    hashes_before = {name:sha(path) for name,path in inputs.items()}
    units = read_csv(inputs['units'])
    fam = read_csv(inputs['families'])
    code = json.loads((HERE/'coding.json').read_text(encoding='utf-8'))
    ids = [r['unit_id'] for r in units]
    by_id = {r['unit_id']:r for r in units}
    assert len(ids)==33 and len(set(ids))==33
    assert len({r['citation_key'] for r in units})==22
    assert set(code['endpoints'])==set(ids)
    members = [i for cohort in code['cohorts'].values() for i in cohort]
    assert len(members)==33 and set(members)==set(ids)
    cohort_of = {i:k for k,group in code['cohorts'].items() for i in group}
    evaluated = {r['citation_key'] for r in fam if r['status']=='VERIFIED_EVALUATION'}
    assert len(evaluated)==16 and set(code['families'])==evaluated
    explicit = {frozenset((r['a'],r['b'])):r for r in code['same_family_pairs']}
    expected_same = {frozenset((a['unit_id'],b['unit_id'])) for a,b in itertools.combinations(units,2) if a['citation_key']==b['citation_key']}
    assert len(explicit)==13 and set(explicit)==expected_same
    alignments = [set(x) for x in code['positive_descriptive_alignments']]
    # These positive, semantic conflicts are source-coded definitions, not raw text inequality.
    conflicts = {
        frozenset(x) for x in [
            ('topic','workflow'),('topic','prompt-reconstruction'),
            ('prompt-reconstruction','workflow'),('model-identity','agent-detectability'),
            ('prompt-token','retrieval-timing-gap'),('prompt-token','raw-cache-timing-gap'),
            ('cache-membership','retrieval-timing-gap'),('cache-membership','raw-cache-timing-gap'),
            ('retrieval-timing-gap','raw-cache-timing-gap'),
        ]
    }
    pairs, directions = [], []
    for n,(a,b) in enumerate(itertools.combinations(units,2),1):
        ai,bi = a['unit_id'],b['unit_id']
        ae,be = code['endpoints'][ai],code['endpoints'][bi]
        related = cohort_of[ai]==cohort_of[bi]
        same = a['citation_key']==b['citation_key']
        d=p=tab=tba='NOT_APPLICABLE'
        dr=pr=tr='Outside the predeclared mechanism-question subset; no comparison is asserted. This does not prove that no other question could relate these sources.'
        rule='R0_outside_scope'
        pairkey=frozenset((ai,bi))
        if pairkey in explicit:
            e=explicit[pairkey]
            d,p=e['D'],e['P']
            tab,tba=(e['T_ab'],e['T_ba']) if ai==e['a'] else (e['T_ba'],e['T_ab'])
            dr,pr,tr=e['D_reason'],e['P_reason'],e['T_reason']
            rule='R1_explicit_same_family_source_review'
        elif related:
            p='NOT_APPLICABLE'
            pr='Distinct studies do not supply the same defended test population for this cross-record paired subtraction.'
            tab=tba='UNRESOLVED'
            tr='No source-bound directional transfer bridge between these recorded conditions was established. This is not evidence of failure.'
            if any({ai,bi}<=group for group in alignments):
                d='COMPATIBLE'
                dr='Positive source-coded target/receiver-facing outcome alignment permits qualified description only. Preserve differing metric, mode, labels and populations; no numerical ranking or subtraction is licensed.'
                rule='R2_positive_semantic_alignment'
            elif 'cost-only' in (ae[3],be[3]):
                d='INCOMPATIBLE'
                dr=f'The requested same-object comparison substitutes {ae[2]} for {be[2]}. These are explicitly different cost/outcome objects. Component-wise discussion remains valid.'
                rule='R3_positive_cost_object_conflict'
            elif frozenset((ae[0],be[0])) in conflicts:
                d='INCOMPATIBLE'
                dr=f'The explicitly defined protected/measurement objects differ: {ae[2]} versus {be[2]}. They cannot be represented as one outcome, though thematic discussion is allowed.'
                rule='R4_positive_target_conflict'
            else:
                d='UNRESOLVED'
                dr='A common target/receiver-facing measurement is not positively aligned by the inspected source records. Different wording alone is not coded as incompatibility.'
                rule='R5_alignment_unverified'
        assert {d,p,tab,tba} <= VERDICTS
        pair={
            'pair_id':f'P{n:03d}','left_unit':ai,'right_unit':bi,
            'left_family':a['citation_key'],'right_family':b['citation_key'],
            'related_subset':str(related).lower(),'same_family':str(same).lower(),
            'cohort':cohort_of[ai] if related else 'NOT_APPLICABLE',
            'descriptive':d,'paired_effect':p,'transfer_left_to_right':tab,
            'transfer_right_to_left':tba,'transfer_pair':tab if tab==tba else 'DIRECTION_DEPENDENT',
            'rule':rule,'descriptive_reason':dr,'paired_effect_reason':pr,'transfer_reason':tr,
            'left_source':a['source_url'],'left_scope':a['scope'],'left_source_sha256':a['source_sha256'],
            'right_source':b['source_url'],'right_scope':b['scope'],'right_source_sha256':b['source_sha256'],
        }
        pairs.append(pair)
        for source,destination,verdict in [(ai,bi,tab),(bi,ai,tba)]:
            directions.append({'pair_id':pair['pair_id'],'source_unit':source,'destination_unit':destination,'related_subset':pair['related_subset'],'same_family':pair['same_family'],'verdict':verdict,'reason':tr,'source_scope':by_id[source]['scope'],'destination_scope':by_id[destination]['scope']})
    assert len(pairs)==528 and len(directions)==1056
    assert len({(x['left_unit'],x['right_unit']) for x in pairs})==528
    related=[r for r in pairs if r['related_subset']=='true']
    same=[r for r in pairs if r['same_family']=='true']
    assert len(related)==102 and len(same)==13
    six=[]
    for key,data in code['families'].items():
        rows=[r for r in units if r['citation_key']==key]
        assert rows and len(data['status'])==len(data['scope'])==len(data['reason'])==6
        assert set(data['status'])<=STATUS
        for i,(status,scope,reason) in enumerate(zip(data['status'],data['scope'],data['reason']),1):
            assert scope and reason
            six.append({'citation_key':key,'check':i,'check_label':CHECKS[i-1],'status':status,'reason':reason,
                'result_ids':';'.join(r['unit_id'] for r in rows),'source_scope':scope,
                'source_url':rows[0]['source_url'],'source_path':rows[0]['source_path'],'source_sha256':rows[0]['source_sha256'],
                'utility_subfield':data['utility'] if i==6 else 'NOT_APPLICABLE_TO_THIS_CELL',
                'cost_subfield':data['cost'] if i==6 else 'NOT_APPLICABLE_TO_THIS_CELL',
                'join_boundary':data['join'] if i==6 else 'NOT_APPLICABLE_TO_THIS_CELL',
                'coding_provenance':code['provenance']})
    assert len(six)==96 and len({(x['citation_key'],x['check']) for x in six})==96
    semantic=[]
    for r in units:
        e=code['endpoints'][r['unit_id']]
        semantic.append({'unit_id':r['unit_id'],'citation_key':r['citation_key'],'cohort':cohort_of[r['unit_id']],
          'target_object':e[0],'receiver':e[1],'endpoint_definition':e[2],'measurement_kind':e[3],
          'source_scope':r['scope'],'source_url':r['source_url'],'source_sha256':r['source_sha256']})
    overlays=[
      {'unit_id':'SPEC-padding-REST','field':'D1 applicability/binding','old_frozen_text':by_id['SPEC-padding-REST']['D1_defended_distribution_fit'],'new_interpretation':'Learned Random Forest attack is present; protected-fit and paired protected-test binding NR-V, not NA on a reference-matching rationale.','source_scope':'4.2;4.4;6.1','locator':'derived/wei2024speculation.txt:172-176,208-209,326-343'},
      {'unit_id':'TIME-length-instruction','field':'D1 applicability/binding','old_frozen_text':by_id['TIME-length-instruction']['D1_defended_distribution_fit'],'new_interpretation':'Input-length-conditioned attack thresholds are fitted; protected refitting/matched-test binding NR-V. Absence of an adaptation claim is distinct from an unfitted rule.','source_scope':'V-B-C;VII-B','locator':'derived/timewilltell2024.txt:264-278,296,539-540'},
      {'unit_id':'SAFE-post-trigger','field':'post-trigger window','old_frozen_text':by_id['SAFE-post-trigger']['evidence_boundary'],'new_interpretation':'Fig12/7.2.3 explicitly gives W=5s; window length resolved only. Exact sample size and historical run pairing remain unverified.','source_scope':'7.2.3 Figure12','locator':'derived/chu2025safekv.txt:455-461'},
      {'unit_id':'SAFE-post-trigger','field':'performance-cost scope','old_frozen_text':by_id['SAFE-post-trigger']['performance_cost'],'new_interpretation':'Section7.4 reports serving TTFT and throughput as separate performance experiments; not only detector-service latency and not a matched Fig12 leakage-cost point.','source_scope':'7.3-7.4','locator':'derived/chu2025safekv.txt:521-524'},
    ]
    for r in overlays:
        u=by_id[r['unit_id']]
        r.update(source_url=u['source_url'],source_sha256=u['source_sha256'],action='NEW_OVERLAY_ONLY; original frozen row unchanged')
    checks=[]
    for i,label in enumerate(CHECKS,1):
        selected=[r for r in six if r['check']==i]
        totals=Counter(r['status'] for r in selected)
        checks.append({'check':i,'label':label,**{s:totals[s] for s in ['SAT','PARTIAL','NR-R','NR-V','NA']},'total':len(selected)})
    summary={
      'audit_date':code['audit_date'],'status':'ANALYZED; deterministic coding aggregation verified; no experiment rerun',
      'unit_count':33,'family_count':22,'all_unordered_pairs':528,'related_pairs':len(related),'outside_scope_pairs':528-len(related),
      'related_cohorts':dict(Counter(r['cohort'] for r in related)),
      'same_family_pairs':13,
      'same_family_descriptive':count(same,'descriptive'),
      'same_family_paired_effect':count(same,'paired_effect'),
      'same_family_transfer_pairs':count(same,'transfer_pair'),
      'same_family_transfer_directions':count([r for r in directions if r['same_family']=='true'],'verdict'),
      'related_descriptive':count(related,'descriptive'),
      'related_paired_effect':count(related,'paired_effect'),
      'related_transfer_directions':count([r for r in directions if r['related_subset']=='true'],'verdict'),
      'evaluated_families':16,'check_cells':96,'check_distribution':checks,
      'internal_positive_paired_contrasts':['UI-delay-offline: clean/adapted comparison on protected test (6.1/Fig5)','DANGOL-capture: in-fold protected adaptive comparison (9.8-9.9)'],
      'utility_cost_examples':{'AHB':'online detectability + objective task success, execution cost unreported','DANGOL-live':'workflow recovery + live bytes/latency, objective task utility unreported','SPEC':'padding accuracy + token payload, live/wire/utility not established'},
      'overlay_count':len(overlays),
      'input_hashes':hashes_before,
      'claims_not_supported':['author error rate','independent human coding','SCOPE superiority','general defense failure rate','meta-analytic efficacy ranking','literature-wide coverage'],
    }
    source_receipts=[]
    for source in sorted({r['source_path'] for r in units}):
        candidates=[REPO/source,release/source]
        available=next((p for p in candidates if p.is_file()),None)
        expected={r['source_sha256'] for r in units if r['source_path']==source}
        assert len(expected)==1
        expected=next(iter(expected))
        observed=sha(available) if available else 'NR-A_in_this_copy'
        if available:
            assert observed==expected,(source,observed,expected)
        source_receipts.append({'source_path':source,'expected_sha256':expected,'observed_sha256':observed,'status':'MATCH' if available else 'NOT_REDISTRIBUTED; use source URL/locator'})
    assert hashes_before=={name:sha(path) for name,path in inputs.items()}
    report=[
      'Material Passport: ARS experiment-agent / validate; 2026-10-21; ANALYZED.',
      'This is deterministic aggregation of explicit AI-assisted source judgments, not new experiment data or independent researcher validation.',
      '',
      'Most informative bounded results:',
      '1. The 33 records form 13 within-family pairs. Seven permit source-qualified descriptive comparison; six concern different primitives/outcome/cost objects and cannot be represented as one measurement.',
      '2. Of the seven within-family pairs with an aligned outcome, four have positively distinct test/execution populations and three lack a matched-test/fit binding. No between-record paired subtraction is licensed. This does not negate the two already recorded internal D2 contrasts (UI delay and Dangol capture).',
      '3. The six-check inventory is claim-scoped and has no composite score. Check 6 is partial for all16 families because component, replay, or separately measured evidence does not supply every object needed by an end-to-end deployment inference; this is not a requirement imposed retroactively on each original component study.',
      '',
      'Six-check distribution (SAT/PARTIAL/NR-R/NR-V/NA):',
    ]
    report += [f"Check {r['check']}: {r['SAT']}/{r['PARTIAL']}/{r['NR-R']}/{r['NR-V']}/{r['NA']} (n=16). {r['label']}" for r in checks]
    report += [
      '',
      'All528 pairs remain in pair-inventory.csv.102 fall within the declared mechanism-question cohorts;426 are outside that comparison scope. These bins are retrospective relevance choices, not a denominator for literature prevalence or a naive-reading error rate.',
      'Transfer is directional; 1056 direction rows retain related/out-of-scope distinctions. Within-family copying is blocked for five specified pairs and unresolved for eight. An untested bridge is never coded as a demonstrated failed defense.',
      '',
      'Example A: Dangol capture/live may be described together as workflow-recovery evidence, but ~0.17/16.2x capture and ~0.30/13x bytes/11x live latency are not paired or interchangeable.',
      'Example B: Splice CTBF signal suppression and QCP-only7.5-token/<5ms cost concern different components; their co-occurrence in a paper does not create a measured combined-defense frontier.',
      '',
      'Source corrections are overlays only: Speculation uses a fitted Random Forest; TimeWillTell fits thresholds; SafeKV states W=5s and separately reports serving performance. Frozen005 rows remain byte-identical.',
      '',
      'Statistical-fallacy coverage:11/11 checked.',
      'Simpson: no pooled effect/trend; cohort and same-family counts separate.',
      'Ecological: record/family denominators explicit; no claim about authors or the whole field.',
      'Berkson/selection: purposive corpus and retrospective relevance bins disclosed; no population sampling inference.',
      'Collider: no covariate conditioning or causal estimator.',
      'Base-rate neglect: no diagnostic accuracy or reviewer-error estimate.',
      'Regression to mean: no pre/post intervention estimate.',
      'Survivorship: all33 and all528 retained; NA/unresolved do not silently disappear.',
      'Look-elsewhere: no hypothesis tests or selected significant findings.',
      'Forking paths: retrospective coding, explicit rules and alternative-status boundaries; no preregistration claim.',
      'Correlation/causation: counts do not estimate a causal effect or prove framework efficacy.',
      'Reverse causality: no directional causal inference; transfer directions encode proposed reuse only.',
      '',
      'Reproduction: audit.py --release-root <evidence-release004> --verify checks the saved derivation and input hashes without fitting or network calls. Original source texts are not redistributed; source URLs, scopes and source hashes are retained.',
    ]
    return {
      'pair-inventory.csv':encode_csv(pairs),
      'directional-transfer.csv':encode_csv(directions),
      'six-checks.csv':encode_csv(six),
      'six-check-summary.csv':encode_csv(checks),
      'semantic-coding.csv':encode_csv(semantic),
      'interpretation-overlays.csv':encode_csv(overlays),
      'source-receipts.csv':encode_csv(source_receipts),
      'summary.json':(json.dumps(summary,indent=2,ensure_ascii=False)+'\n').encode(),
      'SUMMARY.txt':('\n'.join(report)+'\n').encode(),
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--release-root',type=Path,default=DEFAULT_RELEASE)
    parser.add_argument('--verify','--check',dest='verify',action='store_true')
    args=parser.parse_args()
    outputs=derive(args.release_root.resolve())
    if args.verify:
        for name,data in outputs.items():
            # Source availability changes when only an anonymous package is distributed.
            if name=='source-receipts.csv':
                continue
            assert (HERE/name).read_bytes()==data, f'Derivation mismatch: {name}'
        manifest=json.loads((HERE/'manifest.json').read_text())
        for name,expected in manifest.items():
            assert sha(HERE/name)==expected,f'Hash mismatch: {name}'
        print('PASS: immutable inputs and deterministic saved outputs; 33 records,528 pairs,96 checklist cells; no fit/network/model calls.')
    else:
        for name,data in outputs.items():
            (HERE/name).write_bytes(data)
        names=sorted([*outputs,'audit.py','coding.json','RULES.txt','publication-text.txt'])
        manifest={name:sha(HERE/name) for name in names}
        (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        print(outputs['summary.json'].decode())

if __name__=='__main__':
    main()
