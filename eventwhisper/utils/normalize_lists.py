from __future__ import annotations

import json
from collections.abc import Iterable as AbcIterable
from typing import Any

from eventwhisper.utils.normalize_wrapping_quotes import normalize_wrapping_quotes


def _is_seq(value: Any) -> bool:
    return isinstance(value, AbcIterable) and not isinstance(
        value, str | bytes | bytearray
    )


def _split_multi(s: str) -> list[str]:
    return [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]


def _maybe_load_json_array(s: str) -> list[Any] | None:
    if s.startswith("[") and s.endswith("]"):
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return arr
        except Exception:
            pass
    return None


def normalize_int_list(value: Any) -> list[int]:
    """
    Normalize many shapes into a list[int].

    Accepts:
      - None                          -> []
      - int                           -> [int]
      - str "1" / "'1'" / "`1`"       -> [1]
      - str "1, 2; '03'"              -> [1, 2, 3]
      - str JSON array "[1, \"02\"]"  -> [1, 2]
      - iterable of str/int           -> [ints...]
    Ignores non-integer tokens. De-duplicates while preserving order.
    """
    if value is None:
        return []

    out: list[int] = []
    seen: set[int] = set()

    def add_number(n: int) -> None:
        if n not in seen:
            seen.add(n)
            out.append(n)

    def handle_token(tok: Any) -> None:
        # Accept plain ints but ignore bools (bool is a subclass of int)
        if isinstance(tok, int) and not isinstance(tok, bool):
            add_number(tok)
            return

        s = normalize_wrapping_quotes(str(tok)).strip()
        if not s:
            return

        # JSON array string?
        arr = _maybe_load_json_array(s)
        if arr is not None:
            for el in arr:
                handle_token(el)
            return

        # Comma/semicolon-separated string; normalize EACH token before parsing
        parts = _split_multi(s) or [s]
        for p in parts:
            p_norm = normalize_wrapping_quotes(p).strip()
            if not p_norm:
                continue
            body = p_norm.lstrip("+-")
            if body.isdigit():
                try:
                    add_number(int(p_norm))
                except Exception:
                    pass

    if _is_seq(value):
        for item in value:
            handle_token(item)
    else:
        handle_token(value)

    return out


def normalize_str_list(value: Any, *, lowercase: bool = False) -> list[str]:
    """
    Normalize many shapes into a list[str].

    Accepts:
      - None                          -> []
      - str "alpha" / "'alpha'"       -> ["alpha"]
      - str '"a", "b"; `c`'           -> ["a", "b", "c"]
      - str JSON array '["A","b"]'    -> ["A", "b"] (or lowercased)
      - iterable of str/any           -> [str(...)...]
    Strips whitespace and surrounding quotes/backticks, drops empties,
    de-duplicates (order-preserving). Optionally lowercases.
    """
    if value is None:
        return []

    out: list[str] = []
    seen: set[str] = set()

    def add_token(txt: str) -> None:
        s = normalize_wrapping_quotes(txt).strip()
        if not s:
            return
        s = s.lower() if lowercase else s
        if s not in seen:
            seen.add(s)
            out.append(s)

    def handle_token(tok: Any) -> None:
        s = normalize_wrapping_quotes(str(tok)).strip()
        if not s:
            return

        arr = _maybe_load_json_array(s)
        if arr is not None:
            for el in arr:
                handle_token(el)
            return

        parts = _split_multi(s) or [s]
        for p in parts:
            add_token(p)

    if _is_seq(value):
        for item in value:
            handle_token(item)
    else:
        handle_token(value)

    return out
