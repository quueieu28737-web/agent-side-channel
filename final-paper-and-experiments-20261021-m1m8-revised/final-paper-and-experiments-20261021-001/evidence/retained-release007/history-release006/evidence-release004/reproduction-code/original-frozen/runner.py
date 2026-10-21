"""Freeze and supervise one local public-artifact analysis; no model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
FILES = ('README.md', 'PROTOCOL.md', 'PLAN.json', 'ENGINEERING-TESTS.json', 'features.py', 'ingest.py', 'analyze.py',
         'runner.py', 'test_features.py', 'test_ingest.py', 'test_analyze.py', 'test_runner.py')


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value, exclusive=True):
    with Path(path).open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def protected(root):
    paths = [root / 'main.tex', root / 'refs.bib']
    for directory in ('sections', 'tables', 'figures'):
        paths.extend(sorted((root / directory).glob('*.tex')))
    paths.append(root / 'experiments/native_goal_luna_measurement/deliverables/luna-fresh27-A3-20261001-001/empirical-results.tex')
    return {str(path.relative_to(root)).replace('\\', '/'): digest(path) for path in paths}


def check_sources(plan, root):
    for key in ('archive', 'split_record'):
        path = (root / plan[key]).resolve()
        if root not in path.parents or path.is_symlink() or not path.is_file():
            raise ValueError('unsafe_or_missing_input:' + key)
        expected = plan['archive_sha256' if key == 'archive' else 'split_sha256']
        if digest(path) != expected:
            raise ValueError('input_hash_mismatch:' + key)


def prepare(root, out):
    root = Path(root).resolve()
    out = Path(out).resolve()
    if root not in out.parents:
        raise ValueError('pack_outside_workspace')
    plan = read(HERE / 'PLAN.json')
    check_sources(plan, root)
    for name in FILES:
        if not (HERE / name).is_file():
            raise ValueError('missing_snapshot_source:' + name)
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / 'snapshot'
    snapshot.mkdir()
    for name in FILES:
        shutil.copyfile(HERE / name, snapshot / name)
    freeze = {'schema': 'uitraces-frozen-reanalysis-v1', 'created_utc': now(),
              'workspace': str(root), 'source_commit': plan['source_commit'],
              'snapshot_sha256': {name: digest(snapshot / name) for name in FILES},
              'input_sha256': {plan['archive']: plan['archive_sha256'], plan['split_record']: plan['split_sha256']},
              'protected_sha256': protected(root), 'model_requests': 0,
              'prior_source_and_published_results_known': True,
              'not_blind_preregistration': True}
    save(out / 'freeze.json', freeze)
    with (out / 'seal.sha256').open('x', encoding='ascii') as stream:
        stream.write(digest(out / 'freeze.json') + '\n')
    return {'status': 'FROZEN_BEFORE_THIS_REANALYSIS', 'pack': str(out), 'freeze_sha256': digest(out / 'freeze.json')}


def verify(pack):
    pack = Path(pack).resolve()
    freeze = read(pack / 'freeze.json')
    if digest(pack / 'freeze.json') != (pack / 'seal.sha256').read_text(encoding='ascii').strip():
        raise ValueError('changed_freeze')
    for name, value in freeze['snapshot_sha256'].items():
        if digest(pack / 'snapshot' / name) != value:
            raise ValueError('changed_snapshot:' + name)
    root = Path(freeze['workspace']).resolve()
    plan = read(pack / 'snapshot/PLAN.json')
    check_sources(plan, root)
    if protected(root) != freeze['protected_sha256']:
        raise ValueError('changed_protected_manuscript')
    return plan, root


def capture_release(pack, consume_rows=False):
    """Bind the exact byte stream consumed, not just a preceding pathname check."""
    pack = Path(pack)
    attempt = pack / 'attempt-001'
    release_bytes = (attempt / 'data-release.json').read_bytes()
    inventory_bytes = (attempt / 'data/inventory.json').read_bytes()
    release = json.loads(release_bytes.decode('utf-8'))
    inventory = json.loads(inventory_bytes.decode('utf-8'))
    rows = []
    consumed = hashlib.sha256()
    with (attempt / 'data/episodes.jsonl').open('rb') as stream:
        for line in stream:
            consumed.update(line)
            if consume_rows and line.strip():
                rows.append(json.loads(line.decode('utf-8')))
    bindings = {
        'data_release_sha256': hashlib.sha256(release_bytes).hexdigest(),
        'inventory_sha256': hashlib.sha256(inventory_bytes).hexdigest(),
        'episodes_sha256': consumed.hexdigest(),
        'freeze_sha256': digest(pack / 'freeze.json')}
    if (release.get('status') != 'COMPLETE_READY'
            or inventory.get('status') != 'COMPLETE_READY'
            or any(release.get(key) != bindings[key]
                   for key in ('inventory_sha256', 'episodes_sha256', 'freeze_sha256'))):
        raise ValueError('changed_or_incomplete_canonical_episode_release')
    return rows, bindings


def require_analysis_complete(result):
    if not isinstance(result, dict) or result.get('status') != 'complete':
        raise ValueError('analysis_did_not_declare_completion')


def verify_outputs(pack):
    pack = Path(pack)
    attempt = pack / 'attempt-001'
    _, current = capture_release(pack)
    binding = read(attempt / 'analysis-output-bindings.json')
    if binding['input_bindings'] != current:
        raise ValueError('changed_analysis_input_release')
    files = {path.name: digest(path) for path in sorted((attempt / 'analysis').iterdir())
             if path.is_file()}
    if files != binding['files']:
        raise ValueError('changed_analysis_output')
    require_analysis_complete(read(attempt / 'analysis/summary.json'))


def stage(pack, name):
    pack = Path(pack).resolve()
    plan, root = verify(pack)
    attempt = pack / 'attempt-001'
    if name == 'ingest':
        from ingest import ingest
        result = ingest(root / plan['archive'], root / plan['split_record'], attempt / 'data',
                        limits=plan['ingest_limits'])
        save(attempt / 'data-release.json', {'status': result['status'],
             'inventory_sha256': digest(attempt / 'data/inventory.json'),
             'episodes_sha256': digest(attempt / 'data/episodes.jsonl'),
             'freeze_sha256': digest(pack / 'freeze.json'),
             'created_utc': now()})
        print(json.dumps({'status': result['status'], 'stage': name}, ensure_ascii=False), flush=True)
        return 0 if result['status'] == 'COMPLETE_READY' else 2
    if name == 'analysis':
        import numpy
        import scipy
        import sklearn
        environment = {'python': sys.version.split()[0], 'numpy': numpy.__version__,
                       'scipy': scipy.__version__, 'sklearn': sklearn.__version__}
        if environment != plan['execution']['analysis_environment']:
            raise ValueError('analysis_environment_mismatch')
        rows, input_bindings = capture_release(pack, consume_rows=True)
        from analyze import analyze
        save(attempt / 'analysis-environment.json', environment)
        result = analyze(rows, plan['analysis'], attempt / 'analysis')
        require_analysis_complete(result)
        _, after_bindings = capture_release(pack)
        if after_bindings != input_bindings:
            raise ValueError('analysis_input_changed_during_fit')
        save(attempt / 'analysis-output-bindings.json', {
            'freeze_sha256': digest(pack / 'freeze.json'),
            'input_bindings': input_bindings,
            'files': {path.name: digest(path) for path in sorted((attempt / 'analysis').iterdir())
                      if path.is_file()}, 'created_utc': now()})
        print(json.dumps({'status': result.get('status'), 'stage': name}, ensure_ascii=False), flush=True)
        return 0
    raise ValueError('unknown_stage')


def run(pack):
    pack = Path(pack).resolve()
    plan, root = verify(pack)
    attempt = pack / 'attempt-001'
    attempt.mkdir(exist_ok=False)
    execution = plan['execution']
    started = time.monotonic()
    launch = {'schema': 'uitraces-supervisor-launch-v1', 'started_utc': now(),
              'pid': os.getpid(), 'executable': sys.executable, 'argv': sys.argv,
              'pack': str(pack), 'freeze_sha256': digest(pack / 'freeze.json'),
              'timeouts': execution, 'automatic_retries': 0, 'model_requests': 0}
    save(attempt / 'launch.json', launch)
    receipts = []
    status = 'HOLD'
    error = None
    active = None
    try:
        for name, python, limit in (
                ('ingest', execution['ingest_python'], execution['ingest_timeout_s']),
                ('analysis', execution['analysis_python'], execution['analysis_timeout_s'])):
            command = [python, '-B', str(pack / 'snapshot/runner.py'), 'stage', '--pack', str(pack), '--stage', name]
            environment = os.environ.copy()
            for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
                environment[key] = '1'
            phase_started = time.monotonic()
            receipt = {'stage': name, 'started_utc': now(), 'command': command, 'limit_s': limit}
            with (attempt / (name + '.stdout.log')).open('xb') as stdout, (attempt / (name + '.stderr.log')).open('xb') as stderr:
                active = subprocess.Popen(command, cwd=str(pack / 'snapshot'), env=environment,
                                          stdout=stdout, stderr=stderr)
                receipt['pid'] = active.pid
                save(attempt / (name + '.launch.json'), receipt)
                last_update = 0.0
                timed_out = False
                while active.poll() is None:
                    elapsed = time.monotonic() - phase_started
                    total = time.monotonic() - started
                    if elapsed > limit or total > execution['supervisor_timeout_s']:
                        timed_out = True
                        print('Hard timeout; stopping this analysis child only.', flush=True)
                        active.terminate()
                        try:
                            active.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            active.kill()
                            active.wait(timeout=5)
                        break
                    if any((attempt / (name + suffix)).stat().st_size > execution['max_stage_log_bytes']
                           for suffix in ('.stdout.log', '.stderr.log')):
                        active.terminate()
                        active.wait(timeout=5)
                        raise ValueError('stage_log_limit')
                    if elapsed - last_update >= 15 or last_update == 0:
                        save(attempt / 'progress.json', {'status': 'RUNNING', 'stage': name,
                             'elapsed_s': elapsed, 'total_elapsed_s': total,
                             'closed_stages': len(receipts), 'child_pid': active.pid,
                             'model_requests': 0}, exclusive=False)
                        last_update = elapsed
                    time.sleep(0.5)
                receipt.update(exit_code=active.returncode, elapsed_s=time.monotonic() - phase_started,
                               finished_utc=now(), timed_out=timed_out, owned_child_exited=active.poll() is not None)
            receipts.append(receipt)
            save(attempt / (name + '.receipt.json'), receipt)
            active = None
            if timed_out or receipt['exit_code'] != 0:
                raise ValueError(name + '_stage_not_passed')
        verify(pack)
        verify_outputs(pack)
        status = 'COMPLETE_REANALYSIS_REQUIRES_NUMERIC_REVIEW'
    except Exception as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    finally:
        if active is not None and active.poll() is None:
            active.terminate()
            try:
                active.wait(timeout=5)
            except subprocess.TimeoutExpired:
                active.kill()
                active.wait(timeout=5)
        final = {'schema': 'uitraces-supervisor-final-v1', 'status': status, 'error': error,
                 'finished_utc': now(), 'elapsed_s': time.monotonic() - started,
                 'stages': receipts, 'cleanup_confirmed': active is None or active.poll() is not None,
                 'model_requests': 0, 'automatic_retries': 0,
                 'freeze_sha256': digest(pack / 'freeze.json')}
        save(attempt / 'final.json', final)
        save(attempt / 'progress.json', final, exclusive=False)
    return final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'verify', 'run', 'stage'))
    parser.add_argument('--root', default=str(HERE.parent.parent))
    parser.add_argument('--out', type=Path)
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--stage', choices=('ingest', 'analysis'))
    args = parser.parse_args()
    if args.command == 'stage':
        return stage(args.pack, args.stage)
    if args.command == 'prepare':
        result = prepare(args.root, args.out)
    elif args.command == 'verify':
        plan, root = verify(args.pack)
        result = {'status': 'FREEZE_AND_PROTECTION_PASS', 'source_commit': plan['source_commit']}
    else:
        result = run(args.pack)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0 if result.get('status') != 'HOLD' else 2


if __name__ == '__main__':
    raise SystemExit(main())
