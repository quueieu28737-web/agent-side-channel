"""Derive replay inputs from closed, verified collection; no model execution."""
import argparse
import json
from pathlib import Path
import run_study as study


def export(pack, run, out):
    study.verify(pack)
    final = json.loads((run/'final.json').read_text())
    supervision = json.loads((run/'supervision.json').read_text())
    if final['status'] != 'COLLECTION_COMPLETE' or not study.lc.owned.control_ok(supervision):
        raise ValueError('complete_collection_and_owned_cleanup_required')
    requests = json.loads((pack/'requests.json').read_text())
    meta = {r['id']: r for r in json.loads((pack/'e1-metadata.json').read_text())}
    e1, plans, provenance = [], {}, []
    for req in requests:
        folder = run/'requests'/req['id']
        result = json.loads((folder/'response.json').read_text())
        if result['status'] not in ('COMPLETE', 'CONTENT_FAILURE'):
            raise ValueError('unclosed_model_response')
        raw_path = folder/'final-answer.raw.txt'
        raw = raw_path.read_text(encoding='utf-8')
        provenance.append({'id': req['id'], 'raw_final_sha256': study.digest(raw_path),
                           'response_sha256': study.digest(folder/'response.json'),
                           'thread_id': result.get('thread_id'), 'turn_id': result.get('turn_id'),
                           'usage': result['token_usage']})
        if req['experiment'] == 'E1':
            value = result['prediction']
            ok = result['status'] == 'COMPLETE' and isinstance(value, dict) and set(value) == {'text'} and isinstance(value['text'], str)
            e1.append({**meta[req['id']], 'text': value['text'] if ok else '',
                       'status': 'ok' if ok else 'model_content_failure'})
        else:
            plans[req['id']] = raw
    out.mkdir(parents=True, exist_ok=False)
    with (out/'e1.jsonl').open('x', encoding='utf-8') as stream:
        for row in sorted(e1, key=lambda r:r['id']):
            stream.write(json.dumps(row, ensure_ascii=False)+'\n')
    study.save(out/'e2-plans.json', plans)
    study.save(out/'raw-binding.json', {'collection_sha256': study.digest(run/'final.json'),
                'supervision_sha256': study.digest(run/'supervision.json'), 'records': provenance,
                'e1': len(e1), 'e2': len(plans), 'new_model_calls': 0})
    print(json.dumps({'status':'EXPORTED', 'e1':len(e1), 'e2':len(plans), 'out':str(out)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    export(args.pack.resolve(), args.run.resolve(), args.out.resolve())
