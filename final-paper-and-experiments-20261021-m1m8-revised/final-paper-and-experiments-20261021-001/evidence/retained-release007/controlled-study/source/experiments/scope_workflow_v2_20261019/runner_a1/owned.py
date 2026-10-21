"""New bounded 80h controller; reuses pinned Job/identity/drain primitives.

No machine-wide enumeration or PID-based termination. Startup work is gated
until owned membership, retained handle, creation time and command are verified.
Uninterruptible native calls, OS/power/filesystem failures are not certified.
"""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import time

from dependencies import core, prior

MAX_BUDGET = 288000


def control_ok(r):
    return (r.get('status') == 'EXIT_ZERO' and r.get('reap_confirmed') is True
            and r.get('process_control_within_budget') is True
            and r.get('final_accounting', {}).get('active_processes') == 0
            and r.get('identity_failures_observed', 0) == 0
            and not r.get('owned_job_termination_requested'))


def run_owned(argv, out, *, budget_s, cleanup_reserve_s, identity_api_factory=None):
    if (type(budget_s) not in (int, float) or not 5 < cleanup_reserve_s < budget_s
            or not budget_s <= MAX_BUDGET):
        raise ValueError('invalid_finite_owned_budget')
    out = Path(out)
    began = time.monotonic()
    deadline = began + budget_s
    work_deadline = deadline - cleanup_reserve_s
    r = {'status': 'STARTING', 'budget_s': budget_s, 'cleanup_reserve_s': cleanup_reserve_s,
         'gate_released': False, 'job_assigned': False, 'reap_confirmed': False,
         'root_returncode': None, 'model_service_terminated': False,
         'identity_binding': 'job_membership_retained_handle_creation_image_full_command',
         'identity_sampling_limit': 'short-lived members can be missed; missing identity is not invented'}
    process = job = tracker = None
    last_signature = None
    with contextlib.ExitStack() as stack:
        stdout = stack.enter_context((out / 'watchdog.stdout.raw').open('xb'))
        stderr = stack.enter_context((out / 'watchdog.stderr.raw').open('xb'))
        journal = stack.enter_context((out / 'identity-timeline.jsonl').open('xb'))

        def observe(stage, strict=True):
            nonlocal last_signature
            snap = tracker.snapshot(stage)
            signature = [(v['pid'], v['creation_filetime_100ns'], v['image_path'], v['command_line'],
                          v['exit_code'], v['exit_utc'], len(v['identity_errors'])) for v in snap['history']]
            signature += [('failures', len(snap['failures']), 'gaps', len(snap['observability_gaps']))]
            if signature != last_signature or stage != 'during_work':
                journal.write((json.dumps(snap, ensure_ascii=True) + '\n').encode())
                journal.flush()
                os.fsync(journal.fileno())
                last_signature = signature
            r['identity_failures_observed'] = len(snap['failures'])
            r['identity_observability_gaps'] = len(snap['observability_gaps'])
            if strict and not snap['diagnostic_pass']:
                raise RuntimeError('owned_identity_capture_failed_closed')
            return snap

        try:
            job = core.watchdog.OwnedJob()
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
            r['root_pid'] = process.pid
            job.assign(process)
            r['job_assigned'] = True
            tracker = prior.identity.IdentityTracker(job, api=identity_api_factory() if identity_api_factory else None)
            tracker.set_query_deadline(work_deadline)
            first = observe('root_assigned_before_gate')
            root = next((v for v in first['history'] if v['pid'] == process.pid), None)
            if (root is None or root['creation_filetime_100ns'] == 'NR'
                    or root['command_line'] != subprocess.list2cmdline([str(a) for a in argv])
                    or os.path.normcase(os.path.normpath(root['image_path'])) != os.path.normcase(os.path.normpath(argv[0]))):
                raise RuntimeError('gated_root_identity_mismatch')
            r['root_identity'] = root
            r['initial_accounting'] = job.accounting()
            if time.monotonic() >= work_deadline:
                raise TimeoutError('startup_exhausted_work_budget')
            process.stdin.write((json.dumps({'protocol': 'owned-job-gate-v1', 'work_deadline': work_deadline}) + '\n').encode())
            process.stdin.flush()
            process.stdin.close()
            r['gate_released'] = True
            while True:
                observe('during_work')
                code = process.poll()
                if code is not None:
                    r['status'] = 'EXIT_ZERO' if code == 0 else 'CHILD_EXIT_ERROR'
                    r['root_exit_observed'] = prior.identity.stamp()
                    observe('root_exited')
                    if code == 0:
                        r['natural_drain'] = prior.bounded_drain(job, observe, deadline)
                    break
                if time.monotonic() >= work_deadline:
                    raise TimeoutError('owned_work_deadline')
                time.sleep(min(.02, max(0, work_deadline - time.monotonic())))
        except TimeoutError as exc:
            r.update(status='DEADLINE', error=repr(exc))
        except BaseException as exc:
            r.update(status='SUPERVISION_ERROR', error=repr(exc))
        finally:
            try:
                if process is not None and process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if job is not None and r['job_assigned']:
                    if tracker is not None:
                        observe('pre_cleanup', strict=False)
                    r['pre_cleanup_accounting'] = job.accounting()
                    if r['pre_cleanup_accounting']['active_processes']:
                        if r['status'] == 'EXIT_ZERO':
                            r['status'] = 'RESIDUAL_CHILDREN_TERMINATED'
                        r['owned_job_termination_requested'] = prior.identity.stamp()
                        job.terminate()
                    while True:
                        remaining = job.accounting()
                        if remaining['active_processes'] == 0:
                            r['reap_confirmed'] = True
                            break
                        if time.monotonic() >= deadline:
                            break
                        time.sleep(min(.02, max(0, deadline - time.monotonic())))
                    r['final_accounting'] = remaining
                    if tracker is not None:
                        r['final_identity_snapshot'] = observe('after_cleanup', strict=False)
                        if tracker.failures and r['status'] == 'EXIT_ZERO':
                            r['status'] = 'IDENTITY_FAILURE'
                elif process is not None:
                    # Gate was never released. Only this owned root can be killed.
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    r['reap_confirmed'] = process.poll() is not None
                if process is not None:
                    process.wait(timeout=max(.01, deadline - time.monotonic()))
                    r['root_returncode'] = process.returncode
            except BaseException as exc:
                r.update(cleanup_error=repr(exc), reap_confirmed=False)
            finally:
                for resource, label in ((tracker, 'identity_handles'), (job, 'owned_job')):
                    if resource is not None:
                        try:
                            resource.close()
                        except BaseException as exc:
                            r.update({label + '_close_error': repr(exc), 'reap_confirmed': False})
                if process is not None:
                    try:
                        process.wait(timeout=max(.01, deadline - time.monotonic()))
                        r['root_returncode'] = process.returncode
                    except BaseException as exc:
                        r.update(root_reap_error=repr(exc), reap_confirmed=False)
            if not r['reap_confirmed']:
                r['status_before_unconfirmed_reap'] = r['status']
                r['status'] = 'REAP_UNCONFIRMED'
    r['process_control_elapsed_s'] = time.monotonic() - began
    r['process_control_within_budget'] = r['process_control_elapsed_s'] <= budget_s
    if not r['process_control_within_budget']:
        r['status_before_budget_exceeded'] = r['status']
        r['status'] = 'CONTROL_BUDGET_EXCEEDED'
    return r
