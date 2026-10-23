"""Deterministic TLS 1.2 (ECDHE-RSA-AES128-GCM-SHA256) application-record model.

Each length-prefixed message (4-byte prefix + body) is written with one sendall.
OpenSSL fragments plaintext at 16,384 bytes; every GCM record adds an 8-byte
explicit nonce and a 16-byte tag, so the record payload is fragment + 24 bytes.
validate_against_r4() checks this model against every socket-measured R4 capture
before any new result is computed; tlslab.py remains the measurement reference.
"""
import math

MAX_FRAGMENT = 16384
GCM_OVERHEAD = 24


def framed_length(n, framing, req, caps):
    """Length of the framed message body (excluding the 4-byte prefix)."""
    if framing == 'raw':
        return n
    total = n + 4
    if framing == 'bucket1024':
        return int(math.ceil(total / 1024)) * 1024 - 4
    cap = caps['req' if req else 'resp']
    tgt = cap if total <= cap else int(math.ceil(total / 1024)) * 1024
    return tgt - 4


def records(direction, body_len):
    n = body_len + 4
    out = []
    while n > 0:
        k = min(n, MAX_FRAGMENT)
        out.append((direction, k + GCM_OVERHEAD))
        n -= k
    return out


def session(calls, framing, caps):
    seq = []
    for c in calls:
        seq += records('c2s', framed_length(c['req'], framing, True, caps))
        seq += records('s2c', framed_length(c['resp'], framing, False, caps))
    return seq


def validate_against_r4(sessions, caps):
    bad = 0
    for s in sessions:
        fr = 'const' if s['condition'] in ('padding_only', 'shape_const') else 'raw'
        model = session(s['calls'], fr, caps)
        if [tuple(x) for x in s['records']] != model:
            bad += 1
    return {'sessions': len(sessions), 'mismatches': bad}
