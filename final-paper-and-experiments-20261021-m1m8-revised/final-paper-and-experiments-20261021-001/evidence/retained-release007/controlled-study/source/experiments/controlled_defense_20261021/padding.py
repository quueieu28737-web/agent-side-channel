"""E1: two real TLS links, receiver re-chunking, and padding placement.

Only localhost sockets are opened. The model collection is a separate operation;
this module replays the exact saved UTF-8 output in three predeclared arms.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import random
import socket
import ssl
import statistics
import struct
import threading
import time
import traceback
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

SEED = 20261021
ARMS = ("NONE", "UPSTREAM_PAD", "END_TO_END_PAD")
PAD_FRAMES = 16
PAD_FRAME_BYTES = 1024
PLAIN_FRAME_BYTES = 128
PAD_CAPACITY = PAD_FRAMES * PAD_FRAME_BYTES
SOCKET_TIMEOUT = 8.0
BOOTSTRAPS = 5000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def encode_message(text: str, padded: bool) -> list[bytes]:
    body = text.encode("utf-8")
    message = struct.pack("!I", len(body)) + body
    if len(message) > PAD_CAPACITY:
        raise ValueError("padding overflow: retain failed output, never truncate")
    if padded:
        message += b"\x00" * (PAD_CAPACITY - len(message))
    size = PAD_FRAME_BYTES if padded else PLAIN_FRAME_BYTES
    return [message[i:i + size] for i in range(0, len(message), size)]


def decode_message(message: bytes, padded: bool) -> str:
    if len(message) < 4:
        raise ValueError("missing encrypted application length")
    length = struct.unpack("!I", message[:4])[0]
    if length > PAD_CAPACITY - 4 or length > len(message) - 4:
        raise ValueError("invalid encrypted application length")
    if padded:
        if len(message) != PAD_CAPACITY or any(message[4 + length:]):
            raise ValueError("invalid fixed padding")
    elif len(message) != 4 + length:
        raise ValueError("unexpected unpadded application bytes")
    return message[4:4 + length].decode("utf-8", errors="strict")


def listener() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    sock.settimeout(SOCKET_TIMEOUT)
    return sock


def certificate(directory: Path) -> tuple[Path, Path]:
    """Ephemeral self-signed certificate, valid only for loopback names."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - dt.timedelta(minutes=5))
            .not_valid_after(now + dt.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
            .sign(key, hashes.SHA256()))
    directory.mkdir(parents=True, exist_ok=True)
    cert_path, key_path = directory / "localhost-cert.pem", directory / "localhost-key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                          serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    return cert_path, key_path


def contexts(cert_path: Path, key_path: Path) -> tuple[ssl.SSLContext, ssl.SSLContext]:
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client.load_verify_locations(cafile=str(cert_path))
    server.load_cert_chain(str(cert_path), str(key_path))
    for context in (server, client):
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256")
        context.options |= ssl.OP_NO_TICKET
    return server, client


class Worker:
    """Non-daemon worker; every exception is retained and every thread joined."""

    def __init__(self, name, fn):
        self.error = None
        self.result = None

        def target():
            try:
                self.result = fn()
            except BaseException:
                self.error = traceback.format_exc()

        self.thread = threading.Thread(target=target, name=name, daemon=False)

    def start(self):
        self.thread.start()
        return self

    def join(self):
        self.thread.join(SOCKET_TIMEOUT + 2)
        if self.thread.is_alive():
            raise RuntimeError("owned socket worker failed bounded closure: " + self.thread.name)
        return self


class Tee:
    """Transparent TCP relay: records only bytes actually read from sockets."""

    def __init__(self, listen: socket.socket, destination: int, prefix: Path):
        self.listen, self.destination, self.prefix = listen, destination, prefix
        self.streams = {"c2s": bytearray(), "s2c": bytearray()}
        self.chunks = {"c2s": [], "s2c": []}
        self.start_ns = time.monotonic_ns()
        self.worker = Worker("tee-" + prefix.name, self.run)
        self.pump_workers = []

    def run(self):
        try:
            with self.listen:
                incoming, _ = self.listen.accept()
            with incoming, socket.create_connection(("127.0.0.1", self.destination), SOCKET_TIMEOUT) as outgoing:
                incoming.settimeout(SOCKET_TIMEOUT)
                outgoing.settimeout(SOCKET_TIMEOUT)

                def pump(source, sink, direction):
                    while True:
                        data = source.recv(65536)
                        timestamp = time.monotonic_ns() - self.start_ns
                        if not data:
                            try:
                                sink.shutdown(socket.SHUT_WR)
                            except OSError:
                                pass
                            break
                        offset = len(self.streams[direction])
                        self.streams[direction].extend(data)
                        self.chunks[direction].append({"offset": offset, "length": len(data), "read_ns": timestamp})
                        sink.sendall(data)

                self.pump_workers = [Worker("pump-" + self.prefix.name + "-" + d,
                                            lambda a=a, b=b, d=d: pump(a, b, d)).start()
                                     for a, b, d in ((incoming, outgoing, "c2s"), (outgoing, incoming, "s2c"))]
                for worker in self.pump_workers:
                    worker.join()
                errors = [w.error for w in self.pump_workers if w.error]
                if errors:
                    raise RuntimeError("\n".join(errors))
        finally:
            self.prefix.parent.mkdir(parents=True, exist_ok=True)
            for direction in self.streams:
                self.prefix.with_name(self.prefix.name + "-" + direction + ".bin").write_bytes(self.streams[direction])
            write_json(self.prefix.with_name(self.prefix.name + "-reads.json"), self.chunks)

    def start(self):
        self.worker.start()
        return self

    def join(self):
        self.worker.join()
        if self.worker.error:
            raise RuntimeError(self.worker.error)

    def parsed(self):
        return {direction: parse_tls(bytes(stream), self.chunks[direction])
                for direction, stream in self.streams.items()}


def parse_tls(stream: bytes, reads: list[dict]) -> dict:
    """TLS1.2 record boundaries, independent of TCP segmentation.

    read_ns is receiver-local tee read time, not authenticated wire time.
    Handshake/CCS/alert records stay in raw captures but are excluded from the
    predeclared application-record size feature.
    """
    records, offset = [], 0
    while offset < len(stream):
        if len(stream) - offset < 5:
            raise ValueError("truncated TLS record header")
        kind, major, minor, size = struct.unpack("!BBBH", stream[offset:offset + 5])
        if major != 3 or kind not in (20, 21, 22, 23):
            raise ValueError("unexpected TLS record header")
        end = offset + 5 + size
        if end > len(stream):
            raise ValueError("truncated TLS record payload")
        matching = next((r for r in reads if r["offset"] + r["length"] >= end), None)
        records.append({"offset": offset, "type": kind, "version": [major, minor],
                        "payload_bytes": size, "wire_bytes": size + 5,
                        "tee_read_ns": matching["read_ns"] if matching else None})
        offset = end
    app = [r for r in records if r["type"] == 23]
    times = [r["tee_read_ns"] for r in app if r["tee_read_ns"] is not None]
    return {"records": records, "raw_bytes": len(stream), "sha256": sha(stream),
            "application_record_count": len(app),
            "application_payload_bytes": sum(r["payload_bytes"] for r in app),
            "application_wire_bytes": sum(r["wire_bytes"] for r in app),
            "application_first_to_last_read_ns": max(times) - min(times) if times else None}


def receive_tls(connection) -> bytes:
    parts = []
    while True:
        part = connection.recv(65536)
        if not part:
            return b"".join(parts)
        parts.append(part)


def send_frames(connection, frames):
    for frame in frames:
        connection.sendall(frame)
    # unwrap transmits close_notify, waits for its peer, and authenticates EOF.
    raw = connection.unwrap()
    raw.close()


def receive_and_close(connection):
    message = receive_tls(connection)
    raw = connection.unwrap()
    raw.close()
    return message


def replay(text: str, arm: str, out: Path, server_context, client_context) -> dict:
    if arm not in ARMS:
        raise ValueError("unknown arm")
    padded_up, padded_down = arm != "NONE", arm == "END_TO_END_PAD"
    up_frames = encode_message(text, padded_up)
    down_frames = encode_message(text, padded_down)
    origin_socket, up_socket, front_socket, down_socket = [listener() for _ in range(4)]
    all_sockets = [origin_socket, up_socket, front_socket, down_socket]
    ports = [s.getsockname()[1] for s in all_sockets]
    workers = []
    tees = []
    started = time.perf_counter_ns()
    observed_text = None
    error = None
    try:
        def origin():
            with origin_socket:
                conn, _ = origin_socket.accept()
            with conn:
                tls = server_context.wrap_socket(conn, server_side=True)
                tls.settimeout(SOCKET_TIMEOUT)
                send_frames(tls, up_frames)

        def frontend():
            # The visible receiver is a different TLS connection, after a real
            # decrypt/de-pad/re-chunk boundary. It never copies upstream padding.
            with socket.create_connection(("127.0.0.1", ports[1]), SOCKET_TIMEOUT) as conn:
                tls = client_context.wrap_socket(conn, server_hostname="localhost")
                received = decode_message(receive_and_close(tls), padded_up)
            if received != text:
                raise ValueError("frontend content changed")
            with front_socket:
                downstream, _ = front_socket.accept()
            with downstream:
                tls = server_context.wrap_socket(downstream, server_side=True)
                tls.settimeout(SOCKET_TIMEOUT)
                send_frames(tls, encode_message(received, padded_down))
            return sha(received.encode("utf-8"))

        tees = [Tee(up_socket, ports[0], out / "observer" / "upstream").start(),
                Tee(down_socket, ports[2], out / "observer" / "terminal").start()]
        workers = [Worker("origin", origin).start(), Worker("frontend", frontend).start()]
        with socket.create_connection(("127.0.0.1", ports[3]), SOCKET_TIMEOUT) as conn:
            tls = client_context.wrap_socket(conn, server_hostname="localhost")
            observed_text = decode_message(receive_and_close(tls), padded_down)
    except BaseException:
        error = traceback.format_exc()
    finally:
        for sock in all_sockets:
            try:
                sock.close()
            except OSError:
                pass
        closure_errors = []
        for worker in workers:
            try:
                worker.join()
                if worker.error:
                    closure_errors.append(worker.error)
            except BaseException:
                closure_errors.append(traceback.format_exc())
        for tee in tees:
            try:
                tee.join()
            except BaseException:
                closure_errors.append(traceback.format_exc())
        if closure_errors:
            error = (error or "") + "\n".join(closure_errors)
    elapsed = time.perf_counter_ns() - started
    closure = all(not w.thread.is_alive() for w in workers)
    closure &= all(not t.worker.thread.is_alive() and all(not w.thread.is_alive() for w in t.pump_workers) for t in tees)
    parsed = {}
    if error is None:
        try:
            parsed = {site: tee.parsed() for site, tee in zip(("upstream", "terminal"), tees)}
            for site, frames in (("upstream", up_frames), ("terminal", down_frames)):
                sizes = [r["payload_bytes"] for r in parsed[site]["s2c"]["records"] if r["type"] == 23]
                # TLS1.2 AES-GCM has 8-byte explicit nonce and 16-byte tag.
                # This check verifies actual SSL write/record framing on this run.
                if sizes != [len(frame) + 24 for frame in frames]:
                    raise ValueError("actual TLS framing differs from declared frames")
            if observed_text != text:
                raise ValueError("terminal content integrity failure")
        except BaseException:
            error = traceback.format_exc()
    report = {"status": "ok" if not error and closure else "failed", "arm": arm,
              "source_utf8_bytes": len(text.encode("utf-8")), "source_sha256": sha(text.encode("utf-8")),
              "terminal_sha256": sha(observed_text.encode("utf-8")) if observed_text is not None else None,
              "end_to_end_ns": elapsed, "all_owned_threads_joined": closure,
              "tls": "TLSv1.2/ECDHE-RSA-AES128-GCM-SHA256", "sites": parsed, "error": error}
    write_json(out / "private" / "integrity.json", {k: v for k, v in report.items() if k != "sites"})
    for site, observation in parsed.items():
        write_json(out / "observer" / (site + "-records.json"), observation)
    return report


def fit_threshold(rows):
    """Single-feature attack; training ties favor the constant class-0 rule."""
    values = sorted(set(row["feature"] for row in rows))
    candidates = [{"kind": "constant", "label": 0}, {"kind": "constant", "label": 1}]
    candidates += [{"kind": "threshold", "threshold": (a + b) / 2, "direction": direction}
                   for a, b in zip(values, values[1:]) for direction in (1, -1)]
    scored = [(sum(predict(candidate, row["feature"]) != row["label"] for row in rows), i, candidate)
              for i, candidate in enumerate(candidates)]
    return min(scored, key=lambda x: (x[0], x[1]))[2]


def predict(model, value):
    if model["kind"] == "constant":
        return model["label"]
    return int(value > model["threshold"]) if model["direction"] == 1 else int(value < model["threshold"])


def percentile(values, quantile):
    data = sorted(values)
    position = (len(data) - 1) * quantile
    lower = math.floor(position)
    return data[lower] + (data[min(lower + 1, len(data) - 1)] - data[lower]) * (position - lower)


def cluster_interval(group_values, seed=SEED):
    keys = sorted(group_values)
    rng = random.Random(seed)
    boot = [statistics.mean(group_values[rng.choice(keys)] for _ in keys) for _ in range(BOOTSTRAPS)]
    return [percentile(boot, .025), percentile(boot, .975)]


def analyze(features: list[dict]) -> dict:
    result = {"attacks": [], "paired_effects": []}
    correctness = {}
    for arm in ARMS:
        for site in ("upstream", "terminal"):
            selected = [r for r in features if r["arm"] == arm and r["site"] == site and r["status"] == "ok"]
            train = [r for r in selected if r["split"] == "train"]
            test = [r for r in selected if r["split"] == "test"]
            if not train or not test:
                result["attacks"].append({"arm": arm, "site": site, "status": "insufficient_data"})
                continue
            model = fit_threshold(train)
            outcomes = [{"id": r["id"], "group_id": r["group_id"], "label": r["label"],
                         "prediction": predict(model, r["feature"]),
                         "correct": int(predict(model, r["feature"]) == r["label"])} for r in test]
            groups = {}
            for outcome in outcomes:
                groups.setdefault(outcome["group_id"], []).append(outcome["correct"])
            group_means = {key: statistics.mean(value) for key, value in groups.items()}
            correctness[arm, site] = {r["id"]: r for r in outcomes}
            result["attacks"].append({"arm": arm, "site": site, "status": "ok", "model": model,
                "train_n": len(train), "test_n": len(test), "test_groups": len(groups),
                "train_accuracy": statistics.mean(predict(model, r["feature"]) == r["label"] for r in train),
                "test_accuracy": statistics.mean(r["correct"] for r in outcomes),
                "cluster_percentile_95ci": cluster_interval(group_means),
                "train_distinct_feature_values": len({r["feature"] for r in train}),
                "test_distinct_feature_values": len({r["feature"] for r in test}), "predictions": outcomes})
    for site in ("upstream", "terminal"):
        for first, second in (("NONE", "UPSTREAM_PAD"), ("UPSTREAM_PAD", "END_TO_END_PAD")):
            a, b = correctness.get((first, site), {}), correctness.get((second, site), {})
            if not a or set(a) != set(b):
                result["paired_effects"].append({"site": site, "from": first, "to": second, "status": "unpaired_missing"})
                continue
            groups = {}
            for key in a:
                groups.setdefault(a[key]["group_id"], []).append(b[key]["correct"] - a[key]["correct"])
            means = {key: statistics.mean(value) for key, value in groups.items()}
            result["paired_effects"].append({"site": site, "from": first, "to": second, "status": "ok",
                "accuracy_difference": statistics.mean(means.values()), "test_groups": len(means),
                "cluster_percentile_95ci": cluster_interval(means)})
    return result


def validate_records(records, expected_groups=24):
    seen, groups = set(), {}
    for row in records:
        if not set(("id", "group_id", "label", "split", "text", "status")).issubset(row):
            raise ValueError("missing input field")
        if row["id"] in seen or row["label"] not in (0, 1) or row["split"] not in ("train", "test"):
            raise ValueError("duplicate id or invalid label/split")
        if not isinstance(row["text"], str) or not isinstance(row["status"], str):
            raise ValueError("text/status must be strings")
        seen.add(row["id"])
        groups.setdefault(row["group_id"], []).append(row)
    for group in groups.values():
        if len(group) != 2 or {r["label"] for r in group} != {0, 1} or len({r["split"] for r in group}) != 1:
            raise ValueError("group must hold exactly one short/detail pair, with no split leakage")
    if expected_groups is not None:
        if len(groups) != expected_groups or sum(g[0]["split"] == "train" for g in groups.values()) != expected_groups // 2:
            raise ValueError("expected 24 groups, 12 train/12 test, 48 paired saved outputs")
    return groups


def run(input_path: Path, out: Path):
    if out.exists():
        raise FileExistsError("new output directory required; no replay/retry in place")
    data = input_path.read_bytes()
    records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    validate_records(records)
    out.mkdir(parents=True)
    write_json(out / "protocol.json", {"version": "E1-v1", "seed": SEED, "input_sha256": sha(data),
        "source_sha256": sha(Path(__file__).read_bytes()), "record_n": len(records), "expected_replays": len(records) * 3,
        "arms": ARMS, "padding_frames": PAD_FRAMES, "padding_frame_bytes": PAD_FRAME_BYTES,
        "unpadded_frame_bytes": PLAIN_FRAME_BYTES, "feature": "S2C TLS1.2 type23 record payload-byte total",
        "split": "12 topic pairs train, 12 disjoint topic pairs test", "bootstrap_clusters": "held-out topic pairs",
        "bootstrap_replicates": BOOTSTRAPS, "timing": "descriptive tee-read timing only, no timing privacy claim",
        "network_boundary": "127.0.0.1 only, ephemeral ports, two actual TLS links",
        "python": platform.python_version(), "openssl": ssl.OPENSSL_VERSION})
    # Preserve exact source records privately; the tee observer files have no
    # plaintext, labels, group names, or task correctness fields.
    (out / "private").mkdir()
    (out / "private" / "input.jsonl").write_bytes(data)
    cert_path, key_path = certificate(out / "private" / "tls")
    server, client = contexts(cert_path, key_path)
    schedule = [(row, arm) for row in records for arm in ARMS]
    random.Random(SEED).shuffle(schedule)
    features, private_reports, observations = [], [], []
    for index, (row, arm) in enumerate(schedule):
        trace_id = f"trace-{index:04d}"
        trial_path = out / "trials" / trace_id
        if row["status"] != "ok":
            report = {"status": "failed_input", "error": "saved model generation did not complete", "arm": arm,
                      "all_owned_threads_joined": True, "sites": {}, "source_utf8_bytes": len(row["text"].encode()),
                      "end_to_end_ns": None, "source_sha256": sha(row["text"].encode())}
        else:
            try:
                report = replay(row["text"], arm, trial_path, server, client)
            except BaseException:
                report = {"status": "failed_setup", "error": traceback.format_exc(), "arm": arm,
                          "sites": {}, "all_owned_threads_joined": False, "end_to_end_ns": None,
                          "source_utf8_bytes": len(row["text"].encode()), "source_sha256": sha(row["text"].encode())}
        private_reports.append({"trace_id": trace_id, "id": row["id"], "group_id": row["group_id"],
                                "label": row["label"], "split": row["split"], **report})
        for site in ("upstream", "terminal"):
            feature = report.get("sites", {}).get(site, {}).get("s2c", {}).get("application_payload_bytes")
            feature_row = {"trace_id": trace_id, "id": row["id"], "group_id": row["group_id"],
                "label": row["label"], "split": row["split"], "arm": arm, "site": site,
                "status": report["status"], "feature": feature}
            features.append(feature_row)
            observations.append({"trace_id": trace_id, "arm": arm, "site": site,
                                 "status": report["status"], "application_payload_bytes": feature})
        write_json(out / "private" / "replay-receipts.json", private_reports)
        write_json(out / "progress.json", {"closed_replays": index + 1, "expected_replays": len(schedule),
            "failed_replays": sum(r["status"] != "ok" for r in private_reports),
            "all_closed_threads_joined": all(r["all_owned_threads_joined"] for r in private_reports)})
        if not report["all_owned_threads_joined"]:
            break
    write_csv(out / "observer-features.csv", observations)
    write_csv(out / "private" / "attack-release.csv", features)
    attacks = analyze(features)
    costs = []
    for arm in ARMS:
        for site in ("upstream", "terminal"):
            selected = [r for r in private_reports if r["arm"] == arm and r["status"] == "ok"]
            totals = [r["sites"][site]["s2c"]["application_wire_bytes"] for r in selected]
            durations = [r["end_to_end_ns"] / 1e6 for r in selected]
            costs.append({"arm": arm, "site": site, "completed_replays": len(selected),
                "application_wire_bytes_total": sum(totals), "mean_application_wire_bytes": statistics.mean(totals) if totals else None,
                "median_end_to_end_ms": statistics.median(durations) if durations else None,
                "latency_scope": "both links and frontend including per-trial TLS handshakes; descriptive one replay"})
    summary = {"status": "complete" if len(private_reports) == len(schedule) and all(r["status"] == "ok" for r in private_reports) else "partial_or_failed",
        "closed_replays": len(private_reports), "expected_replays": len(schedule),
        "failed_replays": sum(r["status"] != "ok" for r in private_reports),
        "content_integrity_passes": sum(r["status"] == "ok" and r["source_sha256"] == r["terminal_sha256"] for r in private_reports),
        "all_owned_threads_joined": all(r["all_owned_threads_joined"] for r in private_reports),
        "analysis": attacks, "costs": costs,
        "boundary": "size-only fixed saved-output replay; loopback TLS frontend; not a timing/noninterference or general deployed-agent privacy guarantee"}
    write_json(out / "summary.json", summary)
    write_csv(out / "costs.csv", costs)
    manifest = [{"path": str(p.relative_to(out)).replace("\\", "/"), "sha256": sha(p.read_bytes())}
                for p in sorted(out.rglob("*")) if p.is_file()]
    write_json(out / "manifest.json", manifest)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", choices=["run"])
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--execute-approved", action="store_true", required=True)
    args = parser.parse_args()
    summary = run(args.input, args.out)
    print(json.dumps({k: summary[k] for k in ("status", "closed_replays", "failed_replays", "content_integrity_passes", "all_owned_threads_joined")}))


if __name__ == "__main__":
    main()
