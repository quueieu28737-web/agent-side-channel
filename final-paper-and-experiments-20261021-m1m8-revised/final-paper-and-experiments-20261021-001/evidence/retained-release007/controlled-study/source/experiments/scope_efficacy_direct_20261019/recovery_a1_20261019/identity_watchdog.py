"""Owned-job identity/timeline capture plus a bounded natural drain window.

No model/network calls, machine-wide process enumeration or PID-based killing.
The original watchdog and old attempt are never modified or reclassified.
"""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STUDY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STUDY))
import interface_probe as core

IDENTITY_PATH = STUDY.parent.parent / 'evidence/acm-screening-20261010-luna-full-005/identity_capture.py'
IDENTITY_SHA = '0966fb93eedb0120059ec567dca301d2bf84b64214b718bbed018fe5b53efc3e'
if hashlib.sha256(IDENTITY_PATH.read_bytes()).hexdigest() != IDENTITY_SHA:
    raise RuntimeError('read_only_native_identity_dependency_changed')
spec = importlib.util.spec_from_file_location('scope_a1_native_identity', IDENTITY_PATH)
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)

NATURAL_DRAIN_SECONDS = 1.0


def bounded_drain(job, observe, deadline, *, grace_s=NATURAL_DRAIN_SECONDS,
                  clock=time.monotonic, sleep=time.sleep):
    """Natural exit only, within the existing total budget; never extend it."""
    if not 0 <= grace_s <= NATURAL_DRAIN_SECONDS:
        raise ValueError('natural_drain_limit_changed')
    started = clock()
    end = min(started + grace_s, deadline - 5.0)  # reserve forced-cleanup time
    before = job.accounting()
    after = before
    while after['active_processes'] and clock() < end:
        observe('bounded_natural_drain')
        after = job.accounting()
        if after['active_processes'] == 0:
            break
        sleep(min(.02, max(0, end - clock())))
        after = job.accounting()
    return {'before': before, 'after': after, 'maximum_s': grace_s,
            'elapsed_s': clock() - started, 'deadline_monotonic_s': end,
            'drained_naturally': before['active_processes'] > 0 and after['active_processes'] == 0}


def run_owned(argv, out, *, budget_s, cleanup_reserve_s, identity_api_factory=None):
    if not 5 < cleanup_reserve_s < budget_s or budget_s > 10800:
        raise ValueError('invalid_owned_identity_budget')
    out = Path(out)
    started = time.monotonic()
    deadline = started + budget_s
    work_deadline = deadline - cleanup_reserve_s
    report = {'status': 'STARTING', 'budget_s': budget_s, 'cleanup_reserve_s': cleanup_reserve_s,
        'gate_released': False, 'job_assigned': False, 'reap_confirmed': False,
        'root_returncode': None, 'model_service_terminated': False,
        'natural_drain_limit_s': NATURAL_DRAIN_SECONDS,
        'identity_handle_binding': 'membership_verified_retained_handle',
        'identity_sampling_limit': 'short-lived members may be missed; missing identities remain NR'}
    process = job = tracker = None
    last_signature = None
    with contextlib.ExitStack() as stack:
        stdout = stack.enter_context((out / 'watchdog.stdout.raw').open('xb'))
        stderr = stack.enter_context((out / 'watchdog.stderr.raw').open('xb'))
        journal = stack.enter_context((out / 'identity-timeline.jsonl').open('xb'))

        def observe(stage, strict=True):
            nonlocal last_signature
            snap = tracker.snapshot(stage)
            signature = [(r['pid'], r['creation_filetime_100ns'], r['image_path'], r['command_line'],
                          r['exit_code'], r['exit_utc'], len(r['identity_errors'])) for r in snap['history']]
            signature += [('failures', len(snap['failures']), 'gaps', len(snap['observability_gaps']))]
            if signature != last_signature or stage != 'during_work':
                journal.write((json.dumps(snap, ensure_ascii=False) + '\n').encode())
                journal.flush()
                os.fsync(journal.fileno())
                last_signature = signature
            report['identity_failures_observed'] = len(snap['failures'])
            report['identity_observability_gaps'] = len(snap['observability_gaps'])
            if strict and not snap['diagnostic_pass']:
                raise RuntimeError('owned_identity_capture_failed_closed')
            return snap

        try:
            job = core.watchdog.OwnedJob()
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
            report['root_pid'] = process.pid
            job.assign(process)
            report['job_assigned'] = True
            tracker = identity.IdentityTracker(job, api=identity_api_factory() if identity_api_factory else None)
            tracker.set_query_deadline(work_deadline)
            first = observe('root_assigned_before_gate')
            root = next((r for r in first['history'] if r['pid'] == process.pid), None)
            expected_command = subprocess.list2cmdline([str(a) for a in argv])
            if (root is None or root['creation_filetime_100ns'] == 'NR'
                    or root['command_line'] != expected_command
                    or os.path.normcase(os.path.normpath(root['image_path'])) != os.path.normcase(os.path.normpath(argv[0]))):
                raise RuntimeError('gated_root_identity_not_bound_to_exact_command')
            report['root_identity'] = root
            report['initial_accounting'] = job.accounting()
            if time.monotonic() >= work_deadline:
                raise TimeoutError('startup_exhausted_work_budget')
            process.stdin.write((json.dumps({'protocol': 'owned-job-gate-v1', 'work_deadline': work_deadline}) + '\n').encode())
            process.stdin.flush()
            process.stdin.close()
            report['gate_released'] = True
            while True:
                observe('during_work')
                code = process.poll()
                if code is not None:
                    report['status'] = 'EXIT_ZERO' if code == 0 else 'CHILD_EXIT_ERROR'
                    report['root_exit_observed'] = identity.stamp()
                    observe('root_exited')
                    if code == 0:
                        report['natural_drain'] = bounded_drain(job, observe, deadline)
                    break
                if time.monotonic() >= work_deadline:
                    raise TimeoutError('owned_work_deadline')
                time.sleep(min(.02, max(0, work_deadline - time.monotonic())))
        except TimeoutError as exc:
            report.update(status='DEADLINE', error=repr(exc))
        except BaseException as exc:
            report.update(status='SUPERVISION_ERROR', error=repr(exc))
        finally:
            try:
                if process is not None and process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if job is not None and report['job_assigned']:
                    if tracker is not None:
                        observe('pre_cleanup', strict=False)
                    report['pre_cleanup_accounting'] = job.accounting()
                    if report['pre_cleanup_accounting']['active_processes']:
                        if report['status'] == 'EXIT_ZERO':
                            report['status'] = 'RESIDUAL_CHILDREN_TERMINATED'
                        report['owned_job_termination_requested'] = identity.stamp()
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
                    if tracker is not None:
                        report['final_identity_snapshot'] = observe('after_cleanup', strict=False)
                        if tracker.failures and report['status'] == 'EXIT_ZERO':
                            report['status'] = 'IDENTITY_FAILURE'
                elif process is not None:
                    # No gate was released; only this owned root can have run.
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    report['reap_confirmed'] = process.poll() is not None
                if process is not None:
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    report['root_returncode'] = process.returncode
            except BaseException as exc:
                report.update(cleanup_error=repr(exc), reap_confirmed=False)
            finally:
                if tracker is not None:
                    try:
                        tracker.close()
                    except BaseException as exc:
                        report.update(identity_handle_close_error=repr(exc), reap_confirmed=False)
                if job is not None:
                    try:
                        job.close()
                    except BaseException as exc:
                        report.update(job_close_error=repr(exc), reap_confirmed=False)
                if process is not None:
                    try:
                        process.wait(timeout=max(.01, deadline - time.monotonic()))
                        report['root_returncode'] = process.returncode
                    except BaseException as exc:
                        report.update(root_reap_error=repr(exc), reap_confirmed=False)
            if not report['reap_confirmed']:
                report['status_before_unconfirmed_reap'] = report['status']
                report['status'] = 'REAP_UNCONFIRMED'
    report['process_control_elapsed_s'] = time.monotonic() - started
    report['process_control_within_budget'] = report['process_control_elapsed_s'] <= budget_s
    if not report['process_control_within_budget']:
        report['status_before_budget_exceeded'] = report['status']
        report['status'] = 'CONTROL_BUDGET_EXCEEDED'
    return report
