from eventwhisper.utils.normalize_value import normalize_int


def test_none_returns_default():
    assert normalize_int(None, default=10) == 10


def test_positive_int_returns_itself():
    assert normalize_int(7, default=10) == 7


def test_zero_returns_none():
    assert normalize_int(0, default=10) is None


def test_negative_int_returns_none():
    assert normalize_int(-5, default=10) is None


def test_numeric_string_returns_int():
    assert normalize_int("42", default=10) == 42


def test_numeric_string_with_spaces_returns_int():
    assert normalize_int("   8  ", default=10) == 8


def test_backticked_numeric_string_returns_int():
    assert normalize_int("`12`", default=10) == 12


def test_single_quoted_numeric_string_returns_int():
    assert normalize_int("'9'", default=10) == 9


def test_double_quoted_numeric_string_returns_int():
    assert normalize_int('"15"', default=10) == 15


def test_plus_signed_string_returns_int():
    assert normalize_int("+5", default=10) == 5


def test_negative_string_returns_none():
    assert normalize_int("-3", default=10) is None


def test_invalid_string_returns_none():
    assert normalize_int("ten", default=10) is None


def test_non_string_non_int_returns_none():
    assert normalize_int(12.34, default=10) is None
