from eventwhisper.utils.normalize_lists import normalize_int_list, normalize_str_list


def test_normalize_int_list_variants():
    assert normalize_int_list(None) == []
    assert normalize_int_list(3) == [3]
    assert normalize_int_list("7") == [7]
    assert normalize_int_list("-11") == [-11]
    assert normalize_int_list("1, 2,03") == [1, 2, 3]
    assert normalize_int_list(["4", 5, "006"]) == [4, 5, 6]
    assert normalize_int_list(["x", "1", "y", "1"]) == [1]
    assert normalize_int_list("'42'") == [42]
    assert normalize_int_list('`1`, "2", 3') == [1, 2, 3]


def test_normalize_str_list_variants():
    assert normalize_str_list(None) == []
    assert normalize_str_list("alpha") == ["alpha"]
    assert normalize_str_list("a,b,  c") == ["a", "b", "c"]
    assert normalize_str_list([" A ", "b", "A"], lowercase=True) == ["a", "b"]
    assert normalize_str_list(["", "  ", "x"]) == ["x"]
    assert normalize_str_list('"ping.exe"') == ["ping.exe"]
    assert normalize_str_list(["'A'", "`B`", "A"], lowercase=True) == ["a", "b"]
