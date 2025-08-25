from __future__ import annotations

from datetime import datetime, timedelta, timezone

from eventwhisper.utils.normalize_timestamp import normalize_timestamp


def test_normalize_none_returns_none():
    assert normalize_timestamp(None) is None


def test_normalize_none_with_fallback():
    fb = datetime(2025, 1, 1, tzinfo=timezone.utc)
    assert normalize_timestamp(None, fallback=fb) == fb


def test_normalize_naive_datetime_assume_utc():
    naive = datetime(2025, 1, 1, 2, 3, 4)
    got = normalize_timestamp(naive)
    assert got == naive.replace(tzinfo=timezone.utc)


def test_normalize_aware_datetime_to_utc():
    aware = datetime(2025, 1, 1, 2, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    got = normalize_timestamp(aware)
    assert got == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def test_normalize_date_only():
    assert normalize_timestamp("2025-01-02") == datetime(
        2025, 1, 2, tzinfo=timezone.utc
    )


def test_normalize_space_without_fraction():
    assert normalize_timestamp("2025-01-02 03:04:05") == datetime(
        2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc
    )


def test_normalize_space_with_fraction():
    assert normalize_timestamp("2025-01-02 03:04:05.123456") == datetime(
        2025, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc
    )


def test_normalize_with_trailing_utc():
    assert normalize_timestamp("2025-01-02 03:04:05.789 UTC") == datetime(
        2025, 1, 2, 3, 4, 5, 789000, tzinfo=timezone.utc
    )


def test_normalize_iso_with_z():
    assert normalize_timestamp("2025-01-02T03:04:05Z") == datetime(
        2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc
    )


def test_normalize_iso_with_offset():
    assert normalize_timestamp("2025-01-02T03:04:05.100000+02:00") == datetime(
        2025, 1, 2, 1, 4, 5, 100000, tzinfo=timezone.utc
    )


def test_normalize_strips_quotes_and_backticks():
    got1 = normalize_timestamp('`"2025-01-02 03:04:05"`')
    got2 = normalize_timestamp("`'2025-01-02T03:04:05Z'`")
    assert got1 == datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert got2 == datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


# Fallback coverage for the strptime branch (no brittle patches on C types)


def _force_fromiso_raises(monkeypatch):
    """
    Patch the module’s `datetime` symbol to a TYPE with classmethods,
    so isinstance(..., datetime) keeps working, but fromisoformat() raises.
    """
    from datetime import datetime as real_dt

    import eventwhisper.utils.normalize_timestamp as nt

    class FakeDateTime:
        @classmethod
        def fromisoformat(cls, _s: str):
            raise ValueError("boom")

        @classmethod
        def strptime(cls, s: str, fmt: str):
            return real_dt.strptime(s, fmt)

    monkeypatch.setattr(nt, "datetime", FakeDateTime, raising=True)


def test_fallback_strptime_fractional(monkeypatch):
    _force_fromiso_raises(monkeypatch)
    s = "2025-03-04 05:06:07.890123"
    got = normalize_timestamp(s)
    assert got == datetime(2025, 3, 4, 5, 6, 7, 890123, tzinfo=timezone.utc)


def test_fallback_strptime_no_fraction(monkeypatch):
    _force_fromiso_raises(monkeypatch)
    s = "2025-03-04 05:06:07"
    got = normalize_timestamp(s)
    assert got == datetime(2025, 3, 4, 5, 6, 7, tzinfo=timezone.utc)
