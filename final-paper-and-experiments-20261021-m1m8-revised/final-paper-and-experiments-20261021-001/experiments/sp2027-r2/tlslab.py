"""Loopback TLS harness for E5 (streaming emitter) and E7 (agent-tool link).

A transparent relay sits between client and server and records every byte in
arrival order together with its direction. Only records sent after the
handshake are attributed to the application, so TLS 1.3 encrypted handshake
messages (outer type 23) are never counted as application data.
No external network, model API or production service is contacted.
"""
import datetime as dt
import socket
import ssl
import struct
import threading
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def make_contexts(cert_dir: Path, version: str):
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_p, key_p = cert_dir / "cert.pem", cert_dir / "key.pem"
    if not cert_p.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
        now = dt.datetime.now(dt.timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - dt.timedelta(minutes=5))
                .not_valid_after(now + dt.timedelta(days=2))
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
                .sign(key, hashes.SHA256()))
        cert_p.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_p.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                            serialization.PrivateFormat.PKCS8,
                                            serialization.NoEncryption()))
    srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cli = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    cli.load_verify_locations(cafile=str(cert_p))
    srv.load_cert_chain(str(cert_p), str(key_p))
    v = {"1.2": ssl.TLSVersion.TLSv1_2, "1.3": ssl.TLSVersion.TLSv1_3}[version]
    for ctx in (srv, cli):
        ctx.minimum_version = v
        ctx.maximum_version = v
        if version == "1.2":
            ctx.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256")
    srv.num_tickets = 0  # no post-handshake NewSessionTicket records
    return srv, cli


def parse_records(raw: bytes):
    out, i = [], 0
    while i + 5 <= len(raw):
        typ = raw[i]
        ln = struct.unpack("!H", raw[i + 3:i + 5])[0]
        if i + 5 + ln > len(raw):
            break
        out.append((typ, ln))
        i += 5 + ln
    return out, i


class _Relay:
    """Byte-transparent relay. log holds (direction, bytes) in forwarding order."""

    def __init__(self, srv_port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.srv_port = srv_port
        self.lock = threading.Lock()
        self.log = []
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        c, _ = self.sock.accept()
        s = socket.create_connection(("127.0.0.1", self.srv_port), timeout=10)

        def fwd(src, dst, tag):
            try:
                while True:
                    d = src.recv(65536)
                    if not d:
                        break
                    with self.lock:
                        self.log.append((tag, d))
                    dst.sendall(d)
            except OSError:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        a = threading.Thread(target=fwd, args=(c, s, "c2s"))
        b = threading.Thread(target=fwd, args=(s, c, "s2c"))
        a.start(); b.start(); a.join(); b.join()
        c.close(); s.close(); self.sock.close()

    def mark(self):
        with self.lock:
            return len(self.log)


def _app_records(log, marker):
    """Application records per direction after the marker, in global order."""
    buf = {"c2s": b"", "s2c": b""}
    for tag, d in log[:marker]:
        buf[tag] += d
    # Discard complete handshake-phase records; keep any partial tail.
    for tag in buf:
        _, used = parse_records(buf[tag])
        buf[tag] = buf[tag][used:]
    seq = []
    for tag, d in log[marker:]:
        buf[tag] += d
        recs, used = parse_records(buf[tag])
        buf[tag] = buf[tag][used:]
        seq.extend((tag, ln) for typ, ln in recs if typ == 23)
    return seq


def run_stream(srv_ctx, cli_ctx, events):
    """Server writes each event with one sendall after the client's GO."""
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.bind(("127.0.0.1", 0)); ss.listen(1)
    relay = _Relay(ss.getsockname()[1])
    state = {}

    def server():
        conn, _ = ss.accept()
        with srv_ctx.wrap_socket(conn, server_side=True) as t:
            t.recv(16)
            state["marker"] = relay.mark()
            state["cipher"] = t.cipher()[0]
            state["version"] = t.version()
            for e in events:
                t.sendall(e)
        ss.close()

    th = threading.Thread(target=server); th.start()
    chunks = []
    raw = socket.create_connection(("127.0.0.1", relay.port), timeout=10)
    with cli_ctx.wrap_socket(raw, server_hostname="localhost") as t:
        t.sendall(b"GO")
        while True:
            d = t.recv(65536)
            if not d:
                break
            chunks.append(d)
    th.join(); relay.thread.join()
    seq = [ln for tag, ln in _app_records(relay.log, state["marker"]) if tag == "s2c"]
    return {"record_payloads": seq, "received": b"".join(chunks),
            "cipher": state["cipher"], "version": state["version"]}


def run_session(srv_ctx, cli_ctx, exchanges):
    """Request/response session. exchanges = [(request_bytes, response_bytes)].
    Each message is length-prefixed so the receiver knows where it ends."""
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.bind(("127.0.0.1", 0)); ss.listen(1)
    relay = _Relay(ss.getsockname()[1])
    state = {}

    def recv_msg(t):
        hdr = b""
        while len(hdr) < 4:
            d = t.recv(4 - len(hdr))
            if not d:
                return None
            hdr += d
        n = struct.unpack("!I", hdr)[0]
        body = b""
        while len(body) < n:
            body += t.recv(min(65536, n - len(body)))
        return body

    def server():
        conn, _ = ss.accept()
        with srv_ctx.wrap_socket(conn, server_side=True) as t:
            assert recv_msg(t) == b"GO"
            state["marker"] = relay.mark()
            t.sendall(struct.pack("!I", 2) + b"OK")  # first s2c app record; dropped below
            for _req, resp in exchanges:
                recv_msg(t)
                t.sendall(struct.pack("!I", len(resp)) + resp)
        ss.close()

    th = threading.Thread(target=server); th.start()
    got = []
    raw = socket.create_connection(("127.0.0.1", relay.port), timeout=10)
    with cli_ctx.wrap_socket(raw, server_hostname="localhost") as t:
        t.sendall(struct.pack("!I", 2) + b"GO")
        assert recv_msg(t) == b"OK"
        for req, _resp in exchanges:
            t.sendall(struct.pack("!I", len(req)) + req)
            got.append(recv_msg(t))
    th.join(); relay.thread.join()
    assert got == [r for _q, r in exchanges]
    seq = _app_records(relay.log, state["marker"])
    assert seq[0][0] == "s2c"
    return seq[1:]
