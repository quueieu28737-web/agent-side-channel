"""33-hour formal-campaign derivative of the unchanged Windows owned-job watchdog.
Only the accepted budget ceiling differs; see test_ledger_dev.py for byte comparison.

Windows-only, no-network watchdog for an explicitly gated owned process tree.

Uses an unnamed, non-inherited Job Object with kill-on-last-handle-close and
no breakaway permission. Never enumerates or kills unrelated process IDs.
The child MUST wait for the stdin gate before spawning children or doing work.
"""
import contextlib
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time


class BasicLimits(ctypes.Structure):
    _fields_ = [('PerProcessUserTimeLimit', ctypes.c_longlong),
                ('PerJobUserTimeLimit', ctypes.c_longlong), ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD), ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD), ('SchedulingClass', wintypes.DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ('ReadOperationCount', 'WriteOperationCount',
                'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('BasicLimitInformation', BasicLimits), ('IoInfo', IOCounters),
                ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(n, ctypes.c_longlong) for n in ('TotalUserTime', 'TotalKernelTime',
                'ThisPeriodTotalUserTime', 'ThisPeriodTotalKernelTime')] + [
                (n, wintypes.DWORD) for n in ('TotalPageFaultCount', 'TotalProcesses',
                                             'ActiveProcesses', 'TotalTerminatedProcesses')]


class OwnedJob:
    def __init__(self):
        if os.name != 'nt':
            raise RuntimeError('windows_job_required_no_unprotected_fallback')
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            'SetInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            'AssignProcessToJobObject': ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            'QueryInformationJobObject': ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            'TerminateJobObject': ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE only.
        try:
            self._check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _check(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, process):
        # CPython Windows Popen owns this live process handle; no PID lookup/race.
        self._check(self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))))

    def accounting(self):
        value = Accounting()
        self._check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(value), ctypes.sizeof(value), None))
        return {'total_processes': value.TotalProcesses, 'active_processes': value.ActiveProcesses,
                'terminated_processes': value.TotalTerminatedProcesses}

    def terminate(self):
        self._check(self.api.TerminateJobObject(self.handle, 124))

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            self._check(self.api.CloseHandle(handle))


def gate():
    """No useful work before assignment. EOF or invalid gate fails closed."""
    import sys
    line = sys.stdin.buffer.readline(4097)
    if len(line) > 4096:
        raise ValueError('oversize_gate')
    value = json.loads(line)
    if value.get('protocol') != 'owned-job-gate-v1' or not isinstance(value.get('work_deadline'), (int, float)):
        raise ValueError('invalid_gate')
    if value['work_deadline'] <= time.monotonic():
        raise TimeoutError('gate_already_expired')
    return value


def run_owned(argv, out, *, budget_s=1800, cleanup_reserve_s=15, job_factory=OwnedJob,
              cancel_check=lambda: False):
    """Supervise owned processes, preserving separate parent and controller logs.

    The execution budget includes startup, work and bounded cleanup. Receipt
    publication follows reaping; unresponsive OS/filesystem/power failure is not
    certified. Parent death closes the non-inherited job handle in the kernel.
    """
    if not 0 < cleanup_reserve_s < budget_s or budget_s > 118800:
        raise ValueError('invalid_watchdog_budget')
    out = Path(out)
    began = time.monotonic()
    deadline = began + budget_s
    work_deadline = deadline - cleanup_reserve_s
    report = {'status': 'STARTING', 'budget_s': budget_s, 'cleanup_reserve_s': cleanup_reserve_s,
              'gate_released': False, 'job_assigned': False, 'reap_confirmed': False,
              'root_returncode': None, 'model_service_terminated': False}
    process = job = None
    with contextlib.ExitStack() as stack:
        stdout = stack.enter_context((out / 'watchdog.stdout.raw').open('xb'))
        stderr = stack.enter_context((out / 'watchdog.stderr.raw').open('xb'))
        try:
            job = job_factory()
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
            report['root_pid'] = process.pid
            job.assign(process)
            report['job_assigned'] = True
            report['initial_accounting'] = job.accounting()
            if cancel_check():
                raise KeyboardInterrupt('cancel_before_gate')
            if time.monotonic() >= work_deadline:
                raise TimeoutError('startup_exhausted_work_budget')
            process.stdin.write((json.dumps({'protocol': 'owned-job-gate-v1',
                                            'work_deadline': work_deadline}) + '\n').encode())
            process.stdin.flush()
            process.stdin.close()
            report['gate_released'] = True
            while True:
                if cancel_check():
                    raise KeyboardInterrupt('cancel_requested')
                code = process.poll()
                if code is not None:
                    report['status'] = 'EXIT_ZERO' if code == 0 else 'CHILD_EXIT_ERROR'
                    break
                if time.monotonic() >= work_deadline:
                    raise TimeoutError('campaign_deadline')
                time.sleep(min(.05, max(0, work_deadline - time.monotonic())))
        except KeyboardInterrupt as exc:
            report.update(status='CANCELLED', error=repr(exc))
        except TimeoutError as exc:
            report.update(status='DEADLINE', error=repr(exc))
        except BaseException as exc:
            report.update(status='SUPERVISION_ERROR', error=repr(exc))
        finally:
            try:
                if process is not None and process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if job is not None and report['job_assigned']:
                    remaining = job.accounting()
                    report['pre_cleanup_accounting'] = remaining
                    if remaining['active_processes']:
                        if report['status'] == 'EXIT_ZERO':
                            report['status'] = 'RESIDUAL_CHILDREN_TERMINATED'
                        job.terminate()
                    while True:
                        remaining = job.accounting()
                        if remaining['active_processes'] == 0:
                            report['reap_confirmed'] = True
                            break
                        if time.monotonic() >= deadline:
                            break
                        time.sleep(min(.02, max(0, deadline - time.monotonic())))
                    report['final_accounting'] = remaining
                elif process is not None:
                    # Assignment failed, so only this gated root is owned; it cannot have worked.
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    report['reap_confirmed'] = process.poll() is not None
                if process is not None:
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    report['root_returncode'] = process.returncode
            except BaseException as exc:
                report['cleanup_error'] = repr(exc)
                report['reap_confirmed'] = False
            finally:
                if job is not None:
                    try:
                        job.close()  # Kernel fallback on any error; never widens target set.
                    except BaseException as exc:
                        report['job_close_error'] = repr(exc)
                        report['reap_confirmed'] = False
                if process is not None:
                    try:
                        # Reap the root after kill-on-close fallback too. This does not
                        # certify all descendants after a failed job accounting query.
                        process.wait(timeout=max(.01, deadline - time.monotonic()))
                        report['root_returncode'] = process.returncode
                    except BaseException as exc:
                        report['root_reap_error'] = repr(exc)
                        report['reap_confirmed'] = False
            if not report['reap_confirmed']:
                report['status_before_unconfirmed_reap'] = report['status']
                report['status'] = 'REAP_UNCONFIRMED'
    report['process_control_elapsed_s'] = time.monotonic() - began
    report['process_control_within_budget'] = report['process_control_elapsed_s'] <= budget_s
    if not report['process_control_within_budget']:
        report['status_before_budget_exceeded'] = report['status']
        report['status'] = 'CONTROL_BUDGET_EXCEEDED'
    # The owner publishes this report atomically, separately from controller report.json.
    return report
