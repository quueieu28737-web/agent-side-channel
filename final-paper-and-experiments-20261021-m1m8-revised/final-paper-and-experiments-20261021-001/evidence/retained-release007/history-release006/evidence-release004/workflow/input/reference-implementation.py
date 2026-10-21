"""Offline-only SCOPE workflow study preparation. No model/network entry point.

Read existing public-artifact releases, construct controlled finite projections,
compute reference answers, prepare blind dispatches and freeze a local proposal.
This is neither a privacy experiment nor evidence that one method beats another.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]
UI = ROOT / 'experiments/uitraces_reanalysis/runtime/frames-origin-order-20261008-001'
FP = ROOT / 'evidence/field-audit-2026-09-20/fpagent-a9bdba8/feature_vectors.json'
OLD = ROOT / 'experiments/scope_efficacy_direct_20261019'
SEED = 'scope-workflow-v2-20261019'
LABELS = ('SUPPORTED', 'REFUTED', 'INSUFFICIENT')
ARMS = ('R', 'T', 'V')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(canonical(value) + b'\n')


def rank(value):
    return hashlib.sha256((SEED + ':' + value).encode()).hexdigest()


def protected_hashes():
    paths = [ROOT / 'main.tex', ROOT / 'sections/11-discussion.tex',
             ROOT / 'sections/25-scope-use-check.tex']
    paths += [ROOT / f'sections/{name}' for name in (
        '04-scope.tex', '05-llm-side-channels.tex', '06-agentic-side-channels.tex',
        '07-threat-models.tex', '08-evaluation.tex', '09-defenses.tex')]
    paths += [OLD / 'casepack-20261019-001/FREEZE.json',
              OLD / 'recovery_a1_20261019/PLAN.json',
              OLD / 'runtime/comparison-20261019-001/final.json',
              OLD / 'runtime/comparison-a1-20261019-001/analysis/result.json']
    return {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in paths}


def acquire_frames():
    """No upstream execution. Bind the consumed normalized release to its receipts."""
    release = load(UI / 'attempt-001/data-release.json')
    bindings = {
        'episodes_sha256': digest(UI / 'attempt-001/data/episodes.jsonl'),
        'inventory_sha256': digest(UI / 'attempt-001/data/inventory.json'),
        'freeze_sha256': digest(UI / 'freeze.json')}
    if release.get('status') != 'COMPLETE_READY' or any(release[k] != v for k, v in bindings.items()):
        raise ValueError('canonical_ui_release_binding_failed')
    archive = ROOT / 'evidence/field-audit-2026-09-20/uitraces-4f3df18/traces-lfs.tar.xz'
    archive_sha = digest(archive)
    if archive_sha != '79aeee6a2a7c9b32cfa0eb2a2c95663258338b33eeac1eb0117001dde5712f79':
        raise ValueError('pinned_ui_archive_changed')
    groups = defaultdict(list)
    total_rows = 0
    with (UI / 'attempt-001/data/episodes.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            total_rows += 1
            events = row['episode']['dom_trace']['events']
            values = [e.get('type', '__missing_type__') for e in events[:24]]
            if values:
                groups[row['question_hash']].append({
                    'record_id': row['id'], 'model': row['agent_id'], 'values': values,
                    'aux': [len(events), len(set(values))]})
    ui_frame = []
    for question, rows in groups.items():
        rows.sort(key=lambda r: rank(r['record_id']))
        pairs = ((a, b) for i, a in enumerate(rows) for b in rows[i + 1:]
                 if a['model'] != b['model'] and a['values'] != b['values'])
        pair = next(pairs, None)
        if pair:
            ui_frame.append({'source': 'uitraces', 'root_id': question, 'pair': pair,
                             'kind': 'archived_action_type_prefix_pair'})
    ui_frame.sort(key=lambda r: rank('ui:' + r['root_id']))
    fp_sha = digest(FP)
    if fp_sha != '9bcf15f1cce65d59cfb2ce2330e5e93a1ccd2a52d15823e4098323658b15f6a9':
        raise ValueError('pinned_fp_feature_release_changed')
    fp_groups = defaultdict(list)
    fp_rows = 0
    for family, records in load(FP).items():
        for key, values in records.items():
            meta = json.loads(key)
            fp_rows += 1
            # Value-position tokenization below retains exact supplied equality,
            # not metric distances or a re-created classifier feature space.
            row = {'record_id': hashlib.sha256(key.encode()).hexdigest(),
                   'model': family, 'values': values['behavioral'], 'aux': values['fpjs'][:16]}
            if not meta.get('source_file') or not row['values']:
                raise ValueError('missing_fp_group_or_features')
            fp_groups[meta['source_file']].append(row)
    fp_frame = []
    for key, rows in fp_groups.items():
        rows.sort(key=lambda r: rank(r['record_id']))
        pair = next(((a, b) for i, a in enumerate(rows) for b in rows[i + 1:]
                     if a['values'] != b['values']), None)
        if pair:
            fp_frame.append({'source': 'fpagent', 'root_id': key, 'pair': pair,
                             'kind': 'released_feature_block_pair_not_raw_trajectory'})
    fp_frame.sort(key=lambda r: rank('fp:' + r['root_id']))
    provenance = {
        'ui': {'repository': 'KabakaWilliam/known_actions',
               'commit': '4f3df1851e0e64dbf835344372b02d1b9593cfab',
               'url': 'https://github.com/KabakaWilliam/known_actions/tree/4f3df1851e0e64dbf835344372b02d1b9593cfab',
               'archive_sha256': archive_sha, **bindings,
               'rows': total_rows, 'nonempty_question_groups': len(groups),
               'eligible_distinct_model_and_prefix_pairs': len(ui_frame)},
        'fp': {'repository': 'ethanbwang/fp-agent',
               'commit': 'a9bdba8701ec0447e98462e95780ea3b0beefd6a',
               'url': 'https://github.com/ethanbwang/fp-agent/tree/a9bdba8701ec0447e98462e95780ea3b0beefd6a',
               'feature_file_sha256': fp_sha, 'rows': fp_rows,
               'source_file_groups': len(fp_groups), 'eligible_groups': len(fp_frame),
               'source_file_is_person_or_host_identity': False,
               'original_paper_result_binding': 'UNVERIFIED_NOT_NEEDED_FOR_THIS_FINITE_TASK'},
        'new_source_repositories_disjoint_from_old_six': True,
        'new_blinded_model_calls': 0, 'source_pretraining_exposure': 'UNKNOWN',
        'independent_curator_or_researcher': False,
        'redistribution_rights_for_raw_sources_certified': False,
        'upstream_code_executed': False,
        'ui_archive_ingestion': 'read existing fully bound canonical release; no old analysis rerun',
        'semantic_task_or_person_holdout_certified': False}
    old_sources = {x['repository'] for x in load(OLD / 'casepack-20261019-001/private/provenance.json')['sources']}
    if old_sources & {provenance['ui']['repository'], provenance['fp']['repository']}:
        raise ValueError('source_repository_overlap_with_old_model_battery')
    return ui_frame, fp_frame, provenance


def source_tokens(frame):
    # Bijection over the observed (field-position,value) tokens in this pair.
    # The UI sequence uses action categories without position; FP uses positions.
    atoms = []
    raw = []
    for row in frame['pair']:
        values = [canonical(('action', x) if frame['source'] == 'uitraces'
                            else ('feature', i, x)).decode() for i, x in enumerate(row['values'])]
        aux = [canonical(('aux', i, x)).decode() for i, x in enumerate(row['aux'])]
        atoms += values + aux
        raw.append((values, aux))
    unique = sorted(set(atoms), key=lambda a: rank(frame['root_id'] + a))
    lookup = {a: i + 1 for i, a in enumerate(unique)}
    return [([lookup[x] for x in values], [lookup[x] for x in aux]) for values, aux in raw]


def case_from_frame(frame, index, partition):
    rng = random.Random(rank('case:' + frame['source'] + ':' + frame['root_id']))
    signals = source_tokens(frame)
    cid = 'W' + rank(frame['source'] + ':' + frame['root_id'])[:14]
    ids = ['n' + rank(cid + ':' + str(i))[:9] for i in range(11)]
    nodes = [
        {'id': ids[0], 'input': 'signal_0'},
        {'id': ids[1], 'input': 'signal_1'},
        {'id': ids[2], 'op': 'reverse', 'parents': [ids[0]]},
        {'id': ids[3], 'op': 'reverse', 'parents': [ids[2]]},
        {'id': ids[4], 'op': ('empty' if index % 2 else 'count'), 'parents': [ids[0]]},
        {'id': ids[5], 'op': 'concat', 'parents': [ids[4], ids[1]]},
        {'id': ids[6], 'op': 'empty', 'parents': [ids[5]]},
        {'id': ids[7], 'op': {'variable': 'u_transform'}, 'parents': [ids[3]]},
        {'id': ids[8], 'op': ('sort' if index % 2 else 'histogram'), 'parents': [ids[3]]},
        {'id': ids[9], 'op': 'concat', 'parents': [ids[6], ids[8]]},
        {'id': ids[10], 'op': 'copy', 'parents': [ids[7]]}]
    mode = index % 8
    # Topology/intervention schedule is fixed before any model responses.
    # Unknown variables can be irrelevant; a known counterexample need not be
    # converted to uncertainty just because some other field is missing.
    options = [
        [(ids[6], True)], [(ids[3], True)], [(ids[10], True)],
        [(ids[8], True)], [(ids[9], True), (ids[0], 'u_permission')],
        [(ids[3], True), (ids[10], 'u_permission')],
        [(ids[6], 'u_permission')], [(ids[4], True), (ids[1], False)]]
    choices = [(mode + offset) % len(options) for offset in (0, 3, 5)]
    queries = []
    for j, choice in enumerate(choices):
        queries.append({'id': 'q' + rank(cid + ':q:' + str(j))[:8],
                        'receiver': 'receiver_' + str(j),
                        'slots': [{'node': node, 'access': access} for node, access in options[choice]],
                        'claim': 'The supplied left/right states have identical final released views for this receiver in the actual configuration.'})
    rng.shuffle(nodes)
    rng.shuffle(queries)
    case = {'case_id': cid, 'evidence': {
        'signal_0': {'left': signals[0][0], 'right': signals[1][0]},
        'signal_1': {'left': signals[0][1], 'right': signals[1][1]}},
        'nodes': nodes,
        'configuration_domains': {'u_transform': ['copy', 'empty'], 'u_permission': [False, True]},
        'queries': queries,
        'source_boundary': 'Opaque equality-preserving tokens from a supplied public-artifact pair; the flow graph, recipients and interventions are researcher-created, not original-paper executions.'}
    binding = {'case_id': cid, 'source': frame['source'], 'partition': partition,
               'root_id': frame['root_id'], 'kind': frame['kind'],
               'source_record_ids': [r['record_id'] for r in frame['pair']],
               'source_pair_sha256': hashlib.sha256(canonical(frame['pair'])).hexdigest(),
               'mode': mode, 'same_root_counted_once': True}
    return case, binding


def run_op(op, values):
    flat = [item for row in values for item in row]
    if op in ('copy', 'concat'):
        return flat
    if op == 'reverse':
        return flat[::-1]
    if op == 'sort':
        return sorted(flat)
    if op == 'count':
        return [len(flat)]
    if op == 'empty':
        return []
    if op == 'histogram':
        counts = Counter(flat)
        return [item for key in sorted(counts) for item in (key, counts[key])]
    raise ValueError('unknown_operation')


def world_views(case, world):
    nodes = {n['id']: n for n in case['nodes']}
    if len(nodes) != len(case['nodes']):
        raise ValueError('duplicate_node')
    views = {q['id']: [] for q in case['queries']}
    for side in ('left', 'right'):
        memo, active = {}, set()

        def evaluate(key):
            if key in memo:
                return memo[key]
            if key in active or key not in nodes:
                raise ValueError('cycle_or_missing_parent')
            active.add(key)
            node = nodes[key]
            if 'input' in node:
                result = case['evidence'][node['input']][side]
            else:
                op = node['op']
                if isinstance(op, dict):
                    op = world[op['variable']]
                result = run_op(op, [evaluate(p) for p in node['parents']])
            active.remove(key)
            memo[key] = result
            return result

        for q in case['queries']:
            output = []
            for slot in q['slots']:
                access = slot['access']
                if isinstance(access, str):
                    access = world[access]
                output.append(evaluate(slot['node']) if access else None)
            views[q['id']].append(output)
    return {key: pair[0] == pair[1] for key, pair in views.items()}


def reference(case):
    domains = case['configuration_domains']
    keys = sorted(domains)
    worlds = [dict(zip(keys, values)) for values in itertools.product(*(domains[k] for k in keys))]
    counts = Counter()
    for world in worlds:
        counts.update({key: int(value) for key, value in world_views(case, world).items()})
    answers = []
    for query in case['queries']:
        equal = counts[query['id']]
        label = 'SUPPORTED' if equal == len(worlds) else ('REFUTED' if equal == 0 else 'INSUFFICIENT')
        answers.append({'query_id': query['id'], 'decision': label,
                        'equal_worlds': equal, 'possible_worlds': len(worlds),
                        'required_evidence_ids': sorted([query['id'], 'signal_0', 'signal_1'])})
    return {'case_id': case['case_id'], 'answers': answers}


def grade(case, prediction):
    """No method/terminology points and no model adjudicator."""
    if not isinstance(prediction, dict) or set(prediction) != {'case_id', 'answers'} or prediction['case_id'] != case['case_id']:
        return {'score': 0.0, 'content_valid': False, 'reason': 'schema_or_case_id'}
    answers = prediction['answers']
    truth = reference(case)['answers']
    if not isinstance(answers, list) or len(answers) != len(truth) or any(not isinstance(x, dict) for x in answers):
        return {'score': 0.0, 'content_valid': False, 'reason': 'coverage'}
    lookup = {x.get('query_id'): x for x in answers}
    if set(lookup) != {x['query_id'] for x in truth} or len(lookup) != len(answers):
        return {'score': 0.0, 'content_valid': False, 'reason': 'duplicate_or_missing_query'}
    correct = []
    for expected in truth:
        row = lookup[expected['query_id']]
        ok_schema = set(row) == {'query_id', 'decision', 'equal_worlds', 'possible_worlds', 'evidence_ids'}
        ids = row.get('evidence_ids')
        ok_schema &= (isinstance(ids, list) and all(isinstance(x, str) for x in ids)
                      and len(ids) == len(set(ids)) and set(ids) == set(expected['required_evidence_ids']))
        ok_schema &= all(type(row.get(k)) is int for k in ('equal_worlds', 'possible_worlds'))
        correct.append(bool(ok_schema and all(row.get(k) == expected[k]
                            for k in ('decision', 'equal_worlds', 'possible_worlds'))))
    return {'score': sum(correct) / len(correct), 'content_valid': True, 'query_correct': correct}


def power_bound(n, delta, alpha=.05):
    margin = math.sqrt(2 * math.log(2 / alpha) / n)
    power = max(0.0, 1 - math.exp(-n * (delta - margin) ** 2 / 2)) if delta > margin else 0.0
    return {'n_root_blocks': n, 'true_effect_assumed': delta, 'interval_half_width': margin,
            'guaranteed_power_lower_bound': power,
            'assumptions': 'fixed bounded slot potential outcomes, independent within-root permutations, no cross-request interference'}


def power_grid():
    deltas = [.05, .10, .15, .20, .25, .30]
    result = []
    for delta in deltas:
        required = math.ceil(2 * (math.sqrt(math.log(40)) + math.sqrt(math.log(5))) ** 2 / delta ** 2)
        result.append({'delta': delta, 'root_blocks_for_80_percent_bound': required,
                       'three_arm_requests': required * 3,
                       'generation_wait_hours_at_60s': required * 3 / 60,
                       'slot_budget_hours_at_180s': required * 3 / 20})
    return {'status': 'DESIGN_CALCULATION_NOT_OBSERVED_METHOD_EFFECT', 'alpha': .05,
            'target_power_lower_bound': .80, 'formula': 'ceil(2*(sqrt(log(40))+sqrt(log(5)))^2/delta^2)',
            'planning_grid': result,
            'fixed_512_main_block_scenarios': [power_bound(512, d) for d in deltas],
            'repeated_queries_per_root_increase_n': False,
            'precision_not_certified_for_10pp_effect': True,
            'fp_transfer_only': {'n': 18, 'standalone_80_percent_10pp_claim': False}}


def contrast_bounds(primary_ids, records, alpha=.05):
    """Prespecified full-denominator V-minus-T bounds; missing is never zero.

    records maps each scheduled root to T/V score in [0,1] or None. A caller
    must first enforce clean engineering admission. No p-value or service-state
    independence certificate is produced by this pure arithmetic function.
    """
    if not primary_ids or len(set(primary_ids)) != len(primary_ids) or set(records) != set(primary_ids):
        raise ValueError('fixed_primary_denominator_required')
    lower, upper, missing = [], [], 0
    for key in primary_ids:
        if set(records[key]) != {'T', 'V'}:
            raise ValueError('primary_arms_required')
        values = records[key]
        for score in values.values():
            if score is not None and (type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1):
                raise ValueError('invalid_root_score')
            missing += score is None
        t, v = values['T'], values['V']
        lower.append((0 if v is None else v) - (1 if t is None else t))
        upper.append((1 if v is None else v) - (0 if t is None else t))
    n = len(primary_ids)
    lo, hi = sum(lower) / n, sum(upper) / n
    margin = math.sqrt(2 * math.log(2 / alpha) / n)
    return {'root_blocks': n, 'missing_arm_outcomes': missing,
            'effect_lower': lo, 'effect_upper': hi,
            'conditional_envelope_lower': max(-1, lo - margin),
            'conditional_envelope_upper': min(1, hi + margin),
            'half_width': margin, 'original_primary_complete': missing == 0,
            'missing_imputed_as_observed': False,
            'confirmatory_p_value': None,
            'scope': 'conditional finite battery; fixed slot outcomes/independent permutations/no interference required'}


def build(out):
    out = Path(out).resolve()
    if STUDY not in out.parents:
        raise ValueError('new_pack_must_be_under_this_study')
    out.mkdir(exist_ok=False)
    before = protected_hashes()
    ui, fp, provenance = acquire_frames()
    if len(ui) < 16 + 512 or len(fp) < 1:
        raise ValueError('insufficient_eligible_source_units_no_substitution')
    cases, bindings = [], []
    for partition, frame in [('development', ui[:16]), ('primary_test', ui[16:528]), ('source_transfer', fp)]:
        for index, item in enumerate(frame):
            case, binding = case_from_frame(item, index, partition)
            cases.append(case)
            bindings.append(binding)
    cases.sort(key=lambda c: rank(c['case_id']))
    save(out / 'public/cases.json', cases)
    save(out / 'private/source-bindings.json', bindings)
    save(out / 'private/reference.json', [reference(c) for c in cases])
    save(out / 'private/source-provenance.json', provenance)
    save(out / 'private/frame-accounting.json', {
        'ui_eligible': len(ui), 'ui_development': 16, 'ui_primary_test': 512,
        'ui_unused_reserve_not_replacement_pool': len(ui) - 528,
        'fp_source_transfer': len(fp), 'primary_source_population_claim': False,
        'root_block': 'exact UI question hash; FP source_file proxy separately',
        'near_duplicate_semantic_holdout': 'NOT_CERTIFIED',
        'old_case_repository_overlap': 0, 'raw_source_upload_allowed': False})
    partitions = {b['case_id']: b['partition'] for b in bindings}
    schedule = []
    # Formal requests cover held-out primary and source-transfer roots only.
    allocation_rng = random.SystemRandom()
    for case in sorted(cases, key=lambda c: rank('order:' + c['case_id'])):
        if partitions[case['case_id']] == 'development':
            continue
        arms = list(ARMS)
        allocation_rng.shuffle(arms)
        schedule += [{'case_id': case['case_id'], 'arm': arm, 'partition': partitions[case['case_id']]} for arm in arms]
    save(out / 'private/dispatch-schedule.json', schedule)
    save(out / 'private/arm-key.json', {'R': 'complete_flat_checklist',
        'T': 'complete_generic_structured_workflow', 'V': 'scope_relational_workflow'})
    save(out / 'private/protected-before.json', before)
    save(out / 'power.json', power_grid())
    counts = Counter(a['decision'] for c in cases if partitions[c['case_id']] == 'primary_test'
                     for a in reference(c)['answers'])
    save(out / 'BUILD.json', {'status': 'OFFLINE_CASEPACK_PREPARED_NOT_RUN',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'cases': len(cases),
        'primary_roots': 512, 'source_transfer_roots': len(fp), 'development_roots': 16,
        'queries_per_root': 3, 'primary_query_label_counts': dict(counts),
        'formal_requests_proposed_not_authorized': len(schedule),
        'model_calls': 0, 'learned_attacker_fits': 0, 'protected_files_unchanged': before == protected_hashes()})
    if before != protected_hashes():
        raise ValueError('protected_files_changed_during_build')
    print(json.dumps(load(out / 'BUILD.json')))


def check_pack(pack):
    pack = Path(pack)
    cases = load(pack / 'public/cases.json')
    refs = load(pack / 'private/reference.json')
    if refs != [reference(c) for c in cases]:
        raise ValueError('reference_mismatch')
    if len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('duplicate_case')
    bindings = load(pack / 'private/source-bindings.json')
    for source in ('uitraces', 'fpagent'):
        rows = [b for b in bindings if b['source'] == source]
        if len({b['root_id'] for b in rows}) != len(rows):
            raise ValueError('repeated_source_root')
    operation_ids = [f'K{i:02d}' for i in range(1, 11)]
    cards = {a: (STUDY / f'cards/{a}.txt').read_text(encoding='utf-8') for a in ARMS}
    for card in cards.values():
        if any(card.count(k) != 1 for k in operation_ids):
            raise ValueError('missing_or_duplicated_common_operation')
    words = {a: len(card.split()) for a, card in cards.items()}
    if max(words.values()) / min(words.values()) > 1.10:
        raise ValueError('method_card_word_budget_diff_over_10_percent')
    payload_sizes = [len(canonical(c)) + max(len(c.encode()) for c in cards.values())
                     + (STUDY / 'COMMON.txt').stat().st_size for c in cases]
    if max(payload_sizes) > 32768:
        raise ValueError('input_byte_boundary')
    schedule = load(pack / 'private/dispatch-schedule.json')
    if len(schedule) != (len(cases) - 16) * 3:
        raise ValueError('schedule_coverage')
    expected = {(b['case_id'], a) for b in bindings if b['partition'] != 'development' for a in ARMS}
    if {(s['case_id'], s['arm']) for s in schedule} != expected or len(expected) != len(schedule):
        raise ValueError('duplicate_or_missing_dispatch')
    before = load(pack / 'private/protected-before.json')
    current = protected_hashes()
    changed = [key for key in before if before[key] != current[key]]
    # main.tex is a read-only, non-input manuscript watcher in this side chat.
    # Preserve concurrent edits rather than blocking or overwriting the parent.
    # All actual source inputs have separate strict pinned-hash checks above.
    # Baseline sections and old experiment records still fail closed on change.
    if any(key != 'main.tex' for key in changed):
        raise ValueError('protected_baseline_or_old_run_files_changed')
    return {'status': 'OFFLINE_MECHANICAL_VALIDATION_PASS_NOT_EFFICACY',
            'model_calls': 0, 'cases': len(cases), 'method_card_words': words,
            'maximum_input_bytes': max(payload_sizes), 'reference_recalculation': True,
            'schedule_unique_and_complete': True,
            'protected_baseline_and_old_run_files_unchanged': True,
            'concurrent_noninput_main_change_detected': 'main.tex' in changed,
            'noninput_main_hash_at_build': before['main.tex'],
            'noninput_main_hash_at_check': current['main.tex']}


def freeze(pack):
    pack = Path(pack).resolve()
    validation = check_pack(pack)
    check = load(pack / 'reference-js-check.json')
    if check.get('status') != 'MATCH_ALL_PUBLIC_CASE_REFERENCES' or check.get('cases') != validation['cases']:
        raise ValueError('separate_code_path_reference_not_checked')
    files = [p for p in pack.rglob('*') if p.is_file() and p.name != 'FREEZE.json']
    source = [p for p in STUDY.rglob('*') if p.is_file() and pack not in p.parents
              and 'casepack-' not in str(p.relative_to(STUDY))
              and p.suffix in ('.py', '.js', '.txt', '.md', '.json')]
    # Explicit immutable preparation-source list; no future run output included.
    source = [p for p in source if p.parent == STUDY or p.parent == STUDY / 'cards']
    save(pack / 'FREEZE.json', {'status': 'LOCAL_OFFLINE_FREEZE_NOT_EXECUTION_APPROVAL',
        'files': {str(p.relative_to(STUDY)).replace('\\', '/'): digest(p) for p in sorted(files + source)},
        'model_execution_authorized': False,
        'proposal_requires_effect_target_budget_and_transport_acceptance': True})
    print(json.dumps({'status': 'LOCAL_OFFLINE_FREEZE_COMPLETE', 'sha256': digest(pack / 'FREEZE.json')}))


def verify(pack):
    record = load(Path(pack) / 'FREEZE.json')
    bad = [key for key, value in record['files'].items() if digest(STUDY / key) != value]
    if bad:
        raise ValueError('frozen_files_changed:' + ','.join(bad))
    return {'status': 'FROZEN_PREPARATION_BINDINGS_MATCH_NO_MODEL_CALLS', 'files': len(record['files'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'check', 'freeze', 'verify', 'power'])
    parser.add_argument('--pack', type=Path)
    args = parser.parse_args()
    if args.mode == 'power':
        print(json.dumps(power_grid()))
    elif args.pack is None:
        parser.error('--pack required')
    elif args.mode == 'build':
        build(args.pack)
    elif args.mode == 'check':
        print(json.dumps(check_pack(args.pack)))
    elif args.mode == 'freeze':
        freeze(args.pack)
    else:
        print(json.dumps(verify(args.pack)))
