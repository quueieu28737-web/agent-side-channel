"""Restricted observer views of the pinned UI Traces public DOM events.

``project`` reads only ``dom_trace.events``. It retains the page-JavaScript
event vocabulary and excludes harness HTTP-navigation records. The URL gates
origin membership and supplies an opaque page key retained only as internal
metadata. Neither URL content, the page key, page counts, nor episode/harness
metadata is a predictor. ``t_episode`` is never read.

Feature layout:
* coarse: seven log1p type counts, an untransformed empty flag, log1p missing-
  and valid-local-timestamp counts, and log1p raw page-local timestamp
  sum/mean/population-std/median/p90.
* combined: coarse plus 49 ordered bigram counts divided by the total number
  of adjacent retained pairs. Pairs follow recorded archive-receiver order,
  including across documents; this block uses no timing or page key. The
  protocol grants an ordered callback transcript at the retained receiver.
  This is not an assumption of independent capture by a single page's JS.
* action_only: the seven log1p type counts, empty flag, and the bigram block.

Local timestamp statistics describe each event's page age in milliseconds.
There is no subtraction between events or inferred document segmentation: the
archive lacks reliable document-stream IDs, and same-URL reloads can reset a
clock without identifying a new document. An absent/non-real/non-finite/
negative local ``t`` becomes ``None``; zero is valid. No episode duration,
latency, or cross-document wall-clock estimate is substituted.

``delay`` is an offline timestamp obfuscation control, not a live agent defense.
``shuffle_types`` is a diagnostic counterfactual, not a physically replayable
trace. Neither helper modifies its input.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import hashlib
import math
from numbers import Real
import random
from typing import Any, Optional
from urllib.parse import urlsplit

import numpy as np


EVENT_TYPES = (
    "click", "keydown", "scroll", "navigate", "beforeunload", "focus", "unknown"
)
PROJECTION_VIEWS = ("pooled_js", "single_origin_js", "other_origins_js")
FEATURE_VIEWS = ("coarse", "combined", "action_only")
DEFAULT_ORIGIN = "https://en.wikipedia.org"
_TYPE_INDEX = {event_type: i for i, event_type in enumerate(EVENT_TYPES)}
_JS_NAVIGATION_TRIGGERS = frozenset(("pushState", "popstate"))


def _timestamp(value: Any) -> Optional[float]:
    """Accept nonnegative numeric page age without coercing strings/booleans."""
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    try:
        value = float(value)
    except (OverflowError, TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def _event_type(value: Any) -> str:
    return value if isinstance(value, str) and value in _TYPE_INDEX else "unknown"


def _origin(url: Any) -> Optional[tuple[str, str, int]]:
    """Return a browser-origin tuple, treating explicit default ports equally."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        if scheme not in ("http", "https") or not hostname:
            return None
        port = parsed.port
    except ValueError:
        return None
    return (scheme, hostname.lower(), port if port is not None else (443 if scheme == "https" else 80))


def project(
    episode: Mapping[str, Any],
    view: str = "pooled_js",
    origin: str = DEFAULT_ORIGIN,
) -> list[dict[str, Any]]:
    """Project an episode to sanitized ``{type, t, page_key}`` records.

    ``pooled_js`` accepts events on any HTTP(S) origin. ``single_origin_js``
    accepts exactly ``origin`` under browser-origin semantics.
    ``other_origins_js`` is its exact complement among HTTP(S) page-JS events.
    Unknown event names map to the explicit ``unknown`` bucket. Any event named ``navigate``
    is retained only when its trigger is ``pushState`` or ``popstate``.
    Missing local timestamps remain as events and are represented by ``None``.
    """
    if view not in PROJECTION_VIEWS:
        raise ValueError(f"unknown projection view: {view!r}")
    required_origin = _origin(origin)
    if view != "pooled_js" and required_origin is None:
        raise ValueError("origin-restricted views require an HTTP(S) origin")
    dom_trace = episode.get("dom_trace", {})
    if not isinstance(dom_trace, Mapping):
        return []
    raw_events = dom_trace.get("events", [])
    if not isinstance(raw_events, (list, tuple)):
        return []

    projected = []
    for event in raw_events:
        if not isinstance(event, Mapping):
            continue
        raw_type = event.get("type")
        if raw_type == "navigate" and event.get("trigger") not in _JS_NAVIGATION_TRIGGERS:
            continue
        url = event.get("url")
        event_origin = _origin(url)
        if event_origin is None:
            continue
        if view == "single_origin_js" and event_origin != required_origin:
            continue
        if view == "other_origins_js" and event_origin == required_origin:
            continue
        projected.append({
            "type": _event_type(raw_type),
            "t": _timestamp(event.get("t")),
            "page_key": hashlib.sha256(url.encode("utf-8")).hexdigest(),
        })
    return projected


def _records(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Copy only the allowed fields so helpers cannot propagate metadata."""
    records = []
    for event in events:
        if not isinstance(event, Mapping):
            raise TypeError("events must contain mappings")
        page_key = event.get("page_key")
        records.append({
            "type": _event_type(event.get("type")),
            "t": _timestamp(event.get("t")),
            "page_key": page_key if isinstance(page_key, str) and page_key else None,
        })
    return records


def _transitions(records: list[dict[str, Any]]) -> np.ndarray:
    transitions = np.zeros((len(EVENT_TYPES), len(EVENT_TYPES)), dtype=np.float64)
    for previous, current in zip(records, records[1:]):
        transitions[_TYPE_INDEX[previous["type"]], _TYPE_INDEX[current["type"]]] += 1.0
    if len(records) > 1:
        transitions /= len(records) - 1
    return transitions.ravel()


def feature_names(view: str = "coarse") -> tuple[str, ...]:
    """Return names in exactly the order emitted by ``features``."""
    if view not in FEATURE_VIEWS:
        raise ValueError(f"unknown feature view: {view!r}")
    names = tuple(f"log1p_count_{event_type}" for event_type in EVENT_TYPES) + ("empty",)
    if view in ("coarse", "combined"):
        names += (
            "log1p_local_timestamp_missing_count", "log1p_local_timestamp_valid_count",
            "log1p_local_timestamp_sum_ms", "log1p_local_timestamp_mean_ms",
            "log1p_local_timestamp_std_ms", "log1p_local_timestamp_median_ms",
            "log1p_local_timestamp_p90_ms",
        )
    if view in ("combined", "action_only"):
        names += tuple(
            f"transition_{previous}_to_{current}"
            for previous in EVENT_TYPES for current in EVENT_TYPES
        )
    return names


def features(events: Iterable[Mapping[str, Any]], view: str = "coarse") -> np.ndarray:
    """Return a float64 feature vector using only type and raw local t.

    Ordered type bigrams use the archive receiver's callback transcript order.
    Page keys are never used, including to infer document or clock boundaries.
    """
    if view not in FEATURE_VIEWS:
        raise ValueError(f"unknown feature view: {view!r}")
    records = _records(events)
    counts = np.zeros(len(EVENT_TYPES), dtype=np.float64)
    for record in records:
        counts[_TYPE_INDEX[record["type"]]] += 1.0
    blocks = [np.log1p(counts), np.array([float(not records)], dtype=np.float64)]

    if view in ("coarse", "combined"):
        local_timestamps = np.array(
            [record["t"] for record in records if record["t"] is not None],
            dtype=np.float64,
        )
        missing_count = sum(record["t"] is None for record in records)
        summaries = (
            [local_timestamps.sum(), local_timestamps.mean(), local_timestamps.std(ddof=0),
             np.median(local_timestamps), np.percentile(local_timestamps, 90)]
            if local_timestamps.size else [0.0] * 5
        )
        blocks.append(np.log1p(np.array([missing_count, local_timestamps.size, *summaries], dtype=np.float64)))
    if view in ("combined", "action_only"):
        blocks.append(_transitions(records))
    return np.concatenate(blocks)


def delay(
    events: Iterable[Mapping[str, Any]],
    max_delay_ms: float = 5000,
    seed: str = "0",
) -> list[dict[str, Any]]:
    """Add independent U(0,D) noise to every valid local timestamp.

    This offline timestamp obfuscation control preserves event order/types,
    page keys, and missing times. It does not reconstruct document boundaries,
    claim a physical action delay, or measure live execution utility.
    """
    bound = _timestamp(max_delay_ms)
    if bound is None or bound < 0:
        raise ValueError("max_delay_ms must be a finite nonnegative number")
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")
    records = _records(events)
    rng = random.Random(seed)
    for record in records:
        if record["t"] is not None:
            record["t"] += rng.uniform(0.0, bound)
    return records


def shuffle_types(
    events: Iterable[Mapping[str, Any]], seed: str
) -> list[dict[str, Any]]:
    """Permute type assignments, preserving all counts and local time/page vectors.

    The shuffled trace is a diagnostic counterfactual, not a physical replay.
    """
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")
    records = _records(events)
    types = [record["type"] for record in records]
    random.Random(seed).shuffle(types)
    for record, event_type in zip(records, types):
        record["type"] = event_type
    return records
