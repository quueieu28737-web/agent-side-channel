"""Contained text/plan collection; reuse audited JSONL and owned-job primitives.

No model calls occur on import. No executable tools or research files are supplied
to the ephemeral model thread. Provider-internal retry counts are not exposed.
"""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'experiments/scope_workflow_v2_20261019/runner_a1'
sys.path.insert(0, str(PRIOR))
spec = importlib.util.spec_from_file_location('controlled_prior_transport', PRIOR / 'transport.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
import owned

tr = prior.core.tr
MODEL, EFFORT = 'gpt-6-luna', 'low'
BINARY = Path('LOCAL_USER/AppData/Local/OpenAI/Codex/bin/896a0166b774037a/codex.exe')
BASE = ('You provide one response to a synthetic controlled task. Use only the '
        'supplied task. Return the requested JSON object. Do not use tools, files, '
        'memory, search, or external sources. Proposed tool actions are data for '
        'the local application; never execute them yourself.')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def startup(out, deadline):
    names = tr.disabled_mcp(Path(os.environ.get('CODEX_HOME', 'LOCAL_USER/.codex')) / 'config.toml')
    client = prior.WorkflowClient(prior.compatible.command(BINARY, names), out, min(time.monotonic()+40, deadline-20))
    client.guard = prior.WorkflowGuard()
    try:
        init = client.request('initialize', {'clientInfo': {'name': 'controlled-defense-study', 'version': '1.0.0'},
                                           'capabilities': {'experimentalApi': True}})
        tr.save(out / 'initialize.json', init)
        client.send({'method': 'initialized'})
        remote = client.request('remoteControl/status/read', None)
        tr.save(out / 'remote-control.json', remote)
        tr.check_remote_disabled(remote)
        models = client.request('model/list', {'limit': 100, 'includeHidden': True})
        tr.save(out / 'models.json', models)
        rows = models.get('data', [])
        matches = [x for x in rows if x.get('model') == MODEL or x.get('id') == MODEL]
        if not matches:
            raise ValueError('requested_gpt6_luna_absent_no_substitution')
        params = prior.compatible.parameters()
        params['baseInstructions'] = BASE
        start = client.request('thread/start', params)
        tr.save(out / 'thread-attestation.json', start)
        tid = prior.valid_thread(start, client.guard)
        mcp = client.request('mcpServerStatus/list', {'threadId': tid, 'detail': 'toolsAndAuthOnly', 'limit': 100})
        tr.save(out / 'mcp-attestation.json', mcp)
        tr.check_mcp_empty(mcp)
        return client, tid
    except BaseException:
        client.close(False)
        raise


def preflight(out, deadline):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'STARTING', 'application_admissions': 0, 'model': MODEL, 'effort': EFFORT}
    client = None
    try:
        for name, argv in [('version', [str(BINARY), '--version']), ('auth', [str(BINARY), 'login', 'status'])]:
            run = subprocess.run(argv, capture_output=True, timeout=10, env=tr.isolated_environment(),
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            (out / (name+'.stdout.raw')).write_bytes(run.stdout)
            (out / (name+'.stderr.raw')).write_bytes(run.stderr)
            if run.returncode:
                raise ValueError('cli_'+name+'_failed')
            if name == 'auth' and (run.stdout+run.stderr).decode().strip() != 'Logged in using ChatGPT':
                raise ValueError('chatgpt_login_not_attested')
        client, tid = startup(out, deadline)
        result.update(status='NO_GENERATION_PREFLIGHT_PASS', thread_id=tid)
        client.close(True)
        client = None
    except BaseException as exc:
        result.update(status='HOLD', error=repr(exc))
    finally:
        if client is not None:
            try:
                client.close(False)
            except BaseException as exc:
                result['close_error'] = repr(exc)
        result['finished_utc'] = stamp()
        tr.save(out/'result.json', result)
    return result


def one_request(request, out, deadline):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    tr.save(out/'request.json', request)
    r = {'id': request['id'], 'model': MODEL, 'effort': EFFORT, 'status': 'PREFLIGHT',
         'application_admissions': 0, 'application_retries': 0, 'provider_internal_retries': 'NR',
         'started_utc': stamp(), 'token_usage': 'not_requested', 'prediction': None}
    client, clean = None, False
    began = time.monotonic()
    try:
        if len(request['prompt'].encode()) > 32768:
            raise ValueError('input_limit')
        client, tid = startup(out, deadline)
        if time.monotonic()+125 > deadline:
            raise TimeoutError('insufficient_remaining_request_budget')
        tr.save(out/'generation-admission.json', {'id': request['id'], 'utc': stamp(), 'model': MODEL,
                                                'effort': EFFORT, 'local_wait_s': 120})
        r.update(application_admissions=1, token_usage='pending_not_zero')
        client.guard.turn_permitted = True
        client.deadline = min(time.monotonic()+120, deadline-10)
        started = client.request('turn/start', {'threadId': tid, 'environments': [], 'runtimeWorkspaceRoots': [],
            'model': MODEL, 'effort': EFFORT, 'input': [{'type': 'text', 'text': request['prompt']}],
            'outputSchema': request['schema']})
        turn = started.get('turn', {}).get('id')
        if not turn or client.guard.turn_id not in (None, turn):
            raise ValueError('turn_identity_mismatch')
        client.guard.turn_id = turn
        while not client.guard.finished:
            client.next()
        raw, usage = client.guard.completed_text_and_usage()
        r.update(status='COMPLETE_PENDING_EXIT', token_usage=usage, thread_id=tid, turn_id=turn)
        clean = True
    except BaseException as exc:
        r.update(status='HOLD', error=repr(exc))
    finally:
        if client is not None:
            if client.guard.usage is not None:
                r['token_usage'] = client.guard.usage
            try:
                client.close(clean)
                r.update(exit_code=client.process.returncode, stdout_eof=client.saw_stdout_eof,
                         reader_closed=not client.reader.is_alive())
                if clean:
                    raw, usage = client.guard.completed_text_and_usage()
                    r['token_usage'] = usage
                    (out/'final-answer.raw.txt').write_text(raw, encoding='utf-8', newline='')
            except BaseException as exc:
                r.update(status='HOLD', close_error=repr(exc))
        if r['status'] == 'COMPLETE_PENDING_EXIT':
            try:
                r['prediction'] = tr.strict_json(raw)
                r['status'] = 'COMPLETE'
            except (ValueError, TypeError) as exc:
                r.update(status='CONTENT_FAILURE', content_error=repr(exc))
        r.update(finished_utc=stamp(), elapsed_s=time.monotonic()-began)
        tr.save(out/'response.json', r)
    return r
