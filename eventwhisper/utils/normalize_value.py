from __future__ import annotations

from typing import Any

from eventwhisper.utils.normalize_wrapping_quotes import normalize_wrapping_quotes


def normalize_int(value: Any, default: int) -> int | None:
    """
    Minimal integer normalizer:
      - Accepts int or str (e.g. "10", "`10`")
      - Returns a positive int
      - Returns `default` when value is None
      - Returns None on invalid input
    """
    if value is None:
        return default

    if isinstance(value, int):
        return value if value > 0 else None

    if isinstance(value, str):
        s = normalize_wrapping_quotes(value).strip()
        try:
            i = int(s, 10)
        except Exception:
            return None
        return i if i > 0 else None

    return None
