"""Contained Codex subscription transport, not a raw-model API.

The only model-facing data are an episode's already-constructed messages/tools.
Codex receives no execution environment and no executable tools. Its structured
assistant envelope goes back through the UNCHANGED local broker. Raw app-server
stdout/stderr and client frames are retained; underlying HTTP and hidden reasoning
are not exposed by this interface and must not be described as recorded.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import tomllib

MODEL = 'gpt-6-luna'
CLI_VERSION = 'codex-cli 0.158.0-alpha.2.1'
VERSION = 'codex-luna-envelope-v8'
BASE = ('You are an isolated retail-task decision provider. Return ONLY the next '
        'assistant message for the supplied messages and function schemas. '
        'The supplied system message defines the task policy. Do not execute tools '
        'yourself. Select a function by returning its original name and exact JSON '
        'argument string in tool_calls, or return a user-facing content reply. '
        'Do not invent tool observations. The local application executes selected '
        'calls and supplies the next history. No research analysis or filesystem access.')
OFF = ('shell_tool', 'unified_exec_tty', 'unified_exec_zsh_fork',
       'apply_patch_freeform', 'apps', 'plugins',
       'remote_plugin', 'hooks', 'multi_agent', 'multi_agent_v2', 'memories',
       'code_mode', 'code_mode_host', 'browser_use', 'browser_use_external',
       'computer_use', 'in_app_browser', 'image_generation', 'view_image',
       'skill_search', 'workspace_dependencies', 'goals', 'sleep_tool',
       'tool_suggest', 'unbounded_connection_retries', 'shell_snapshot',
       'deferred_executor', 'request_permissions_tool', 'token_budget',
       'current_time_reminder', 'send_message_to_user_async',
       'skill_mcp_dependency_install', 'recommended_plugins', 'daemon_auto_start')
CONFIG = {**{'features.'+k: False for k in OFF},
          # Pinned upstream managed_features.rs normalizes this implementation
          # selector to true. It is NOT tool authorization: spec_plan.rs gates
          # exec on ShellTool AND a nonempty execution environment.
          'features.unified_exec': True,
          'features.skip_host_skill_discovery': True,
          'agents.enabled': False, 'web_search': 'disabled',
          'tools.update_plan.enabled': False,
          'tools.experimental_request_user_input.enabled': False,
          'project_doc_max_bytes': 0, 'skills.include_instructions': False,
          'include_environment_context': False, 'include_apps_instructions': False,
          'include_collaboration_mode_instructions': False,
          'notify': [], 'model_provider': 'openai', 'model_reasoning_effort': 'low'}
# The CLI reserves built-in provider IDs. Do not invent an override or switch
# providers to force retry counts. Application retries are zero; internal
# provider retries are NOT controlled/observed by this adapter.
RETRY_POLICY = {'application_retries': 0, 'provider_retry_override': False,
                'provider_internal_retries': 'NR',
                'provider_behavior': 'built-in provider; CLI-managed retries may occur'}
ALLOWED_ITEM_TYPES = {'userMessage', 'agentMessage', 'reasoning'}
ALLOWED_NOTIFICATIONS = {'thread/started', 'thread/status/changed', 'turn/started',
    'turn/completed', 'item/started', 'item/completed', 'item/agentMessage/delta',
    'item/reasoning/summaryTextDelta', 'item/reasoning/summaryPartAdded',
    'item/reasoning/textDelta', 'thread/tokenUsage/updated',
    'account/rateLimits/updated', 'model/rerouted', 'remoteControl/status/changed',
    'deprecationNotice', 'warning', 'account/updated', 'model/verification',
    'model/safetyBuffering/updated', 'turn/moderationMetadata'}

PINNED_UPSTREAM_COMMIT = '0d9c7cbfa6cf1489f55a8a9542b75ddd2c061807'


def check_startup_notice(method, params):
    if not isinstance(params, dict):
        raise ValueError('malformed_startup_notice')
    if method == 'deprecationNotice':
        # Historical v3 receipt replay only; the alias is absent from v4 config.
        expected = {
            'summary': '`[features].experimental_use_unified_exec_tool` is deprecated. Use `[features].unified_exec` instead.',
            'details': 'Enable it with `--enable unified_exec` or `[features].unified_exec` in config.toml. See https://developers.openai.com/codex/config-basic#feature-flags for details.'}
        if params != expected:
            raise ValueError('unreviewed_deprecation_notice')
    elif (set(params)-{'message', 'threadId'}
            or not isinstance(params.get('threadId'), (str, type(None)))
            or not isinstance(params.get('message'), str)
            or (params['message'] != CODE_MODE_DISABLED_NOTICE and not re.fullmatch(r'Under-development features enabled: skip_host_skill_discovery\. Under-development features are incomplete and may behave unpredictably\. To suppress this warning, set `suppress_unstable_features_warning = true` in [^\r\n]+config\.toml\.', params['message']))):
        raise ValueError('unreviewed_startup_warning')


CODE_MODE_DISABLED_NOTICE = ('Code Mode is unavailable because code-mode host is disabled. '
    'Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.')


def isolated_environment():
    """Do not inherit this research thread's app pipes, identity or overrides.

    Keep the user's existing CODEX_HOME (if set), never copy/read authentication.
    This is child-local hygiene, NOT an OS sandbox or a tool-access attestation.
    """
    return {key: value for key, value in os.environ.items()
            if not key.upper().startswith('CODEX_') or key.upper() == 'CODEX_HOME'}


def check_remote_disabled(params):
    if (not isinstance(params, dict)
            or set(params)-{'status', 'environmentId', 'serverName', 'installationId'}
            or params.get('status') != 'disabled'
            or params.get('environmentId') is not None
            or not isinstance(params.get('serverName'), str)
            or not isinstance(params.get('installationId'), str)):
        raise ValueError('remote_control_not_attested_disabled')


def check_mcp_empty(result):
    # The protocol inventories disabled CONFIGURED servers as well. Require
    # zero available capabilities, not absence of display-only disabled rows.
    rows = result.get('data')
    if not isinstance(rows, list) or result.get('nextCursor') is not None:
        raise ValueError('mcp_inventory_not_attested_empty')
    for row in rows:
        if (not isinstance(row, dict) or row.get('runtimeStatus') != 'disabled'
                or row.get('tools') != {} or row.get('resources') != []
                or row.get('resourceTemplates') != []
                or row.get('serverInfo') is not None
                or row.get('serverCapabilities') is not None
                or row.get('toolsError') is not None):
            raise ValueError('mcp_capabilities_not_attested_disabled')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def save(path, value):
    with Path(path).open('xb') as stream:
        stream.write(encoded(value)+b'\n')
        stream.flush(); os.fsync(stream.fileno())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def payload(messages, tools):
    """No plan/account/score/path argument; reject undeclared envelope fields."""
    if not messages or messages[0].get('role') != 'system':
        raise ValueError('original_system_message_required')
    for message in messages:
        if (not isinstance(message, dict) or
                set(message)-{'role', 'content', 'tool_calls', 'tool_call_id'} or
                message.get('role') not in {'system', 'user', 'assistant', 'tool'}):
            raise ValueError('unapproved_message_fields')
    names = []
    for tool in tools:
        if set(tool) != {'type', 'function'} or tool['type'] != 'function':
            raise ValueError('unapproved_tool_envelope')
        fn = tool['function']
        if set(fn)-{'name', 'description', 'parameters', 'strict'}:
            raise ValueError('unapproved_tool_fields')
        if not re.fullmatch('[a-zA-Z0-9_]+', fn['name']):
            raise ValueError('invalid_tool_name')
        names.append(fn['name'])
    if not names or len(set(names)) != len(names):
        raise ValueError('empty_or_duplicate_tools')
    return copy.deepcopy({'messages': messages, 'tools': tools})


def output_schema(tools):
    return {'type': 'object', 'additionalProperties': False,
        'required': ['role', 'content', 'tool_calls'], 'properties': {
        'role': {'type': 'string', 'enum': ['assistant']},
        'content': {'type': ['string', 'null']},
        'tool_calls': {'type': 'array', 'items': {'type': 'object',
            'additionalProperties': False, 'required': ['id', 'type', 'function'],
            'properties': {'id': {'type': 'string'},
                'type': {'type': 'string', 'enum': ['function']},
                'function': {'type': 'object', 'additionalProperties': False,
                    'required': ['name', 'arguments'], 'properties': {
                        'name': {'type': 'string', 'enum': [t['function']['name'] for t in tools]},
                        'arguments': {'type': 'string'}}}}}}}}


def disabled_mcp(config_file):
    """Read only server names, never log credentials or copy authentication."""
    if not config_file.exists():
        return []
    data = tomllib.loads(config_file.read_text(encoding='utf-8'))
    if data.get('profile'):
        raise ValueError('configured_profile_requires_separate_review')
    if data.get('model_instructions_file'):
        raise ValueError('custom_model_instructions_not_allowed')
    if set(data.get('model_providers', {})) & {'openai', 'ollama', 'lmstudio'}:
        raise ValueError('reserved_builtin_provider_override')
    if data.get('openai_base_url') or data.get('chatgpt_base_url'):
        raise ValueError('provider_endpoint_override_requires_separate_review')
    names = sorted(data.get('mcp_servers', {}))
    if any(not re.fullmatch('[a-zA-Z0-9_-]+', name) for name in names):
        raise ValueError('unsupported_mcp_name')
    return names


def config_arguments(mcp_names):
    if any(not re.fullmatch('[a-zA-Z0-9_-]+', name) for name in mcp_names):
        raise ValueError('unsupported_mcp_name')
    config = {**CONFIG, **{'mcp_servers.'+n+'.enabled': False for n in mcp_names}}
    if any(key == 'model_providers' or key.startswith('model_providers.') for key in config):
        raise ValueError('provider_table_overrides_not_allowed')
    argv = []
    for key, value in config.items():
        argv += ['-c', key+'='+json.dumps(value)]
    return argv


def command(binary, mcp_names):
    return [str(binary), 'app-server', '--stdio', *config_arguments(mcp_names)]


def config_check_command(binary, mcp_names):
    # Real CLI config loading without app-server, authentication or a model turn.
    # No `features enable/disable`: only read-only `features list`.
    return [str(binary), 'features', 'list', *config_arguments(mcp_names)]


def thread_params():
    return {'model': MODEL, 'modelProvider': 'openai', 'allowProviderModelFallback': False,
        'ephemeral': True, 'environments': [], 'runtimeWorkspaceRoots': [],
        'selectedCapabilityRoots': [], 'dynamicTools': [], 'approvalPolicy': 'never',
        'sandbox': 'read-only', 'baseInstructions': BASE, 'developerInstructions': '',
        'config': CONFIG, 'experimentalRawEvents': False}


def check_thread(result):
    if (result.get('model') != MODEL or result.get('modelProvider') != 'openai'
            or result.get('reasoningEffort') != 'low'
            or result.get('instructionSources') != []
            or result.get('runtimeWorkspaceRoots') != []
            or result.get('thread', {}).get('environments') != []
            or result.get('thread', {}).get('ephemeral') is not True
            or result.get('approvalPolicy') != 'never'
            or result.get('sandbox') != {'type': 'readOnly', 'networkAccess': False}
            or result.get('thread', {}).get('parentThreadId') is not None
            or result.get('thread', {}).get('forkedFromId') is not None):
        raise ValueError('thread_boundary_or_model_not_attested')
    return result['thread']['id']


class EventGuard:
    def __init__(self):
        self.finished = False
        self.messages = []
        self.annotations = []
        self.usage = None

    def observe(self, frame):
        if 'method' not in frame:
            return
        method, params = frame['method'], frame.get('params', {})
        if 'id' in frame:
            raise ValueError('server_tool_or_approval_request_forbidden')
        if method not in ALLOWED_NOTIFICATIONS or method == 'model/rerouted':
            raise ValueError('unapproved_server_event:'+method)
        if method == 'remoteControl/status/changed':
            check_remote_disabled(params)
        if method in {'warning', 'deprecationNotice'}:
            check_startup_notice(method, params)
        if method == 'account/updated':
            if (not isinstance(params, dict) or set(params)-{'authMode', 'planType'}
                    or params.get('authMode') != 'chatgpt'
                    or not isinstance(params.get('planType'), (str, type(None)))):
                raise ValueError('subscription_auth_boundary_changed')
        if method in {'model/verification', 'model/safetyBuffering/updated', 'turn/moderationMetadata'}:
            if (not isinstance(params, dict) or not isinstance(params.get('threadId'), str)
                    or not isinstance(params.get('turnId'), str)):
                raise ValueError('malformed_provider_metadata')
            if method == 'model/verification' and (
                    set(params) != {'threadId', 'turnId', 'verifications'}
                    or not isinstance(params['verifications'], list)
                    or any(v != 'trustedAccessForCyber' for v in params['verifications'])):
                raise ValueError('unreviewed_model_verification')
            if method == 'turn/moderationMetadata' and set(params) != {'threadId', 'turnId', 'metadata'}:
                raise ValueError('malformed_moderation_metadata')
            if method == 'model/safetyBuffering/updated' and (
                    set(params)-{'threadId', 'turnId', 'model', 'reasons', 'useCases', 'showBufferingUi', 'fasterModel'}
                    or params.get('model') != MODEL
                    or not isinstance(params.get('showBufferingUi'), bool)
                    or not isinstance(params.get('reasons'), list)
                    or not isinstance(params.get('useCases'), list)):
                raise ValueError('buffering_model_boundary_changed')
        if method in {'item/started', 'item/completed'}:
            item = params.get('item', {})
            if item.get('type') not in ALLOWED_ITEM_TYPES:
                raise ValueError('executable_or_unknown_item_forbidden')
            if method == 'item/completed' and item['type'] == 'agentMessage':
                phase = item.get('phase')
                if phase == 'commentary':
                    # Private raw annotations are NOT a business-tool envelope.
                    # Never parse/execute them, even if they resemble JSON.
                    self.annotations.append(item.get('text'))
                elif phase in {None, 'final_answer'}:
                    self.messages.append(item.get('text'))
                else:
                    raise ValueError('unreviewed_assistant_message_phase')
        if method == 'thread/tokenUsage/updated':
            self.usage = params.get('tokenUsage')
        if method == 'turn/completed':
            if self.finished or params.get('turn', {}).get('status') != 'completed':
                raise ValueError('incomplete_or_duplicate_turn')
            self.finished = True

    def result(self):
        if not self.finished or len(self.messages) != 1 or not isinstance(self.messages[0], str):
            raise ValueError('one_completed_assistant_required')
        value = strict_json(self.messages[0])
        if (set(value) != {'role', 'content', 'tool_calls'} or value['role'] != 'assistant'
                or not isinstance(value['tool_calls'], list)
                or (value['content'] is not None and not isinstance(value['content'], str))):
            raise ValueError('invalid_assistant_envelope')
        # Business argument/authorization validation stays with the existing broker.
        return value


class Client:
    """JSONL child, raw bytes first; no external calls on module import."""
    def __init__(self, argv, out, deadline):
        self.out, self.deadline = Path(out), deadline
        self.items, self.guard, self.index = queue.Queue(), EventGuard(), 0
        self.stdout = (self.out/'server.stdout.raw').open('xb')
        self.stderr = (self.out/'server.stderr.raw').open('xb')
        self.sent = (self.out/'client.jsonl').open('xb')
        try:
            self.process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=self.stderr, cwd=self.out, env=isolated_environment(),
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except BaseException:
            self.stdout.close(); self.stderr.close(); self.sent.close()
            raise
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            while True:
                raw = self.process.stdout.readline(2_000_001)
                if not raw:
                    self.items.put(('eof', None)); return
                self.stdout.write(raw); self.stdout.flush(); os.fsync(self.stdout.fileno())
                if len(raw) > 2_000_000 or not raw.endswith(b'\n'):
                    raise ValueError('oversize_or_unterminated_frame')
                self.items.put(('frame', strict_json(raw)))
        except BaseException as exc:
            self.items.put(('error', repr(exc)))

    def send(self, frame):
        raw = encoded(frame)+b'\n'
        self.sent.write(raw); self.sent.flush(); os.fsync(self.sent.fileno())
        self.process.stdin.write(raw); self.process.stdin.flush()

    def next(self):
        remaining = self.deadline-time.monotonic()
        if remaining <= 0:
            raise TimeoutError('decision_deadline')
        try:
            kind, value = self.items.get(timeout=remaining)
        except queue.Empty:
            raise TimeoutError('decision_deadline') from None
        if kind != 'frame':
            raise RuntimeError('appserver_'+kind+':'+str(value))
        if 'error' in value:
            raise RuntimeError('appserver_error')
        self.guard.observe(value)
        return value

    def request(self, method, params):
        self.index += 1
        current = self.index
        self.send({'id': current, 'method': method, 'params': params})
        while True:
            frame = self.next()
            if frame.get('id') == current:
                return frame['result']
            if 'id' in frame:
                raise ValueError('unexpected_response_id')

    def close(self, clean):
        failure = None
        try:
            try:
                self.process.stdin.close()
            except OSError as exc:
                failure = exc
            try:
                self.process.wait(timeout=max(.01, min(5, self.deadline-time.monotonic())))
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=5)
                if clean:
                    failure = RuntimeError('appserver_did_not_exit_cleanly')
            self.reader.join(timeout=5)
            if self.reader.is_alive():
                raise RuntimeError('stdout_drain_not_confirmed')
            while not self.items.empty():
                kind, frame = self.items.get_nowait()
                if kind == 'frame':
                    self.guard.observe(frame)
                elif kind == 'error':
                    raise RuntimeError('late_reader_error')
            if clean and self.process.returncode != 0:
                raise RuntimeError('nonzero_appserver_exit')
            if failure is not None and clean:
                raise failure
        finally:
            if self.process.poll() is None:
                self.process.kill(); self.process.wait(timeout=5)
            self.reader.join(timeout=5)
            self.process.stdout.close()
            self.stdout.close(); self.stderr.close(); self.sent.close()


def decision(binary, mcp_names, request, out, deadline, *, preflight=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    approved = payload(request['messages'], request['tools'])
    save(out/'input.json', approved)
    client = Client(command(binary, mcp_names), out, deadline)
    clean = False
    try:
        client.request('initialize', {'clientInfo': {'name': 'bounded-retail', 'version': VERSION},
            'capabilities': {'experimentalApi': True}})
        client.send({'method': 'initialized'})
        requirements = client.request('configRequirements/read', None)
        save(out/'requirements.json', requirements)
        remote = client.request('remoteControl/status/read', None)
        save(out/'remote-control.json', remote)
        check_remote_disabled(remote)
        # Raw config can contain credentials. Do NOT request config/read here.
        # Isolation is enforced by no environments + disabled process-local
        # capabilities; live preflight must attest the returned thread boundary.
        start = client.request('thread/start', thread_params())
        save(out/'thread-attestation.json', start)
        thread_id = check_thread(start)
        mcp = client.request('mcpServerStatus/list', {'threadId': thread_id,
            'detail': 'toolsAndAuthOnly', 'limit': 100})
        save(out/'mcp-attestation.json', mcp)
        check_mcp_empty(mcp)
        if not preflight:
            client.request('turn/start', {'threadId': thread_id, 'environments': [],
                'runtimeWorkspaceRoots': [], 'model': MODEL, 'effort': 'low',
                'input': [{'type': 'text', 'text': encoded(approved).decode()}],
                'outputSchema': output_schema(approved['tools'])})
            while not client.guard.finished:
                client.next()
            answer = client.guard.result()
        else:
            answer = None
        clean = True
    finally:
        client.close(clean)
    # Success only after EOF, zero exit and late-event checks. Never repair JSON.
    save(out/'result.json', {'message': answer, 'model': MODEL,
        'mode': 'PREFLIGHT_NO_GENERATION' if preflight else VERSION,
        'token_usage': client.guard.usage, 'underlying_http_requests': 'NR',
        'private_annotations': client.guard.annotations,
        'underlying_http_bytes': 'NR', 'hidden_reasoning': 'NR',
        'retry_policy': RETRY_POLICY})
    return answer
