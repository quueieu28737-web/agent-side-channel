"""Collect E13 live tool RPCs, real ciphertext timings, and paired resource costs."""
import argparse
import asyncio
import ctypes
import datetime as dt
import math
import platform
import random
import ssl
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

from r6common import *
from transport import CELL, PAYLOAD, Endpoint, Relay, encode, now, until
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

async def session(e, cond, cfg, cal, tools, base, contexts, expected_state):
    backend = Backend(tools, base)
    connection = asyncio.get_running_loop().create_future()
    async def accept(reader, writer):
        connection.set_result((reader, writer))
    listener = await asyncio.start_server(accept, '127.0.0.1', 0, ssl=contexts[0], ssl_handshake_timeout=10)
    relay = Relay()
    port = await relay.start(listener.sockets[0].getsockname()[1])
    cr, cw = await asyncio.open_connection('127.0.0.1', port, ssl=contexts[1], server_hostname='localhost')
    sr, sw = await connection
    origin = now() + 5_000_000
    period = cfg['period_ns'].get(cond, 0)
    slots = cfg['tunnel_slots'] if period else 0
    padded = cond in ('padding', 'shadow_serial', 'shadow_parallel2')
    caps = cfg['caps'] if padded else {'req': 0, 'resp': 0}
    futures, requests, completions, response_matches = {}, [], [], []
    semaphore = asyncio.Semaphore(2 if cond == 'shadow_parallel2' else 1)
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
                    if cond == 'shadow_parallel2':
                        jobs.append(asyncio.create_task(call(extra, 'cover')))
                        await asyncio.sleep(0)
                    else:
                        await call(extra, 'cover')
                cover.observe(c['name'])
            await call(c, 'real')
        marks['flush_start_ns'] = now()
        if cond.startswith('shadow'):
            for c in cover.flush():
                if cond == 'shadow_parallel2':
                    jobs.append(asyncio.create_task(call(c, 'cover', True)))
                else:
                    await call(c, 'cover', True)
            if jobs:
                await asyncio.gather(*jobs)
        marks['driver_done_ns'] = now()
    status, error = 'complete', None
    driver = asyncio.create_task(drive())
    timeout = max(5.0, period*slots/1e9 + 0.25) if period else 10.0
    try:
        await asyncio.wait_for(driver, timeout)
        if period:
            await asyncio.gather(client.tx, server.tx)
            # Local send/drain completion does not prove that the remote TLS
            # endpoint consumed trailing dummy cells. Wait for both directions.
            await asyncio.wait_for(asyncio.gather(client.cells_complete.wait(),server.cells_complete.wait()),5)
    except Exception as ex:
        status, error = 'timeout' if isinstance(ex, TimeoutError) else 'error', repr(ex)
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
    result.update(condition=cond, status=status, error=error, source_episode_sha256=digest(e),
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
                  client_cells_received=client.cells_received,server_cells_received=server.cells_received,
                  wire_bytes=sum(n+5 for d,n,t in records),
                  scope='Live local tool RPCs driven by saved model actions; no model generation or WAN delay in the clock')
    return result

def source_hashes():
    return {n:sha(HERE/n) for n in ('r6common.py','transport.py','experiment.py')}

def freeze():
    rows, split, cal = inputs()
    train = [e for e in rows if e['task'] in split['train']]
    # Public training messages determine the common horizon, never test outcomes.
    budgets = []
    for e in train:
        budget = sum(math.ceil(len(encode(request(c,99,'real')))/PAYLOAD) +
                     math.ceil(len(encode({'id':99,'text':c['resp_text']}))/PAYLOAD) + 4 for c in e['calls'])
        budgets.append(budget)
    cfg = {'conditions':CONDITIONS, 'cell_bytes':CELL,
           'period_ns':{'tunnel_2ms':2_000_000,'tunnel_5ms':5_000_000},
           'tunnel_slots':max(128, math.ceil(1.5*max(budgets))+16),
           'horizon_rule':'max(128, ceil(1.5 * max_training_sum(request_cells + response_cells + 4 per real call)) + 16) slots',
           'max_training_slot_budget':max(budgets),
           'caps':{'req':cal['caps']['req']+256,'resp':cal['caps']['resp']+256},
           'cap_note':'Frozen R4 caps plus 256 bytes for encrypted RPC envelope; whole-cap overflow buckets',
           'calibration_sha256':sha(R4/'calibration.json'), 'split':split,
           'training_episodes':len(train), 'test_episodes':276,
           'training_episode_hashes':{key(e):digest(e) for e in train},
           'source_sha256':source_hashes(), 'seed':SEED,
           'clock':'perf_counter_ns; Windows timeBeginPeriod(1); observed scheduling lateness retained',
           'collection_order':'training before test; shuffled episodes and conditions with fixed seed; one session at a time',
           'revision':'v2: complete receive barrier; restore legacy size histograms and profiled tool-decoding attackers',
           'prior_measurement_status':'v1 retained under development/tail-drain-v1; two of 1380 tunnel captures lacked trailing dummy records. Entire cohort recollected, not selective replacement.',
           'attacks':{'views':['size_order','timing_direction','joint','flush_stripped_joint'],
                      'models':['majority','balanced_logistic_C1','gradient_boosting_100','random_forest_200_leaf2'],
                      'features':'directional size/gap quantiles, count, duration, burst thresholds .1/1/5/20 ms, first/last 32 positions, largest-gap segment; legacy request/response histograms and exchange sequence; profile decoder plus gboost/count-rule on non-tunnel conditions',
                      'detectors':'RF80 depth8 leaf5; per-record flush and per-request cover; 3-fold customer OOF training for segmentation',
                      'bootstrap':'2000 paired customer draws; retain tasks/repeats; reselect suite maximum; fitted-prediction conditional'},
           'interpretation':'Post hoc new measurements on the known R4 population. No new independent customers. No result-based threshold changes.',
           'created_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    if (HERE/'frozen.json').exists():
        oldcfg=read(HERE/'frozen.json')
        assert cfg['source_sha256']==oldcfg['source_sha256']
        return oldcfg
    write(HERE/'frozen.json',cfg)
    print(json.dumps({'frozen':sha(HERE/'frozen.json'),'slots':cfg['tunnel_slots'],
                      'horizons_ms':{k:v*cfg['tunnel_slots']/1e6 for k,v in cfg['period_ns'].items()}}),flush=True)
    return cfg

async def collect(partition, pilot=0):
    rows,split,cal=inputs(); ns,tools,base,tasks=lib.load()
    cfg=read(HERE/'frozen.json')
    assert cfg['source_sha256']==source_hashes(), 'Frozen collector changed'
    assert cfg['calibration_sha256']==sha(R4/'calibration.json')
    chosen=[e for e in rows if e['task'] in split[partition]]
    rng=random.Random(SEED+(partition=='test')); rng.shuffle(chosen)
    dest=HERE/'captures'/partition
    if pilot:
        assert partition=='train'
        chosen=chosen[:pilot]; dest=HERE/'pilot'
    elif partition=='test':
        receipt=read(HERE/'train_complete.json')
        assert receipt['count']==414*len(CONDITIONS) and receipt['frozen_sha256']==sha(HERE/'frozen.json')
    outputs=[]; t0=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='r6-tls-') as tmp:
        contexts=tlslab.make_contexts(Path(tmp),'1.2')
        for i,e in enumerate(chosen):
            state=lib.old.fast_clone(base)
            for c in e['calls']:
                assert invoke(tools,state,c)==c['resp_text'], 'Saved response differs from current tool execution'
            expected=digest(state)
            conditions=list(CONDITIONS); rng.shuffle(conditions)
            for cond in conditions:
                path=dest/f'{key(e)}-{cond}.json'
                if path.exists():
                    result=read(path)
                    assert result['frozen_sha256']==sha(HERE/'frozen.json')
                else:
                    result=await session(e,cond,cfg,cal,tools,base,contexts,expected)
                    result['frozen_sha256']=sha(HERE/'frozen.json')
                    write(path,result)
                outputs.append((path, result))
                if result['status']!='complete' or not result['response_equal'] or not result['db_equal']:
                    print('MEASUREMENT_FAILURE',path.name,result['status'],result['error'],flush=True)
            progress={'partition':partition,'episodes':i+1,'total_episodes':len(chosen),
                      'sessions':len(outputs),'elapsed_seconds':time.monotonic()-t0,
                      'updated_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
            write(HERE/('pilot_status.json' if pilot else 'collection_status.json'),progress)
            if pilot or (i+1)%10==0: print(json.dumps(progress),flush=True)
    receipt={'count':len(outputs),'frozen_sha256':sha(HERE/'frozen.json'),
             'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'failures':[p.name for p,r in outputs if r['status']!='complete' or not r['response_equal'] or not r['db_equal']],
             'files':{str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p,r in outputs},
             'runtime':{'python':platform.python_version(),'system':platform.system(),'release':platform.release(),
                        'machine':platform.machine(),'openssl':ssl.OPENSSL_VERSION}}
    write(HERE/('pilot_complete.json' if pilot else f'{partition}_complete.json'),receipt)
    print('COLLECTED',partition,len(outputs),'FAILURES',len(receipt['failures']),flush=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['freeze','train','test'])
    ap.add_argument('--pilot',type=int,default=0); a=ap.parse_args()
    if a.action=='freeze':freeze();return
    if platform.system()=='Windows':ctypes.windll.winmm.timeBeginPeriod(1)
    try:asyncio.run(collect(a.action,a.pilot))
    finally:
        if platform.system()=='Windows':ctypes.windll.winmm.timeEndPeriod(1)

if __name__=='__main__':main()
