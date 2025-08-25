from __future__ import annotations

from pathlib import Path

from eventwhisper.evtxio.evtxio import list_evtx_files


def test_nonexistent_directory_returns_empty():
    assert list_evtx_files("C:\\this\\path\\should\\not\\exist\\ever") == []


def test_empty_directory_returns_empty(tmp_path: Path):
    assert list_evtx_files(tmp_path) == []


def test_filters_only_evtx_files(tmp_path: Path):
    a = tmp_path / "a.evtx"
    b = tmp_path / "b.txt"
    c = tmp_path / "c.log"
    a.touch()
    b.touch()
    c.touch()

    results = list_evtx_files(tmp_path)
    assert set(results) == {str(a)}
    assert all(isinstance(p, str) for p in results)


def test_recursive_flag_controls_subdirs(tmp_path: Path):
    top_evtx = tmp_path / "top.evtx"
    subdir = tmp_path / "sub"
    subdir.mkdir()
    nested_evtx = subdir / "nested.evtx"
    top_evtx.touch()
    nested_evtx.touch()

    # Non-recursive: only top-level file
    nonrec = set(list_evtx_files(tmp_path, recursive=False))
    assert nonrec == {str(top_evtx)}

    # Recursive: includes nested files
    rec = set(list_evtx_files(tmp_path, recursive=True))
    assert rec == {str(top_evtx), str(nested_evtx)}


def test_accepts_path_object_and_string_equivalents(tmp_path: Path):
    # As Path
    (tmp_path / "one.evtx").touch()
    path_results = set(list_evtx_files(tmp_path))

    # As str
    str_results = set(list_evtx_files(str(tmp_path)))

    assert path_results == str_results == {str(tmp_path / "one.evtx")}


def test_strips_surrounding_quotes_and_backticks(tmp_path: Path):
    target = tmp_path / "quoted.evtx"
    target.touch()

    # With backticks
    backticked = f"`{tmp_path}`"
    res_bt = set(list_evtx_files(backticked))
    assert res_bt == {str(target)}

    # With single quotes
    single_quoted = f"'{tmp_path}'"
    res_sq = set(list_evtx_files(single_quoted))
    assert res_sq == {str(target)}

    # With double quotes
    double_quoted = f'"{tmp_path}"'
    res_dq = set(list_evtx_files(double_quoted))
    assert res_dq == {str(target)}


def test_file_path_instead_of_directory_returns_empty(tmp_path: Path):
    file_path = tmp_path / "not_a_dir.evtx"
    file_path.touch()
    assert list_evtx_files(file_path) == []
