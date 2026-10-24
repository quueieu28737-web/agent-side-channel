"""Real TLS sockets with netem WAN delay, jitter, and timestamped ciphertext relay."""
import asyncio
import json
import random
import socket
import struct
import time

CELL = 4096
PAYLOAD = CELL - 4
now = time.perf_counter_ns

def encode(obj, cap=0):
    raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode()
    body = struct.pack('!I', len(raw)) + raw
    size = max(len(body), cap)
    if cap and size > cap:
        size = ((size + cap - 1) // cap) * cap
    return struct.pack('!I', size) + body + bytes(size - len(body))

def decode(body):
    n = struct.unpack('!I', body[:4])[0]
    return json.loads(body[4:4+n])

def nodelay(writer):
    writer.get_extra_info('socket').setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

async def until(deadline_ns):
    while (left := (deadline_ns - now()) / 1e9) > 0:
        await asyncio.to_thread(time.sleep, left)

class NetemRelay:
    def __init__(self, delay_ms=0.0, jitter_ms=0.0, seed=20261024):
        self.delay_ns = int(delay_ms * 1_000_000)
        self.jitter_ns = int(jitter_ms * 1_000_000)
        self.rng = random.Random(seed)
        self.records = []
        self.chunks = []
        self.writers = []
        self.task = None

    async def start(self, port):
        self.target = port
        self.listener = await asyncio.start_server(self.accept, '127.0.0.1', 0)
        return self.listener.sockets[0].getsockname()[1]

    async def accept(self, cr, cw):
        self.task = asyncio.current_task()
        sr, sw = await asyncio.open_connection('127.0.0.1', self.target)
        nodelay(cw); nodelay(sw)
        self.writers.extend([cw, sw])

        async def forward(reader, writer, direction):
            buf = bytearray()
            last_delivery_ns = 0
            queue = asyncio.Queue()

            async def deliver():
                try:
                    while True:
                        item = await queue.get()
                        if item is None:
                            break
                        delivery_ns, data = item
                        await until(delivery_ns)
                        writer.write(data)
                        await writer.drain()
                        queue.task_done()
                except (ConnectionError, OSError):
                    pass

            deliver_task = asyncio.create_task(deliver())

            try:
                while data := await reader.read(65536):
                    arrival_ts = now()
                    if self.delay_ns > 0:
                        jitter = self.rng.uniform(-self.jitter_ns, self.jitter_ns) if self.jitter_ns else 0.0
                        delivery_ts = arrival_ts + self.delay_ns + int(jitter)
                        delivery_ts = max(delivery_ts, last_delivery_ns)
                        last_delivery_ns = delivery_ts
                    else:
                        delivery_ts = arrival_ts

                    self.chunks.append([direction, len(data), delivery_ts])
                    buf.extend(data)
                    while len(buf) >= 5:
                        size = int.from_bytes(buf[3:5], 'big')
                        if len(buf) < size + 5:
                            break
                        typ = buf[0]
                        if typ == 23:
                            self.records.append([direction, size, delivery_ts])
                        del buf[:size+5]

                    if self.delay_ns > 0:
                        await queue.put((delivery_ts, data))
                    else:
                        writer.write(data)
                        await writer.drain()
            except (ConnectionError, OSError):
                pass
            finally:
                if self.delay_ns > 0:
                    await queue.put(None)
                    await deliver_task
                writer.close()

        await asyncio.gather(forward(cr, sw, 1), forward(sr, cw, -1))

    async def close(self):
        self.listener.close()
        await self.listener.wait_closed()
        for writer in self.writers:
            writer.close()
        if self.task:
            try:
                await asyncio.wait_for(self.task, 5)
            except (asyncio.TimeoutError, Exception):
                pass

class Endpoint:
    def __init__(self, reader, writer, handler, origin, period_ns=0, slots=0, cap=0):
        self.reader, self.writer, self.handler = reader, writer, handler
        nodelay(writer)
        self.origin, self.period, self.slots, self.cap = origin, period_ns, slots, cap
        self.queue = asyncio.Queue()
        self.sent = []
        self.received = []
        self.pending_bytes = 0
        self.max_pending_bytes = 0
        self.handlers = set()
        self.cells_received = 0
        self.cells_complete = asyncio.Event()

    def start(self):
        self.rx = asyncio.create_task(self.receive())
        self.tx = asyncio.create_task(self.transmit())

    def send(self, obj):
        blob = encode(obj, self.cap)
        self.pending_bytes += len(blob)
        self.max_pending_bytes = max(self.max_pending_bytes, self.pending_bytes)
        self.queue.put_nowait((blob, obj['id']))

    async def transmit(self):
        await until(self.origin)
        if not self.period:
            while True:
                blob, mid = await self.queue.get()
                ts = now()
                self.writer.write(blob)
                await self.writer.drain()
                self.pending_bytes -= len(blob)
                self.sent.append({'id': mid, 'time_ns': ts, 'bytes': len(blob)})
        else:
            buf = bytearray()
            for slot in range(self.slots):
                deadline = self.origin + slot * self.period
                await until(deadline)
                while not self.queue.empty():
                    blob, _mid = self.queue.get_nowait()
                    buf.extend(blob)
                n = min(PAYLOAD, len(buf))
                cell = struct.pack('!I', n) + buf[:n] + bytes(PAYLOAD-n)
                del buf[:n]
                ts = now()
                self.writer.write(cell)
                await self.writer.drain()
                self.pending_bytes -= n
                self.sent.append({'slot': slot, 'time_ns': ts, 'deadline_ns': deadline,
                                  'useful_bytes': n, 'bytes': CELL})
            await until(self.origin + self.slots * self.period)

    async def receive(self):
        buf = bytearray()
        try:
            while True:
                if self.period:
                    cell = await self.reader.readexactly(CELL)
                    self.cells_received += 1
                    n = struct.unpack('!I', cell[:4])[0]
                    assert n <= PAYLOAD
                    buf.extend(cell[4:4+n])
                else:
                    hdr = await self.reader.readexactly(4)
                    n = struct.unpack('!I', hdr)[0]
                    buf.extend(hdr + await self.reader.readexactly(n))
                while len(buf) >= 4:
                    size = struct.unpack('!I', buf[:4])[0]
                    if len(buf) < size + 4:
                        break
                    obj = decode(buf[4:4+size]); del buf[:4+size]
                    ts = now()
                    self.received.append({'id': obj['id'], 'time_ns': ts})
                    task = asyncio.create_task(self.handler(obj, ts))
                    self.handlers.add(task)
                    task.add_done_callback(self.handlers.discard)
                if self.period and self.cells_received == self.slots:
                    self.cells_complete.set()
        except (asyncio.IncompleteReadError, ConnectionError):
            return

    async def stop(self):
        for task in (self.tx, self.rx):
            if not task.done():
                task.cancel()
        await asyncio.gather(self.tx, self.rx, return_exceptions=True)
        if self.handlers:
            await asyncio.gather(*self.handlers)
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except (OSError, ConnectionError):
            pass
