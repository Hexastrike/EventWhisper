from __future__ import annotations

import re
from datetime import datetime, timezone

from eventwhisper.utils.normalize_wrapping_quotes import normalize_wrapping_quotes

_Z_REMOVE_UTC = re.compile(r"\s*UTC$", re.IGNORECASE)
_Z_OFFSET_COLONLESS = re.compile(r"([+-]\d{2})(\d{2})$")  # +HHMM → +HH:MM


def normalize_timestamp(
    value: datetime | str | None,
    *,
    fallback: datetime | None = None,
) -> datetime | None:
    """
    Normalize many timestamp shapes into a UTC-aware datetime.

    Accepts:
      - datetime: naive -> assume UTC; aware -> convert to UTC
      - str:
          'YYYY-MM-DD HH:MM:SS[.ffffff][ UTC]'
          'YYYY-MM-DDTHH:MM:SS[.ffffff]Z'
          'YYYY-MM-DDTHH:MM:SS[.ffffff][±HH:MM]'
          'YYYY-MM-DD HH:MM:SS[.ffffff]'
          'YYYY-MM-DD'
      - String may be wrapped in quotes/backticks or triple backticks.
    Returns:
      - UTC-aware datetime on success, fallback on failure (or None if no fallback provided)
    """
    if value is None:
        return fallback

    if isinstance(value, datetime):
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )

    if not isinstance(value, str):
        return fallback

    s = normalize_wrapping_quotes(value)

    # Allow trailing " UTC" (case-insensitive)
    if s.upper().endswith(" UTC"):
        s = s[: -len(" UTC")]

    # Accept trailing Z as +00:00
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    # 1) Try ISO8601 (handles offsets like +00:00)
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        # 2) Space-separated formats (with/without fractional), else date-only
        try:
            if " " in s and ":" in s:
                if "." in s:
                    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return fallback

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt
