"""Not executed: share one sanitized configuration across process and thread.

The v1/v2 attempts remain immutable. Event and isolation guards are unchanged.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import interface_probe as original

REMOVED_KEY = 'features.unified_exec_zsh_fork'
ORIGINAL_PARAMETERS = original.parameters


def configuration():
    value = dict(original.tr.CONFIG)
    if value.pop(REMOVED_KEY, None) is not False:
        raise ValueError('expected_deprecated_false_setting')
    return value


def command(binary, names):
    # The original helper still validates configured MCP names and constructs
    # per-server disable overrides. Its deprecated pair is then removed.
    argv = original.tr.config_arguments(names)
    result = []
    removed = 0
    for i in range(0, len(argv), 2):
        if argv[i] != '-c':
            raise ValueError('unexpected_config_argument_shape')
        if argv[i + 1] == REMOVED_KEY + '=false':
            removed += 1
        else:
            result.extend(argv[i:i + 2])
    if removed != 1:
        raise ValueError('expected_single_deprecated_override')
    expected = {**configuration(), **{'mcp_servers.' + name + '.enabled': False for name in names}}
    if result != [x for k, v in expected.items() for x in ['-c', k + '=' + json.dumps(v)]]:
        raise ValueError('process_thread_configuration_diverged')
    return [str(binary), 'app-server', '--stdio', *result]


def parameters():
    value = ORIGINAL_PARAMETERS()
    value['config'] = configuration()
    return value


def sources():
    return {**original.hashes(), str(Path(__file__).resolve()): original.tr.sha(Path(__file__))}


def worker(out):
    # Child-local construction hooks only; no guard or original source edits.
    original.parameters = parameters
    original.tr.command = command
    return original.worker(out)


def run(out, approved):
    if not approved:
        raise ValueError('new_attempt_requires_confirmation')
    out = out.resolve()
    if original.HERE not in out.parents:
        raise ValueError('output_must_be_in_this_new_study_directory')
    out.mkdir(parents=True, exist_ok=False)
    bindings = sources()
    original.tr.save(out / 'launch.json', {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'SINGLE_SYNTHETIC_REQUEST_V3_ONLY', 'model': 'gpt-6-luna', 'effort': 'low',
        'generation_ceiling': 1, 'generation_seconds': 60, 'total_seconds': 180,
        'cleanup_reserve_seconds': 20, 'source_sha256': bindings,
        'input_text': original.PROMPT, 'removed_key_in_both_config_paths': REMOVED_KEY,
        'auto_retry': False})
    receipt = original.watchdog.run_owned([
        sys.executable, '-B', str(Path(__file__).resolve()), '__worker', str(out)],
        out, budget_s=180, cleanup_reserve_s=20)
    original.tr.save(out / 'supervision.json', receipt)
    unchanged = bindings == sources()
    original.tr.save(out / 'revision-audit.json', {
        'source_hashes_unchanged': unchanged, 'source_sha256': bindings,
        'old_attempts_modified': False, 'guard_relaxation': False, 'formal_efficacy': False})
    passed = (unchanged and receipt['status'] == 'EXIT_ZERO' and receipt['reap_confirmed']
              and receipt['process_control_within_budget']
              and receipt.get('final_accounting', {}).get('active_processes') == 0)
    print(json.dumps({'output': str(out), 'status': 'INTERFACE_PASS_NOT_EFFICACY' if passed else 'HOLD',
                      'supervision_status': receipt['status'], 'reap_confirmed': receipt['reap_confirmed']}))
    return passed


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '__worker':
        sys.exit(0 if worker(Path(sys.argv[2])) else 2)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute-approved', action='store_true')
    args = parser.parse_args()
    sys.exit(0 if run(args.out, args.execute_approved) else 2)
