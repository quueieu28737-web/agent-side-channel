"""Read-only identity capture for members of one explicitly owned Windows Job.

Never enumerates the machine's process table and never terminates a process.
Identity and exit queries use a retained, membership-verified process handle,
not a later PID lookup. Very short-lived members may be missed: record NR.
No model, CLI, network, or shell calls occur in this module.
"""
import copy
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone, timedelta
import os
import math
import time

PARTIAL_COPY = 'command_line_query_ntstatus_0x8000000d'
COMMAND_LINE_MAX_ATTEMPTS = 4
COMMAND_LINE_RETRY_WINDOW_S = 0.100
COMMAND_LINE_RETRY_SLEEP_S = 0.020


class IncompleteRetriedIdentity(RuntimeError):
    """A bounded query never yielded complete identity: always fail closed."""


def stamp():
    return {'utc': datetime.now(timezone.utc).isoformat(), 'monotonic_s': time.monotonic()}


def filetime_ticks(value):
    return (value.dwHighDateTime << 32) | value.dwLowDateTime


def filetime_utc(ticks):
    if not ticks:
        return None
    return (datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ticks // 10)).isoformat()


class UnicodeString(ctypes.Structure):
    _fields_ = [('Length', wintypes.USHORT), ('MaximumLength', wintypes.USHORT),
                ('Buffer', ctypes.c_void_p)]


class NativeIdentityAPI:
    """Handle-bound native queries; no PowerShell/WMI helper subprocess."""
    def __init__(self):
        if os.name != 'nt':
            raise RuntimeError('windows_identity_required')
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'OpenProcess': ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL),
            'IsProcessInJob': ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            'GetProcessTimes': ([wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4, wintypes.BOOL),
            'QueryFullProcessImageNameW': ([wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            'GetExitCodeProcess': ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            'WaitForSingleObject': ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
            'QueryInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.api, name)
            fn.argtypes, fn.restype = args, result
        self.nt = ctypes.WinDLL('ntdll')
        self.nt.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG,
            ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
        self.nt.NtQueryInformationProcess.restype = wintypes.LONG

    @staticmethod
    def check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())

    def members(self, job_handle):
        for capacity in (16, 64, 256, 1024, 4096):
            class PidList(ctypes.Structure):
                _fields_ = [('assigned', wintypes.DWORD), ('listed', wintypes.DWORD),
                            ('pids', ctypes.c_size_t * capacity)]
            value, required = PidList(), wintypes.DWORD()
            ok = self.api.QueryInformationJobObject(job_handle, 3, ctypes.byref(value),
                                                    ctypes.sizeof(value), ctypes.byref(required))
            if not ok:
                error = ctypes.get_last_error()
                if error == 234:  # ERROR_MORE_DATA; bounded growth, never truncation.
                    continue
                raise ctypes.WinError(error)
            if value.listed > capacity or value.assigned > value.listed:
                continue
            return [int(value.pids[i]) for i in range(value.listed)]
        raise RuntimeError('owned_job_member_list_exceeds_4096_or_changes_too_fast')

    def open_member(self, pid, job_handle):
        handle = self.api.OpenProcess(0x1000 | 0x100000, False, pid)
        self.check(handle)
        try:
            inside = wintypes.BOOL()
            self.check(self.api.IsProcessInJob(handle, job_handle, ctypes.byref(inside)))
            if not inside.value:
                raise RuntimeError('pid_no_longer_belongs_to_owned_job')
            return handle
        except BaseException:
            self.close(handle)
            raise

    def times(self, handle):
        created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        self.check(self.api.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                           ctypes.byref(kernel), ctypes.byref(user)))
        return filetime_ticks(created), filetime_ticks(exited)

    def image(self, handle):
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        self.check(self.api.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)))
        return buffer.value

    def command_line(self, handle):
        required = wintypes.ULONG()
        self.nt.NtQueryInformationProcess(handle, 60, None, 0, ctypes.byref(required))
        if not ctypes.sizeof(UnicodeString) <= required.value <= 131072:
            raise RuntimeError('command_line_size_unavailable_or_out_of_bounds')
        buffer = ctypes.create_string_buffer(required.value)
        status = self.nt.NtQueryInformationProcess(handle, 60, buffer, len(buffer), ctypes.byref(required))
        if status != 0:
            raise RuntimeError('command_line_query_ntstatus_' + hex(status & 0xffffffff))
        value = UnicodeString.from_buffer(buffer)
        start = ctypes.addressof(buffer)
        if (value.Length % 2 or not value.Buffer or value.Length > value.MaximumLength
                or value.Buffer < start or value.Buffer + value.Length > start + len(buffer)):
            raise RuntimeError('command_line_buffer_invalid')
        return ctypes.wstring_at(value.Buffer, value.Length // 2)

    def exited(self, handle):
        result = self.api.WaitForSingleObject(handle, 0)
        if result == 0:
            return True
        if result == 258:  # WAIT_TIMEOUT: still live, no wait and no deadline extension.
            return False
        raise RuntimeError('process_wait_status_' + str(result))

    def exit_code(self, handle):
        result = wintypes.DWORD()
        self.check(self.api.GetExitCodeProcess(handle, ctypes.byref(result)))
        return int(result.value)

    def close(self, handle):
        self.check(self.api.CloseHandle(handle))


class IdentityTracker:
    def __init__(self, job, api=None, *, monotonic=None, sleep=None):
        self.job, self.api = job, api or NativeIdentityAPI()
        self.entries, self.failures, self.gaps = {}, [], []
        self.snapshot_count = 0
        self.monotonic, self.sleep = monotonic or time.monotonic, sleep or time.sleep
        self.query_deadline = None

    def set_query_deadline(self, deadline):
        if type(deadline) not in (float, int) or not math.isfinite(deadline):
            raise ValueError('finite_identity_query_deadline_required')
        # Reconfiguration can only shorten an existing deadline.
        self.query_deadline = deadline if self.query_deadline is None else min(self.query_deadline, deadline)

    def _command_line(self, handle, entry):
        """Retry only exact PARTIAL_COPY, only on the same verified held handle.

        Errors resolved here remain in the attempt journal. They are not erased
        or reclassified as errors from any historical attempt. Exhaustion/exit
        during this bounded operation cannot become a harmless observation gap.
        """
        started = self.monotonic()
        local_deadline = started + COMMAND_LINE_RETRY_WINDOW_S
        if self.query_deadline is not None:
            local_deadline = min(local_deadline, self.query_deadline)
        attempts = entry['identity_query_attempts']
        def require_retry_live():
            try:
                exited = self.api.exited(handle)
            except (OSError, RuntimeError) as exc:
                raise IncompleteRetriedIdentity('command_line_retry_exit_query_failed:'+repr(exc)) from exc
            if exited:
                raise IncompleteRetriedIdentity('command_line_retry_target_exited')
        for attempt in range(1, COMMAND_LINE_MAX_ATTEMPTS+1):
            now = self.monotonic()
            row = {'field': 'command_line', 'attempt': attempt,
                'started_monotonic_s': now, 'utc': datetime.now(timezone.utc).isoformat(),
                'deadline_monotonic_s': local_deadline,
                'same_membership_verified_held_handle': True}
            attempts.append(row)
            if now >= local_deadline:
                row.update(status='not_queried_deadline_exhausted', finished_monotonic_s=now)
                raise IncompleteRetriedIdentity('command_line_bounded_query_deadline_exhausted')
            if attempt > 1:
                try:
                    require_retry_live()
                except IncompleteRetriedIdentity as exc:
                    row.update(status='not_queried_exit_boundary', error=repr(exc),
                        finished_monotonic_s=self.monotonic())
                    raise
            try:
                result = self.api.command_line(handle)
            except (OSError, RuntimeError) as exc:
                row.update(status='query_error', error=repr(exc),
                    finished_monotonic_s=self.monotonic(),
                    exact_partial_copy=(type(exc) is RuntimeError and str(exc) == PARTIAL_COPY))
                if not row['exact_partial_copy']:
                    if attempt > 1:
                        raise IncompleteRetriedIdentity('command_line_retry_failed:'+repr(exc)) from exc
                    raise
                # An explicit outer deadline is required before ANY requery.
                if self.query_deadline is None:
                    raise IncompleteRetriedIdentity('command_line_retry_deadline_not_configured') from exc
                try:
                    require_retry_live()
                except IncompleteRetriedIdentity as boundary:
                    row['retry_stop'] = repr(boundary)
                    raise
                if attempt >= COMMAND_LINE_MAX_ATTEMPTS:
                    row['retry_stop'] = 'attempt_limit'
                    raise IncompleteRetriedIdentity('command_line_partial_copy_attempt_limit') from exc
                remaining = local_deadline-self.monotonic()
                if remaining <= COMMAND_LINE_RETRY_SLEEP_S:
                    row['retry_stop'] = 'deadline_insufficient_for_short_wait'
                    raise IncompleteRetriedIdentity('command_line_retry_deadline_exhausted') from exc
                row['retry_sleep_s'] = COMMAND_LINE_RETRY_SLEEP_S
                self.sleep(COMMAND_LINE_RETRY_SLEEP_S)
            else:
                row.update(status='query_success', finished_monotonic_s=self.monotonic())
                # A late completion must not hide exceeding the bounded window.
                if row['finished_monotonic_s'] >= local_deadline:
                    row['retry_stop'] = 'completion_after_deadline'
                    raise IncompleteRetriedIdentity('command_line_query_completed_after_deadline')
                if attempt > 1:
                    try:
                        require_retry_live()
                    except IncompleteRetriedIdentity as boundary:
                        row['retry_stop'] = repr(boundary)
                        raise
                if attempt > 1 and not result:
                    row['retry_stop'] = 'empty_result_after_retry'
                    raise IncompleteRetriedIdentity('command_line_retry_empty_result')
                row['prior_partial_copy_errors_resolved'] = attempt-1
                return result
        raise IncompleteRetriedIdentity('command_line_attempt_limit')

    def _failure(self, stage, error, pid=None):
        self.failures.append({'stage': stage, 'pid': pid, 'error': repr(error), **stamp()})

    def _capture(self, pid, stage):
        handle = None
        try:
            handle = self.api.open_member(pid, self.job.handle)
        except (OSError, RuntimeError) as exc:
            # PID disappearance is not a fabricated identity. Re-query only this Job.
            if pid not in self.api.members(self.job.handle):
                self.gaps.append({'pid': pid, 'identity': 'NR', 'reason': 'disappeared_before_handle_capture',
                                  'stage': stage, **stamp()})
                return
            self._failure(stage, exc, pid)
            return
        entry = {'pid': pid, 'owned_job_membership_verified': True,
                 'handle_binding': 'retained_native_handle_not_later_pid_lookup',
                 'first_observed': stamp(), 'creation_filetime_100ns': 'NR', 'creation_utc': 'NR',
                 'image_path': 'NR', 'command_line': 'NR', 'exit_code': 'NR',
                 'exit_utc': 'NR', 'exit_first_observed': None, 'last_observed_alive': None,
                 'identity_errors': [], 'identity_query_attempts': []}
        self.entries[pid] = (handle, entry)
        for key, query in (('creation', self.api.times), ('image_path', self.api.image),
                           ('command_line', lambda retained: self._command_line(retained, entry))):
            try:
                result = query(handle)
                if key == 'creation':
                    if not result[0]:
                        raise RuntimeError('creation_time_unavailable')
                    entry['creation_filetime_100ns'], entry['creation_utc'] = result[0], filetime_utc(result[0])
                else:
                    if not result:
                        raise RuntimeError(key + '_unavailable')
                    entry[key] = result
            except (OSError, RuntimeError) as exc:
                entry['identity_errors'].append({'field': key, 'error': repr(exc)})
                if isinstance(exc, IncompleteRetriedIdentity):
                    # Never convert an incomplete retried identity to a PASS gap.
                    self._failure(stage, exc, pid)
                elif self.api.exited(handle):
                    self.gaps.append({'pid': pid, 'field': key, 'value': 'NR',
                                      'reason': 'exited_before_field_capture', 'stage': stage, **stamp()})
                else:
                    self._failure(stage, exc, pid)

    def snapshot(self, stage):
        self.snapshot_count += 1
        when, complete, members = stamp(), True, []
        try:
            members = self.api.members(self.job.handle)
            for pid in members:
                if pid not in self.entries:
                    self._capture(pid, stage)
        except (OSError, RuntimeError) as exc:
            complete = False
            self._failure(stage, exc)
        live = []
        for pid, (handle, entry) in self.entries.items():
            try:
                if self.api.exited(handle):
                    if entry['exit_first_observed'] is None:
                        entry['exit_first_observed'] = stamp()
                        entry['exit_code'] = self.api.exit_code(handle)
                        entry['exit_utc'] = filetime_utc(self.api.times(handle)[1]) or 'NR'
                else:
                    entry['last_observed_alive'] = stamp()
                    live.append(copy.deepcopy(entry))
            except (OSError, RuntimeError) as exc:
                self._failure(stage, exc, pid)
        return {'stage': stage, **when, 'query_complete': complete,
                'diagnostic_pass': complete and not self.failures,
                'enumerated_job_pids': members, 'live': live,
                'history': [copy.deepcopy(entry) for _, entry in self.entries.values()],
                'failures': copy.deepcopy(self.failures), 'observability_gaps': copy.deepcopy(self.gaps),
                'coverage_limit': '50-ms/phase sampling can miss short-lived members; total Job count is reported separately; missing identities stay NR'}

    def close(self):
        errors = []
        for handle, _ in self.entries.values():
            try:
                self.api.close(handle)
            except (OSError, RuntimeError) as exc:
                errors.append(repr(exc))
        self.entries.clear()
        if errors:
            raise RuntimeError('identity_handle_close_errors:' + ';'.join(errors))



