"""Finite controller: prepare -> no-generation preflight -> frozen collection."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import luna_client as lc

HERE = Path(__file__).resolve().parent
TOPICS = [
 'tidal power', 'urban trees', 'heat pumps', 'solar batteries', 'water filtration',
 'public libraries', 'rail signaling', 'composting', 'rain gardens', 'bicycle gears',
 'wildfire prevention', 'wetland restoration', 'data backups', 'food refrigeration',
 'soil erosion', 'bridge inspections', 'community gardens', 'acoustic insulation',
 'recycling glass', 'weather forecasting', 'electric motors', 'drip irrigation',
 'building ventilation', 'coastal dunes']
TEXT_SCHEMA = {'type': 'object', 'properties': {'text': {'type': 'string'}},
               'required': ['text'], 'additionalProperties': False}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    lc.tr.save(path, value)


def append(path, value):
    with Path(path).open('ab') as stream:
        stream.write(lc.tr.encoded(value)+b'\n')
        stream.flush()
        import os
        os.fsync(stream.fileno())


def prepare(out):
    import cover
    out.mkdir(parents=True, exist_ok=False)
    order = list(range(24))
    random.Random(20261021).shuffle(order)
    train = set(order[:12])
    requests, metadata = [], []
    for n, topic in enumerate(TOPICS):
        for label in (0, 1):
            ident = f'E1-{n:02d}-{label}'
            length = ('one concise sentence of 12 to 24 words' if label == 0 else
                      'six explanatory sentences totaling 150 to 190 words')
            prompt = (f'Explain {topic} for a general reader. Write {length}. '
                      'Use ordinary factual prose, without headings, list markup, citations or tool calls. '
                      'Return JSON with the single field text containing the explanation.')
            requests.append({'id': ident, 'experiment': 'E1', 'prompt': prompt, 'schema': TEXT_SCHEMA})
            metadata.append({'id': ident, 'group_id': f'topic-{n:02d}', 'topic': topic,
                             'label': label, 'split': 'train' if n in train else 'test'})
    tasks = cover.generate_tasks()
    for task in tasks:
        req = cover.model_request(task)
        requests.append({'id': task['task_id'], 'experiment': 'E2', 'prompt': req['prompt'], 'schema': req['response_schema']})
    random.Random(20261022).shuffle(requests)
    save(out/'e1-metadata.json', metadata)
    save(out/'e2-tasks.json', tasks)
    save(out/'requests.json', requests)
    sources = [p for p in HERE.glob('*.py')] + [HERE/'PROTOCOL.md']
    sources += [Path(x.__file__).resolve() for x in (lc, lc.prior, lc.prior.compatible, lc.prior.core,
                lc.prior.old_transport, lc.tr, lc.prior.core.watchdog, lc.owned, lc.owned.prior, lc.owned.prior.identity)]
    sources += [PRIOR_FILE for PRIOR_FILE in [lc.PRIOR/'dependencies.py']]
    unique = sorted(set(sources))
    bindings = {str(p): digest(p) for p in unique}
    save(out/'freeze.json', {'utc': lc.stamp(), 'model': lc.MODEL, 'effort': lc.EFFORT,
         'requests': len(requests), 'e1': 48, 'e2': len(tasks), 'admission_cap': 72,
         'sources_sha256': bindings, 'requests_sha256': digest(out/'requests.json'),
         'metadata_sha256': digest(out/'e1-metadata.json'), 'tasks_sha256': digest(out/'e2-tasks.json'),
         'provider_internal_retries': 'NR', 'wall_budget_s': 5400})
    print(json.dumps({'status': 'PREPARED', 'requests': len(requests), 'out': str(out)}))


def verify(pack):
    f = json.loads((pack/'freeze.json').read_text())
    if any(digest(p) != h for p, h in f['sources_sha256'].items()):
        raise ValueError('frozen_source_changed')
    if (digest(pack/'requests.json') != f['requests_sha256'] or
        digest(pack/'e1-metadata.json') != f['metadata_sha256'] or
        digest(pack/'e2-tasks.json') != f['tasks_sha256']):
        raise ValueError('frozen_inputs_changed')
    return f


def worker(mode, out, pack=None):
    gate = lc.prior.core.watchdog.gate()
    deadline = gate['work_deadline']
    if mode == 'preflight':
        r = lc.preflight(out/'interface', deadline)
        return r['status'] == 'NO_GENERATION_PREFLIGHT_PASS'
    f = verify(pack)
    requests = json.loads((pack/'requests.json').read_text())
    r = {'status': 'COLLECTING', 'started': 0, 'completed': 0, 'content_failures': 0,
         'admissions': 0, 'observed_tokens': 0, 'unknown_usage': 0, 'started_utc': lc.stamp()}
    try:
        for req in requests:
            verify(pack)
            if time.monotonic()+180 > deadline or r['admissions'] >= f['admission_cap']:
                r.update(status='BUDGET_STOP')
                break
            append(out/'budget-ledger.jsonl', {'event': 'DISPATCH_INTENT', 'id': req['id'], 'utc': lc.stamp()})
            r['started'] += 1
            result = lc.one_request(req, out/'requests'/req['id'], deadline)
            r['admissions'] += result['application_admissions']
            usage = result['token_usage']
            if isinstance(usage, dict) and isinstance(usage.get('last', {}).get('totalTokens'), int):
                r['observed_tokens'] += usage['last']['totalTokens']
            elif result['application_admissions']:
                r['unknown_usage'] += 1
            if result['status'] == 'COMPLETE':
                r['completed'] += 1
            elif result['status'] == 'CONTENT_FAILURE':
                r['content_failures'] += 1
            else:
                r.update(status='HOLD', stopped_id=req['id'], error=result.get('error', result.get('close_error')))
            append(out/'budget-ledger.jsonl', {'event': 'CLOSED', 'id': req['id'], 'status': result['status'],
                'admissions': result['application_admissions'], 'usage': usage, 'utc': lc.stamp()})
            append(out/'progress.jsonl', r)
            print(json.dumps({k:r[k] for k in ('status','started','completed','admissions','observed_tokens')}), flush=True)
            if r['status'] == 'HOLD':
                break
        else:
            r['status'] = 'COLLECTION_COMPLETE'
    except BaseException as exc:
        r.update(status='HOLD', error=repr(exc))
    r['finished_utc'] = lc.stamp()
    save(out/'final.json', r)
    return r['status'] == 'COLLECTION_COMPLETE'


def run(mode, out, pack):
    out.mkdir(parents=True, exist_ok=False)
    budget = 180 if mode == 'preflight' else 5400
    if mode != 'preflight':
        freeze = verify(pack)
    argv = [sys.executable, '-B', str(Path(__file__).resolve()), '__worker', '--mode', mode, '--out', str(out)]
    if pack:
        argv += ['--pack', str(pack)]
    save(out/'launch.json', {'utc': lc.stamp(), 'mode': mode, 'argv': argv, 'budget_s': budget,
                           'freeze_sha256': digest(pack/'freeze.json') if pack else None,
                           'model': lc.MODEL, 'effort': lc.EFFORT})
    supervision = lc.owned.run_owned(argv, out, budget_s=budget, cleanup_reserve_s=30)
    save(out/'supervision.json', supervision)
    print(json.dumps({'out': str(out), 'status': supervision['status'], 'reap_confirmed': supervision['reap_confirmed']}))
    return lc.owned.control_ok(supervision)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare','preflight','collect','__worker'])
    parser.add_argument('--mode', choices=['preflight','collect'])
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute-approved', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.out.resolve())
    elif args.command == '__worker':
        sys.exit(0 if worker(args.mode, args.out.resolve(), args.pack.resolve() if args.pack else None) else 2)
    else:
        if not args.execute_approved:
            raise ValueError('execute-approved_required')
        sys.exit(0 if run(args.command, args.out.resolve(), args.pack.resolve() if args.pack else None) else 2)
