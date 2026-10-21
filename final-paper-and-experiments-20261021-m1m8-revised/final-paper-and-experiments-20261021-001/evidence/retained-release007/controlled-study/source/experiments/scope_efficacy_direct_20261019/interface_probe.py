"""One consented synthetic Codex interface probe; never an efficacy experiment.

Imports only generic containment/transport helpers, never an old campaign entry.
The only generation input and allowed final answer are constants below.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
sys.path.insert(0, str(EXPERIMENTS / 'native_goal_codex_luna'))
import luna_transport as tr
sys.path.insert(0, str(EXPERIMENTS / 'native_goal_formal_run'))
import campaign_watchdog as watchdog

BINARY = Path('LOCAL_USER/AppData/Local/OpenAI/Codex/bin/896a0166b774037a/codex.exe')
PROMPT = 'Return only {"status":"ready"}. Do not call tools or request files.'
BASE = 'You are an isolated interface-test respondent. Follow only the supplied synthetic request. Do not use tools, files, memory, or outside information.'
SCHEMA = {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ready']}},
          'required': ['status'], 'additionalProperties': False}


class ReadyGuard(tr.EventGuard):
    def result(self):
        if not self.finished or len(self.messages) != 1:
            raise ValueError('one_completed_final_required')
        if tr.strict_json(self.messages[0]) != {'status': 'ready'}:
            raise ValueError('unexpected_ready_answer')
        if self.usage is None:
            raise ValueError('usage_receipt_missing')
        return {'status': 'ready'}


def hashes():
    return {str(p): tr.sha(p) for p in [Path(__file__).resolve(), Path(tr.__file__),
                                      Path(watchdog.__file__), BINARY]}


def parameters():
    value = tr.thread_params()
    value['baseInstructions'] = BASE
    return value


def check_ready_boundary(start):
    # Requires the *returned* model/effort and empty environment/instruction roots.
    return tr.check_thread(start)


def worker(out):
    gate = watchdog.gate()  # No app-server process before owned-job assignment.
    report = {'status': 'PREFLIGHT', 'study_responses': 0, 'application_admissions': 0,
              'turn_start_requests_sent': 0, 'completed_generation_turns': 0,
              'model': tr.MODEL, 'effort': 'low', 'formal_efficacy': False,
              'hard_output_token_limit': 'not_enforced_by_this_interface',
              'underlying_provider_request_count': 'not_exposed',
              'application_retries': 0, 'token_usage': 'not_requested_yet',
              'source_sha256': hashes()}
    tr.save(out / 'request.json', {'input': PROMPT, 'output_schema': SCHEMA,
                                 'base_instructions': BASE})
    client = None
    clean = False
    try:
        auth = subprocess.run([str(BINARY), 'login', 'status'], capture_output=True,
                              timeout=5, env=tr.isolated_environment(),
                              creationflags=subprocess.CREATE_NO_WINDOW)
        auth_text = (auth.stdout + auth.stderr).decode('utf-8', errors='strict').strip()
        report['chatgpt_login_attested'] = (auth.returncode == 0 and auth_text == 'Logged in using ChatGPT')
        if not report['chatgpt_login_attested']:
            raise ValueError('current_chatgpt_login_not_attested_no_fallback')
        config_path = Path(os.environ.get('CODEX_HOME', 'LOCAL_USER/.codex')) / 'config.toml'
        names = tr.disabled_mcp(config_path)  # Reads names; never copies credentials.
        deadline = min(time.monotonic() + 45, gate['work_deadline'] - 80)
        if deadline <= time.monotonic():
            raise TimeoutError('insufficient_startup_budget')
        client = tr.Client(tr.command(BINARY, names), out, deadline)
        client.guard = ReadyGuard()
        client.request('initialize', {'clientInfo': {'name': 'scope-interface-probe',
                       'title': 'Single synthetic interface acceptance', 'version': '0.1.0'},
                       'capabilities': {'experimentalApi': True}})
        client.send({'method': 'initialized'})
        remote = client.request('remoteControl/status/read', None)
        tr.save(out / 'remote-control.json', remote)
        tr.check_remote_disabled(remote)
        start = client.request('thread/start', parameters())
        tr.save(out / 'thread-attestation.json', start)
        thread_id = check_ready_boundary(start)
        mcp = client.request('mcpServerStatus/list', {'threadId': thread_id,
                             'detail': 'toolsAndAuthOnly', 'limit': 100})
        tr.save(out / 'mcp-attestation.json', mcp)
        tr.check_mcp_empty(mcp)
        report['status'] = 'GENERATION_ADMITTED'
        report['application_admissions'] = 1
        report['token_usage'] = 'pending_not_zero'
        tr.save(out / 'generation-admission.json', {'model': tr.MODEL, 'effort': 'low',
                'input_sha256': hashlib.sha256(PROMPT.encode()).hexdigest(),
                'admitted_at_utc': datetime.now(timezone.utc).isoformat(),
                'maximum_generation_seconds': 60, 'maximum_application_admissions': 1})
        client.deadline = min(time.monotonic() + 60, gate['work_deadline'] - 15)
        report['turn_start_requests_sent'] = 1  # Counts a send attempt, not success.
        client.request('turn/start', {'threadId': thread_id, 'environments': [],
                       'runtimeWorkspaceRoots': [], 'model': tr.MODEL, 'effort': 'low',
                       'input': [{'type': 'text', 'text': PROMPT}], 'outputSchema': SCHEMA})
        while not client.guard.finished:
            client.next()
        report['answer'] = client.guard.result()
        report['completed_generation_turns'] = 1
        report['token_usage'] = client.guard.usage
        report['status'] = 'ANSWER_RECEIVED_PENDING_CLEAN_EXIT'
        clean = True
    except BaseException as exc:
        report.update(status='HOLD', error=repr(exc))
    finally:
        if client is not None:
            if client.guard.usage is not None:
                report['token_usage'] = client.guard.usage
            try:
                client.close(clean)
                report['app_server_exit_code'] = client.process.returncode
                report['stdout_reader_closed'] = not client.reader.is_alive()
            except BaseException as exc:
                report.update(status='HOLD', close_error=repr(exc))
        report['source_hashes_unchanged'] = hashes() == report['source_sha256']
        if not report['source_hashes_unchanged']:
            report['status'] = 'HOLD'
        if report['status'] == 'ANSWER_RECEIVED_PENDING_CLEAN_EXIT':
            report['status'] = 'INTERFACE_PASS_NOT_EFFICACY'
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        tr.save(out / 'report.json', report)
    return report['status'] == 'INTERFACE_PASS_NOT_EFFICACY'


def run(out, approved):
    if not approved:
        raise ValueError('single_synthetic_request_confirmation_required')
    out = out.resolve()
    if HERE not in out.parents:
        raise ValueError('output_must_be_in_this_new_study_directory')
    out.mkdir(parents=True, exist_ok=False)  # Existing attempts are never reused.
    tr.save(out / 'launch.json', {'started_at_utc': datetime.now(timezone.utc).isoformat(),
            'mode': 'SINGLE_SYNTHETIC_REQUEST_ONLY', 'model': tr.MODEL, 'effort': 'low',
            'generation_ceiling': 1, 'generation_seconds': 60, 'total_seconds': 180,
            'cleanup_reserve_seconds': 20, 'source_sha256': hashes(),
            'input_text': PROMPT, 'auto_retry': False})
    receipt = watchdog.run_owned([sys.executable, '-B', str(Path(__file__).resolve()),
                                 '__worker', str(out)], out,
                                budget_s=180, cleanup_reserve_s=20)
    tr.save(out / 'supervision.json', receipt)
    passed = (receipt['status'] == 'EXIT_ZERO' and receipt['reap_confirmed']
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
