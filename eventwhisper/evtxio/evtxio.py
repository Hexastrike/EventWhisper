from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evtx import PyEvtxParser

from eventwhisper.utils.config import RESULTS_LIMIT, SCAN_LIMIT
from eventwhisper.utils.normalize_lists import normalize_int_list, normalize_str_list
from eventwhisper.utils.normalize_timestamp import normalize_timestamp
from eventwhisper.utils.normalize_value import normalize_int
from eventwhisper.utils.normalize_wrapping_quotes import normalize_wrapping_quotes


# Helpers
def _normalize_path(p: str | Path) -> Path:
    """Coerce to Path and strip surrounding quotes/backticks if it's a string."""
    if isinstance(p, Path):
        return p
    return Path(normalize_wrapping_quotes(p))


def _get_dotted(obj: Any, dotted: str) -> Any:
    """
    Resolve a dotted path in nested dict/list structures.
    Supports dict keys and numeric list indices.
    Examples: 'Event.System.EventID', 'Event.EventData.Data.0'
    Returns None if any segment is missing.
    """
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            if part in cur:
                cur = cur[part]
            else:
                return None
        elif isinstance(cur, list):
            if part.isdigit():
                idx = int(part)
                if 0 <= idx < len(cur):
                    cur = cur[idx]
                else:
                    return None
            else:
                return None
        else:
            return None
    return cur


def _as_event_id(value: Any) -> int | None:
    """
    Normalize various EventID representations to int.
    Handles int, str('4624'), dict({'#text': '4624', ...}).
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        # Common EVTX JSON shapes
        for key in ("#text", "value", "Value"):
            if key in value:
                return _as_event_id(value[key])
    return None


def _project_fields(data: dict[str, Any], fields: Sequence[str]) -> dict[str, Any]:
    """Project dotted paths from a parsed EVTX event.

    Resolution order:
        1) Resolve each path from the root `data`.
        2) If not found, try the same path relative to `data["Event"]` (legacy behavior).

    Missing paths are included with value `None`. List indices in paths are supported.
    """
    event_root = data.get("Event", {}) if isinstance(data, dict) else {}
    out: dict[str, Any] = {}
    for f in fields:
        val = _get_dotted(data, f)
        if val is None:
            val = _get_dotted(event_root, f)
        out[f] = val
    return out


# Public API
def list_evtx_files(directory: str | Path, recursive: bool = False) -> list[str]:
    """Return a list of EVTX file paths found under the given directory."""
    base = _normalize_path(directory)
    if not base.is_dir():
        return []
    iterator = base.rglob("*.evtx") if recursive else base.glob("*.evtx")
    return [str(p) for p in iterator if p.is_file()]


def iter_events_from_evtx(
    evtx_path: str | Path,
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    results_limit: int = RESULTS_LIMIT,
    scan_limit: int = SCAN_LIMIT,
    event_ids: int | str | Sequence[int] | Sequence[str] | None = None,
    contains: str | Sequence[str] | None = None,
    not_contains: str | Sequence[str] | None = None,
    fields: str | Sequence[str] | None = None,
) -> Iterable[dict[str, Any]]:
    """
    Stream parsed EVTX events (as Python dicts) matching filters.

    Time handling:
        - If both 'start' and 'end' are None: no time filter.
        - If only 'start' provided: enforce event_dt >= start.
        - If only 'end' provided:   enforce event_dt <= end.
        - If both provided:         enforce start <= event_dt <= end (swap if reversed).
        - Naive datetimes are assumed UTC (handled by normalize_timestamp).

    Filtering:
        - 'contains'/'not_contains' are case-insensitive substring checks performed on the raw JSON string.
        - 'event_ids' are normalized to ints; EventID values in JSON can be int, str, or dict.
        - 'fields' projects results to selected dotted paths (relative to the *root*), if provided.

    Yields:
        - Either full event dicts, or projected dicts if 'fields' is specified.
    """
    # Normalize path
    path = _normalize_path(evtx_path)
    if not path.is_file():
        return

    # Bound/normalize results limit, default if None/omitted, reject non-positive
    lim = normalize_int(results_limit, default=RESULTS_LIMIT)
    if lim is None:
        return
    lim = min(lim, RESULTS_LIMIT)

    # Bound/normalize scan limit, default if None/omitted, reject non-positive
    cap = normalize_int(scan_limit, default=SCAN_LIMIT)
    if cap is None:
        return
    cap = min(cap, SCAN_LIMIT)

    # Normalize to aware UTC datetimes (if provided)
    utc_now = datetime.now(timezone.utc)
    start = normalize_timestamp(start, fallback=utc_now) if start is not None else None
    end = normalize_timestamp(end, fallback=utc_now) if end is not None else None

    # Swap if both present and reversed
    if start and end and start > end:
        start, end = end, start

    # Normalize eyword filters
    contains_lc = normalize_str_list(contains, lowercase=True)
    not_contains_lc = normalize_str_list(not_contains, lowercase=True)

    # Remove overlaps to avoid contradictory filters
    if contains_lc and not_contains_lc:
        overlap = set(contains_lc) & set(not_contains_lc)
        if overlap:
            contains_lc = [s for s in contains_lc if s not in overlap]
            not_contains_lc = [s for s in not_contains_lc if s not in overlap]

    # Normalize EventIDs
    wanted_ids = set(normalize_int_list(event_ids))

    # Normalize fields
    fields_norm = (
        normalize_str_list(fields, lowercase=False) if fields is not None else None
    )

    returned = 0  # Number of records yielded
    scanned = 0  # Number of records analyzed
    parser = PyEvtxParser(str(path))

    try:
        for record in parser.records_json():
            # Respect scan cap before doing any work
            if cap is not None and scanned >= cap:
                break
            # Stop when we already returned enough
            if returned >= lim:
                break

            scanned += 1

            data_str = record.get("data")
            if not data_str or not isinstance(data_str, str):
                continue

            # Keyword include/exclude on raw payload (fast path)
            lower = data_str.lower()
            if contains_lc and not any(k in lower for k in contains_lc):
                continue
            if not_contains_lc and any(k in lower for k in not_contains_lc):
                continue

            # Parse JSON
            try:
                data = json.loads(data_str)
            except Exception:
                continue

            # EventID filter
            eid_raw = _get_dotted(data, "Event.System.EventID")
            eid = _as_event_id(eid_raw)
            if wanted_ids and (eid is None or eid not in wanted_ids):
                continue

            # Timestamp: prefer SystemTime, else fall back to record['timestamp']
            ts = _get_dotted(data, "Event.System.TimeCreated.#attributes.SystemTime")
            event_dt = normalize_timestamp(ts) or normalize_timestamp(
                record.get("timestamp")
            )
            if not event_dt:
                continue
            # Later, when filtering:
            if start and event_dt < start:
                continue
            if end and event_dt > end:
                continue

            # Projection
            if fields_norm:
                yield _project_fields(data, fields_norm)
            else:
                yield data

            returned += 1
    except Exception:
        pass


def get_events_from_evtx(
    provider: str | Path,
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    results_limit: int | str | None = RESULTS_LIMIT,
    event_ids: int | str | Sequence[int] | Sequence[str] | None = None,
    contains: str | Sequence[str] | None = None,
    not_contains: str | Sequence[str] | None = None,
    fields: str | Sequence[str] | None = None,
) -> list[str]:
    """
    Convenience wrapper that returns a list of JSON strings (UTF-8, unescaped) for callers that expect strings.
    """
    results: list[str] = []
    for ev in iter_events_from_evtx(
        evtx_path=provider,
        start=start,
        end=end,
        results_limit=results_limit,
        event_ids=event_ids,
        contains=contains,
        not_contains=not_contains,
        fields=fields,
    ):
        results.append(json.dumps(ev, ensure_ascii=False))
    return results
