"""Pinned, bounded UI Traces ingestion; no extraction or upstream code execution.

Only canonical ``frames_test`` members are parsed. Model input is reduced to
page-JavaScript event fields ``type``, ``url``, ``t`` and ``trigger``. In
particular, ``t`` is the original page-local clock: collector ``t_episode`` is
NEVER copied or used as a fallback. Missing page-local timestamps stay missing.
This conservative projection is not a reproduction of the author's 41 features.

``ingest`` creates a NEW output directory and returns its inventory. Any input,
binding, archive or resource-limit problem yields HOLD and retains that audit;
HOLD output must not be fitted. Synthetic tests may inject SourceIdentity and
expected_rows, but production defaults pin both source files and all 4,200 rows.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import tarfile
import time
from typing import Any, Mapping


@dataclass(frozen=True)
class SourceIdentity:
    archive_size: int = 184239560
    archive_sha256: str = "79aeee6a2a7c9b32cfa0eb2a2c95663258338b33eeac1eb0117001dde5712f79"
    split_size: int = 1742400
    split_sha256: str = "a3069bd63dafaf3d47cf2316d4cea0fa2ca54c594ea2b5a86e15a77a336d9bf8"


@dataclass(frozen=True)
class Limits:
    max_declared_bytes: int = 64 * 1024**3
    max_members: int = 200000
    max_json_bytes: int = 16 * 1024**2
    max_seconds: float = 600.0


class _Hold(Exception):
    """Controlled refusal with a content-free audit reason."""


class _DeadlineReader:
    """Stream reader that also binds bytes consumed by the actual archive scan."""

    def __init__(self, raw, deadline):
        self.raw = raw
        self.deadline = deadline
        self.sha = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size=-1):
        _check_time(self.deadline)
        # tarfile's stream layer accepts short reads. Bound each blocking read.
        amount = 1024 * 1024 if size < 0 else min(size, 1024 * 1024)
        data = self.raw.read(amount)
        self.sha.update(data)
        self.bytes_read += len(data)
        _check_time(self.deadline)
        return data


def _check_time(deadline):
    if time.monotonic() > deadline:
        raise _Hold("time_limit")


def _reject_constant(_):
    raise _Hold("nonfinite_json_constant")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _Hold("duplicate_json_key")
        result[key] = value
    return result


def _finite_json_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise _Hold("nonfinite_json_number")
    return number


def _bounded_json_int(value):
    # Older Python versions otherwise permit costly decimal integer conversion.
    if len(value.lstrip("-")) > 4096:
        raise _Hold("json_integer_size_limit")
    return int(value)


def _strict_json(raw):
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant, parse_float=_finite_json_float,
                           parse_int=_bounded_json_int)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise _Hold("invalid_json") from None
    return value


def _guarded_tarinfo(limits, deadline, header_counts):
    """Bound headers *before* tarfile reads PAX/GNU extension payloads."""

    class GuardedTarInfo(tarfile.TarInfo):
        @classmethod
        def frombuf(cls, buf, encoding, errors):
            try:
                return super().frombuf(buf, encoding, errors)
            except (tarfile.InvalidHeaderError, tarfile.TruncatedHeaderError):
                # ignore_zeros may skip legitimate zero blocks, never malformed ones.
                raise _Hold("invalid_tar_header") from None

        def _proc_member(self, tar):
            _check_time(deadline)
            header_counts["members"] += 1
            if self.size < 0:
                raise _Hold("negative_member_size")
            header_counts["declared_bytes"] += self.size
            if header_counts["members"] > limits.max_members:
                raise _Hold("member_count_limit")
            if header_counts["declared_bytes"] > limits.max_declared_bytes:
                raise _Hold("declared_size_limit")
            metadata_types = (tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK,
                              tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE)
            if self.type in metadata_types and self.size > limits.max_json_bytes:
                raise _Hold("tar_metadata_size_limit")
            return super()._proc_member(tar)

    return GuardedTarInfo


def _configuration(value, kind):
    if value is None:
        return kind()
    if isinstance(value, kind):
        return value
    if isinstance(value, Mapping):
        return kind(**value)
    raise TypeError("configuration must be its dataclass or a mapping")


def _validate_limits(limits):
    caps = Limits()
    for name, value in asdict(limits).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("resource limits must be positive numbers")
        if not math.isfinite(value) or value <= 0 or value > getattr(caps, name):
            raise ValueError("resource limits must be positive and cannot exceed the protocol caps")
        if name != "max_seconds" and not isinstance(value, int):
            raise ValueError("byte and member limits must be integers")


def _digest_file(path, deadline):
    sha = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            _check_time(deadline)
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            sha.update(block)
    _check_time(deadline)
    return size, sha.hexdigest()


def _safe_member_name(name):
    # Reject both POSIX and Windows absolute forms; no member is written to disk.
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return False
    posix, windows = PurePosixPath(name), PureWindowsPath(name)
    return not (posix.is_absolute() or windows.is_absolute() or windows.drive
                or ".." in name.split("/"))


def _candidate(name):
    # Literal components, without basename substitution or classifier lookup.
    parts = name.split("/")
    if (len(parts) != 5 or parts[0] != "traces" or parts[2] != "frames_test"
            or not parts[1] or not parts[3] or not parts[4].endswith(".json")):
        return None
    episode_id = parts[4][:-5]
    if not episode_id:
        return None
    return parts[1], episode_id


def _canonical(raw, expected_rows, deadline):
    value = _strict_json(raw)
    if not isinstance(value, dict) or value.get("dataset") != "frames":
        raise _Hold("invalid_split_dataset")
    rows = value.get("records")
    if not isinstance(rows, list) or len(rows) != expected_rows:
        raise _Hold("canonical_row_count")
    canonical = {}
    splits = Counter()
    per_agent = defaultdict(Counter)
    for record in rows:
        _check_time(deadline)
        if not isinstance(record, dict):
            raise _Hold("invalid_canonical_record")
        agent, episode = record.get("agent_id"), record.get("episode_id")
        question, split = record.get("question"), record.get("split")
        if (not isinstance(agent, str) or not agent or not isinstance(episode, str)
                or not episode or not isinstance(question, str)
                or split not in ("train", "val", "test")):
            raise _Hold("invalid_canonical_record")
        if any(char in agent + episode for char in ("/", "\\", "\x00")):
            raise _Hold("invalid_canonical_identity")
        key = agent, episode
        if key in canonical:
            raise _Hold("duplicate_canonical_identity")
        try:
            question_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()
        except UnicodeEncodeError:
            raise _Hold("invalid_question_utf8") from None
        canonical[key] = {"agent_id": agent, "episode_id": episode, "split": split,
                          "question": question, "question_hash": question_hash}
        splits[split] += 1
        per_agent[agent][split] += 1
    if value.get("counts") != dict(splits):
        raise _Hold("canonical_split_counts")
    if expected_rows == 4200:
        if (dict(splits) != {"train": 2100, "val": 1050, "test": 1050}
                or len(per_agent) != 14
                or any(dict(counts) != {"train": 150, "val": 75, "test": 75}
                       for counts in per_agent.values())
                or value.get("resplit_seed") != 42
                or value.get("resplit_n_per_agent") != 300):
            raise _Hold("canonical_protocol_counts")
    return canonical, dict(splits), {a: dict(c) for a, c in sorted(per_agent.items())}


def _project_events(episode):
    timing = Counter({key: 0 for key in ("valid", "missing", "null", "negative",
                                        "nonnumeric", "complex_sanitized", "out_of_float_range")})
    dom = episode.get("dom_trace")
    if dom is None:
        return [], dict(timing)
    if not isinstance(dom, dict):
        raise _Hold("invalid_dom_trace")
    events = dom.get("events")
    if events is None:
        return [], dict(timing)
    if not isinstance(events, list):
        raise _Hold("invalid_events")
    projected = []
    for event in events:
        if not isinstance(event, dict):
            raise _Hold("invalid_event")
        safe = {}
        for key in ("type", "url", "trigger"):
            if key in event:
                if event[key] is not None and not isinstance(event[key], str):
                    raise _Hold("invalid_event_field")
                safe[key] = event[key]
        if "t" in event:
            timestamp = event["t"]
            if timestamp is None:
                timing["null"] += 1
                safe["t"] = None
            elif isinstance(timestamp, (list, dict)):
                # Source bytes remain hashed; a complex field is never copied
                # into model input. Explicit None is recorded, never imputed 0.
                timing["complex_sanitized"] += 1
                safe["t"] = None
            elif isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
                timing["nonnumeric"] += 1
                safe["t"] = timestamp
            else:
                try:
                    finite = math.isfinite(timestamp)
                except OverflowError:
                    finite = False
                if not finite:
                    timing["out_of_float_range"] += 1
                elif timestamp < 0:
                    timing["negative"] += 1
                else:
                    timing["valid"] += 1
                safe["t"] = timestamp
        else:
            timing["missing"] += 1
        # t_episode, meta, result, key text, DOM text and all extra fields vanish.
        projected.append(safe)
    return projected, dict(timing)


def _bound_row(episode, canonical):
    if not isinstance(episode, dict) or not isinstance(episode.get("meta"), dict):
        raise _Hold("missing_episode_meta")
    meta = episode["meta"]
    if meta.get("agent_id") != canonical["agent_id"]:
        raise _Hold("agent_label_mismatch")
    if meta.get("episode_id") != canonical["episode_id"]:
        raise _Hold("episode_identity_mismatch")
    # Exact strings bind first; no trimming, normalization or semantic matching.
    if meta.get("question") != canonical["question"]:
        raise _Hold("question_mismatch")
    events, timing = _project_events(episode)
    return {"id": canonical["agent_id"] + "/" + canonical["episode_id"],
            "agent_id": canonical["agent_id"], "episode_id": canonical["episode_id"],
            "label": meta["agent_id"], "split": canonical["split"],
            "question_hash": canonical["question_hash"],
            "error_present": episode.get("error") is not None,
            "result_present": episode.get("result") is not None,
            "empty_trace": len(events) == 0, "event_count": len(events),
            "timestamp_audit": timing,
            "episode": {"dom_trace": {"events": events}}}


def ingest(archive: Path, split_record: Path, output_dir: Path, *,
           limits: Limits | Mapping[str, Any] | None = None,
           expected_identity: SourceIdentity | Mapping[str, Any] | None = None,
           expected_rows: int = 4200):
    """Create episodes.jsonl and inventory.json under a new directory only.

    Audit issues return HOLD, never a substituted cohort. ``scanner_complete``
    means the streaming member iterator reached EOF without a bound or I/O error.
    No selected symbolic/hard links are followed. All names are checked, including
    nonselected members; nonselected member payloads are never parsed.
    """
    limits = _configuration(limits, Limits)
    identity = _configuration(expected_identity, SourceIdentity)
    _validate_limits(limits)
    if isinstance(expected_rows, bool) or not isinstance(expected_rows, int) or expected_rows <= 0:
        raise ValueError("expected_rows must be a positive integer")
    archive, split_record, output_dir = Path(archive), Path(split_record), Path(output_dir)
    # Exclusive creation is intentional: never reuse or overwrite an earlier run.
    output_dir.mkdir(exist_ok=False)
    started = time.monotonic()
    deadline = started + limits.max_seconds
    inventory = {"schema": "uitraces-conservative-ingest-v1", "status": "HOLD",
                 "expected_rows": expected_rows, "expected_identity": asdict(identity),
                 "limits": asdict(limits), "sources": {}, "scanner_complete": False,
                 "members": 0, "declared_bytes": 0, "selected_members": [],
                 "raw_header_counts": {"members": 0, "declared_bytes": 0},
                 "nonselected_counts": {}, "issues": [], "row_counts": {},
                 "model_calls": 0, "upstream_code_executed": False,
                 "archive_extracted": False,
                 "clock": "raw page-local t only; t_episode discarded",
                 "output_files": ["episodes.jsonl", "inventory.json"]}
    canonical, bound, seen_ids, seen_names = {}, set(), Counter(), set()
    row_counts, split_counts, nonselected, timestamp_counts = Counter(), Counter(), Counter(), Counter()
    per_agent = defaultdict(Counter)

    def issue(code, **detail):
        inventory["issues"].append({"code": code, **detail})

    with (output_dir / "episodes.jsonl").open("x", encoding="utf-8", newline="\n") as rows_out:
        try:
            for label, source, size, sha in (
                    ("archive", archive, identity.archive_size, identity.archive_sha256),
                    ("split_record", split_record, identity.split_size, identity.split_sha256)):
                observed_size, observed_sha = _digest_file(source, deadline)
                inventory["sources"][label] = {"path": str(source.resolve()),
                    "size": observed_size, "sha256": observed_sha}
                if observed_size != size or observed_sha != sha:
                    raise _Hold(label + "_identity_mismatch")
            if identity.split_size > limits.max_json_bytes:
                raise _Hold("split_json_size_limit")
            raw_split = split_record.read_bytes()
            if (len(raw_split) != identity.split_size
                    or hashlib.sha256(raw_split).hexdigest() != identity.split_sha256):
                raise _Hold("split_changed_after_hash")
            canonical, counts, agents = _canonical(raw_split, expected_rows, deadline)
            inventory["canonical_counts"] = counts
            inventory["canonical_per_agent"] = agents
            with archive.open("rb") as raw_archive:
                reader = _DeadlineReader(raw_archive, deadline)
                # ignore_zeros scans to physical stream EOF, including entries
                # following tar zero blocks, rather than accepting an early prefix.
                guarded_info = _guarded_tarinfo(limits, deadline, inventory["raw_header_counts"])
                with tarfile.open(fileobj=reader, mode="r|xz", ignore_zeros=True,
                                  tarinfo=guarded_info) as tar:
                    for member in tar:
                        _check_time(deadline)
                        inventory["members"] += 1
                        if member.size < 0:
                            raise _Hold("negative_member_size")
                        inventory["declared_bytes"] += member.size
                        if inventory["members"] > limits.max_members:
                            raise _Hold("member_count_limit")
                        if inventory["declared_bytes"] > limits.max_declared_bytes:
                            raise _Hold("declared_size_limit")
                        name = member.name
                        safe_name = _safe_member_name(name)
                        if not safe_name:
                            issue("unsafe_member_path", member=name)
                        duplicate_name = name in seen_names
                        if duplicate_name:
                            issue("duplicate_member_name", member=name)
                        seen_names.add(name)
                        key = _candidate(name) if safe_name else None
                        if key not in canonical:
                            nonselected["members"] += 1
                            nonselected["declared_bytes"] += member.size
                            nonselected["directories" if member.isdir() else
                                        "regular_files" if member.isfile() else "other"] += 1
                            continue
                        seen_ids[key] += 1
                        manifest = {"member": name, "agent_id": key[0], "episode_id": key[1],
                                    "declared_bytes": member.size, "bytes": 0,
                                    "sha256": None, "binding_status": "REJECTED"}
                        inventory["selected_members"].append(manifest)
                        if seen_ids[key] > 1:
                            issue("duplicate_selected_identity", member=name,
                                  agent_id=key[0], episode_id=key[1])
                        if not member.isfile():
                            issue("selected_member_not_regular", member=name)
                            continue
                        if member.size > limits.max_json_bytes:
                            issue("selected_json_size_limit", member=name)
                            continue
                        selected = tar.extractfile(member)
                        if selected is None:
                            issue("selected_member_unreadable", member=name)
                            continue
                        with selected:
                            raw = selected.read(limits.max_json_bytes + 1)
                        manifest["bytes"] = len(raw)
                        manifest["sha256"] = hashlib.sha256(raw).hexdigest()
                        if len(raw) != member.size:
                            issue("selected_byte_count_mismatch", member=name)
                            continue
                        try:
                            row = _bound_row(_strict_json(raw), canonical[key])
                        except _Hold as exc:
                            issue(str(exc), member=name)
                            continue
                        if duplicate_name or seen_ids[key] > 1:
                            manifest["binding_status"] = "DUPLICATE"
                            continue
                        _check_time(deadline)
                        manifest["binding_status"] = "BOUND"
                        manifest["question_hash"] = row["question_hash"]
                        rows_out.write(json.dumps(row, ensure_ascii=True, allow_nan=False,
                                                  separators=(",", ":")) + "\n")
                        bound.add(key)
                        row_counts["total"] += 1
                        row_counts["empty_rows"] += row["empty_trace"]
                        row_counts["error_present_rows"] += row["error_present"]
                        row_counts["result_present_rows"] += row["result_present"]
                        row_counts["failure_rows"] += row["error_present"] or not row["result_present"]
                        split_counts[row["split"]] += 1
                        per_agent[row["agent_id"]][row["split"]] += 1
                        timestamp_counts.update(row["timestamp_audit"])
                    # tarfile's streaming decoder does not itself require the
                    # XZ footer, so an exhausted iterator alone is insufficient.
                    if not tar.fileobj.cmp.eof:
                        raise _Hold("incomplete_xz_stream")
                    if tar.fileobj.cmp.unused_data:
                        raise _Hold("trailing_compressed_data")
                # Bind every compressed input byte even if the decoder buffered EOF.
                while reader.read(1024 * 1024):
                    pass
                inventory["sources"]["archive"]["scan_bytes"] = reader.bytes_read
                inventory["sources"]["archive"]["scan_sha256"] = reader.sha.hexdigest()
                if (reader.bytes_read != identity.archive_size
                        or reader.sha.hexdigest() != identity.archive_sha256):
                    raise _Hold("archive_changed_during_scan")
                inventory["scanner_complete"] = True
        except _Hold as exc:
            issue(str(exc))
        except (OSError, tarfile.TarError, EOFError, ValueError, OverflowError, RecursionError) as exc:
            # Do not copy raw exception messages, which can contain source text.
            issue("input_or_stream_error", exception_type=type(exc).__name__)

    missing = sorted(set(canonical) - bound)
    inventory["missing_canonical_ids"] = [{"agent_id": a, "episode_id": e} for a, e in missing]
    if canonical and missing:
        issue("missing_canonical_bindings", count=len(missing))
    inventory["row_counts"] = {name: row_counts[name] for name in
        ("total", "empty_rows", "error_present_rows", "result_present_rows", "failure_rows")}
    inventory["row_counts"]["by_split"] = dict(sorted(split_counts.items()))
    inventory["row_counts"]["timestamp_audit"] = dict(timestamp_counts)
    inventory["row_counts"]["by_agent_and_split"] = {a: dict(c) for a, c in sorted(per_agent.items())}
    inventory["row_counts"]["minimum_rows_per_agent"] = min(
        (sum(per_agent[a].values()) for a, _ in canonical), default=0)
    inventory["row_counts"]["minimum_rows_per_agent_split"] = {
        split: min((per_agent[a][split] for a, _ in canonical), default=0)
        for split in ("train", "val", "test")}
    inventory["nonselected_counts"] = dict(nonselected)
    inventory["selected_member_count"] = len(inventory["selected_members"])
    inventory["bound_identity_count"] = len(bound)
    inventory["elapsed_seconds"] = round(time.monotonic() - started, 6)
    if (inventory["scanner_complete"] and not inventory["issues"]
            and len(bound) == expected_rows and len(canonical) == expected_rows):
        inventory["status"] = "COMPLETE_READY"
    with (output_dir / "inventory.json").open("x", encoding="utf-8", newline="\n") as audit_out:
        json.dump(inventory, audit_out, ensure_ascii=True, indent=2, allow_nan=False)
        audit_out.write("\n")
    return inventory
