"""Collect Exp 4 WAN extension: live tool RPCs under tc netem 20ms/50ms delay and 5ms/10ms jitter."""
import argparse
import asyncio
import ctypes
import datetime as dt
import math
import os
import platform
import random
import ssl
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

from r13common import *
from transport import CELL, PAYLOAD, Endpoint, NetemRelay, encode, now, until
import tlslab

class Cover:
    """Prefix-only R4 policy; decisions never read future real calls."""
    def __init__(self, e, cal):
        self.cal = cal
        self.rng = random.Random(20261021 + e['task']*100003 + e['repeat']*7919 + (e['prompt']=='rules')*13)
        self.seen, self.emitted = Counter(), Counter()
        self.pools = {v: [d for d in ds if d['user'] != e['user']] for v, ds in cal['donors'].items()}

    def deficits(self):
        return {v: n-self.seen[v]-self.emitted[v] for v,n in self.cal['template'].items()
                if n > self.seen[v]+self.emitted[v]}

    def make(self, name):
        donor = self.rng.choice(self.pools[name])
        self.emitted[name] += 1
        return {'name': name, 'kwargs': donor['kwargs'], 'donor_task': donor['task']}

    def before(self):
        d = self.deficits()
        if d and self.rng.random() < self.cal['shape_emit_probability']:
            return self.make(self.rng.choices(list(d), weights=list(d.values()))[0])
        return None

    def observe(self, name):
        self.seen[name] += 1

    def flush(self):
        rest = [v for v,n in self.deficits().items() for _ in range(n)]
        self.rng.shuffle(rest)
        return [self.make(v) for v in rest]

class Backend:
    def __init__(self, tools, base):
        self.tools = tools
        self.live, self.shadow = lib.old.fast_clone(base), lib.old.fast_clone(base)
        self.locks = {'real': threading.Lock(), 'cover': threading.Lock()}
        self.events = []

    def execute(self, req, received_ns):
        enqueued = now()
        with self.locks[req['kind']]:
            start = now()
            data = self.live if req['kind'] == 'real' else self.shadow
            text = invoke(self.tools, data, req)
            if not isinstance(text, str):
                text = json.dumps(text)
            end = now()
            self.events.append({'id': req['id'], 'kind': req['kind'], 'name': req['name'],
                                'received_ns': received_ns, 'enqueued_ns': enqueued,
                                'start_ns': start, 'end_ns': end, 'response_sha256': digest(text)})
        return text

async def session(e, cond, profile_key, profile_cfg, cfg, cal, tools, base, contexts, expected_state):
    backend = Backend(tools, base)
    connection = asyncio.get_running_loop().create_future()
    async def accept(reader, writer):
        connection.set_result((reader, writer))
    listener = await asyncio.start_server(accept, '127.0.0.1', 0, ssl=contexts[0], ssl_handshake_timeout=15)
    
    relay_seed = SEED + e['task']*1009 + e['repeat']*37 + (1 if profile_key=='wan_50ms' else 0)*997
    relay = NetemRelay(profile_cfg['delay_ms'], profile_cfg['jitter_ms'], seed=relay_seed)
    port = await relay.start(listener.sockets[0].getsockname()[1])
    cr, cw = await asyncio.open_connection('127.0.0.1', port, ssl=contexts[1], server_hostname='localhost')
    sr, sw = await connection
    
    origin = now() + 10_000_000
    period = cfg['period_ns'].get(cond, 0)
    slots = cfg['tunnel_slots'] if period else 0
    padded = cond in ('padding', 'shadow_serial')
    caps = cfg['caps'] if padded else {'req': 0, 'resp': 0}
    futures, requests, completions, response_matches = {}, [], [], []
    semaphore = asyncio.Semaphore(1)
    
    async def handle_response(obj, stamp):
        completions.append({'id': obj['id'], 'time_ns': stamp})
        if obj['id'] in futures and not futures[obj['id']].done():
            futures[obj['id']].set_result(obj['text'])
            
    async def handle_request(obj, stamp):
        text = await asyncio.to_thread(backend.execute, obj, stamp)
        server.send({'id': obj['id'], 'text': text})
        
    client = Endpoint(cr, cw, handle_response, origin, period, slots, caps['req'])
    server = Endpoint(sr, sw, handle_request, origin, period, slots, caps['resp'])
    client.start(); server.start()
    marks = {'last_real_ns': origin, 'flush_start_ns': None}
    
    async def call(c, kind, is_flush=False):
        queued = now()
        async with semaphore:
            mid = len(requests)
            req = request(c, mid, kind)
            futures[mid] = asyncio.get_running_loop().create_future()
            requests.append({'id': mid, 'kind': kind, 'name': c['name'], 'flush': is_flush,
                             'queued_ns': queued, 'released_ns': now(),
                             'request_sha256': digest(req)})
            client.send(req)
            text = await futures[mid]
            if kind == 'real':
                response_matches.append(text == c['resp_text'])
                marks['last_real_ns'] = now()
            return text
            
    async def drive():
        await until(origin)
        cover = Cover(e, cal)
        jobs = []
        for c in e['calls']:
            if cond.startswith('shadow'):
                extra = cover.before()
                if extra:
                    await call(extra, 'cover')
                cover.observe(c['name'])
            await call(c, 'real')
        marks['flush_start_ns'] = now()
        if cond.startswith('shadow'):
            for c in cover.flush():
                await call(c, 'cover', True)
        marks['driver_done_ns'] = now()
        
    status, error = 'complete', None
    driver = asyncio.create_task(drive())
    
    if not period:
        total_calls = len(e['calls']) + 30
        est_delay = (profile_cfg['delay_ms'] * 2 * total_calls) / 1000.0
        timeout = max(15.0, est_delay + 5.0)
        try:
            await asyncio.wait_for(driver, timeout)
        except Exception as ex:
            status, error = 'timeout' if isinstance(ex, TimeoutError) else 'error', repr(ex)
    else:
        tunnel_sec = slots * period / 1e9
        wan_margin = max(0.5, (profile_cfg['delay_ms'] * 3) / 1000.0)
        max_wait = tunnel_sec + wan_margin + 0.2
        cell_task = asyncio.create_task(client.cells_complete.wait())
        done, pending = await asyncio.wait([driver, cell_task], timeout=max_wait, return_when=asyncio.FIRST_COMPLETED)
        if driver in done:
            status = 'complete'
            await asyncio.gather(client.tx, server.tx)
            await asyncio.wait_for(asyncio.gather(client.cells_complete.wait(), server.cells_complete.wait()), 5)
        else:
            status = 'horizon_exhausted'
            error = f"Horizon exhausted: {len(response_matches)}/{len(e['calls'])} calls completed within {slots} slots ({tunnel_sec*1000:.0f}ms)"
            driver.cancel()
            await asyncio.gather(driver, return_exceptions=True)
            
    finish = now()
    await client.stop(); await server.stop()
    listener.close(); await listener.wait_closed(); await relay.close()
    
    records = sorted([r for r in relay.records if r[2] >= origin], key=lambda r:r[2])
    for r in records:
        r[2] -= origin
        
    def relative(items):
        return [{k:(v-origin if k.endswith('_ns') and v is not None else v) for k,v in item.items()} for item in items]
        
    result = {k:e[k] for k in ('task','prompt','repeat','user','has_cancel','has_return','native_reward','status')}
    result['original_status'] = result.pop('status')
    result.update(condition=cond, wan_profile=profile_key,
                  wan_delay_ms=profile_cfg['delay_ms'], wan_jitter_ms=profile_cfg['jitter_ms'],
                  status=status, error=error, source_episode_sha256=digest(e),
                  start_utc=dt.datetime.now(dt.timezone.utc).isoformat(), origin_clock_ns=origin,
                  records=records, chunks=[[d,n,t-origin] for d,n,t in relay.chunks if t>=origin],
                  requests=relative(requests), completions=relative(completions),
                  backend=relative(backend.events), client_send=relative(client.sent), server_send=relative(server.sent),
                  marks={k:(v-origin if v is not None else None) for k,v in marks.items()},
                  finish_ns=finish-origin, response_equal=all(response_matches) and len(response_matches)==len(e['calls']),
                  real_calls_expected=len(e['calls']), real_calls_completed=len(response_matches),
                  db_equal=digest(backend.live)==expected_state, final_state_sha256=digest(backend.live),
                  max_client_queue_bytes=client.max_pending_bytes, max_server_queue_bytes=server.max_pending_bytes,
                  pending_bytes_at_end=client.pending_bytes+server.pending_bytes,
                  period_ns=period, slots=slots, cell_bytes=CELL if period else None,
                  client_cells_received=client.cells_received, server_cells_received=server.cells_received,
                  wire_bytes=sum(n+5 for d,n,t in records),
                  scope=f"WAN netem emulation: delay {profile_cfg['delay_ms']}ms, jitter {profile_cfg['jitter_ms']}ms, local real tool execution")
    return result

def source_hashes():
    return {n:sha(HERE/n) for n in ('r13common.py','transport.py','experiment.py') if (HERE/n).exists()}

async def collect_profile(profile_key, limit=0):
    rows, split, cal = inputs()
    ns, tools, base, tasks = lib.load()
    cfg = read(R6 / 'frozen.json')
    profile_cfg = WAN_PROFILES[profile_key]
    
    test_episodes = [e for e in rows if e['task'] in split['test']]
    if limit:
        test_episodes = test_episodes[:limit]
        
    dest = HERE / 'captures' / profile_key
    dest.mkdir(parents=True, exist_ok=True)
    
    outputs = []
    t0 = time.monotonic()
    print(f"Starting collection for {profile_key} ({profile_cfg['name']}): {len(test_episodes)} episodes x {len(CONDITIONS)} conditions = {len(test_episodes)*len(CONDITIONS)} sessions")
    
    with tempfile.TemporaryDirectory(prefix=f'r13-tls-{profile_key}-') as tmp:
        contexts = tlslab.make_contexts(Path(tmp), '1.2')
        for i, e in enumerate(test_episodes):
            state = lib.old.fast_clone(base)
            for c in e['calls']:
                assert invoke(tools, state, c) == c['resp_text'], 'Saved response differs from current tool execution'
            expected = digest(state)
            
            for cond in CONDITIONS:
                path = dest / f"{key(e)}-{cond}.json"
                if path.exists():
                    result = read(path)
                else:
                    result = await session(e, cond, profile_key, profile_cfg, cfg, cal, tools, base, contexts, expected)
                    write(path, result)
                outputs.append((path, result))
                if result['status'] != 'complete' and cond != 'tunnel_2ms':
                    print('UNEXPECTED_FAILURE', path.name, result['status'], result['error'], flush=True)
                    
            if (i + 1) % 10 == 0 or (i + 1) == len(test_episodes):
                elapsed = time.monotonic() - t0
                rate = len(outputs) / elapsed if elapsed > 0 else 0
                progress = {'profile': profile_key, 'episodes_completed': i + 1, 'total_episodes': len(test_episodes),
                            'sessions': len(outputs), 'elapsed_seconds': round(elapsed, 1),
                            'sessions_per_sec': round(rate, 2),
                            'updated_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
                write(HERE / f"status_{profile_key}.json", progress)
                print(f"[{profile_key}] Episodes: {i+1}/{len(test_episodes)} | Sessions: {len(outputs)} | Elapsed: {elapsed:.1f}s ({rate:.2f} sess/s)", flush=True)

    receipt = {'count': len(outputs),
               'wan_profile': profile_key,
               'delay_ms': profile_cfg['delay_ms'],
               'jitter_ms': profile_cfg['jitter_ms'],
               'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'failures': [p.name for p, r in outputs if r['status'] != 'complete'],
               'files': {str(p.relative_to(HERE)).replace('\\', '/'): sha(p) for p, r in outputs},
               'runtime': {'python': platform.python_version(), 'system': platform.system(),
                           'release': platform.release(), 'machine': platform.machine(),
                           'openssl': ssl.OPENSSL_VERSION}}
    write(HERE / f"{profile_key}_complete.json", receipt)
    print(f"COMPLETED {profile_key}: {len(outputs)} sessions. Incomplete/Horizon-exhausted: {len(receipt['failures'])}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', choices=['wan_20ms', 'wan_50ms', 'all'], default='all')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    
    if platform.system() == 'Windows':
        ctypes.windll.winmm.timeBeginPeriod(1)
    try:
        profiles = ['wan_20ms', 'wan_50ms'] if args.profile == 'all' else [args.profile]
        for p in profiles:
            asyncio.run(collect_profile(p, args.limit))
    finally:
        if platform.system() == 'Windows':
            ctypes.windll.winmm.timeEndPeriod(1)

if __name__ == '__main__':
    main()
