import json
import os
from pathlib import Path

import pytest

from eventwhisper.evtxio.evtxio import get_events_from_evtx

DEFAULT_PATH = Path(__file__).parent / "data" / "test.evtx"
TEST_EVTX = Path(os.getenv("TEST_EVTX", DEFAULT_PATH.as_posix()))


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_len():
    events = get_events_from_evtx(TEST_EVTX)
    assert len(events) == 565


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_unique_event_ids():
    events = get_events_from_evtx(TEST_EVTX, fields=["Event.System.EventID"])
    ids = []
    for e in events:
        obj = json.loads(e)
        ids.append(obj.get("Event.System.EventID"))
    ids = sorted(set(ids))
    assert ids == [1, 3, 5, 7, 10, 11, 12, 13, 19, 20, 21]


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_notepad_events_len():
    events = get_events_from_evtx(TEST_EVTX, contains=["notepad"])
    assert len(events) == 11


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_lsass_timestamp_projection():
    events = get_events_from_evtx(
        TEST_EVTX,
        contains=["lsass"],
        fields=["Event.System.TimeCreated.#attributes.SystemTime"],
    )
    assert events == [
        '{"Event.System.TimeCreated.#attributes.SystemTime": "2019-07-19T15:11:16.487990Z"}',
        '{"Event.System.TimeCreated.#attributes.SystemTime": "2019-07-19T15:11:26.642464Z"}',
    ]


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_lsass_multi_projection():
    events = get_events_from_evtx(
        TEST_EVTX,
        contains=["lsass"],
        fields=[
            "Event.System.TimeCreated.#attributes.SystemTime",
            "Event.EventData.Image",
            "Event.System.Channel",
        ],
    )
    assert events == [
        '{"Event.System.TimeCreated.#attributes.SystemTime": "2019-07-19T15:11:16.487990Z", "Event.EventData.Image": null, "Event.System.Channel": "Microsoft-Windows-Sysmon/Operational"}',
        '{"Event.System.TimeCreated.#attributes.SystemTime": "2019-07-19T15:11:26.642464Z", "Event.EventData.Image": "C:\\\\Windows\\\\System32\\\\cmd.exe", "Event.System.Channel": "Microsoft-Windows-Sysmon/Operational"}',
    ]


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_lsass_timestamp_filter_projection():
    events = get_events_from_evtx(
        TEST_EVTX,
        contains=["lsass"],
        fields=["Event.System.TimeCreated.#attributes.SystemTime"],
        end="2019-07-19 15:11:17 UTC",
    )
    assert events == [
        '{"Event.System.TimeCreated.#attributes.SystemTime": "2019-07-19T15:11:16.487990Z"}'
    ]


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_not_contains_multi():
    events = get_events_from_evtx(
        TEST_EVTX, not_contains=["ping", "powershell", "services"]
    )
    assert len(events) == 121


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_start_and_end():
    events = get_events_from_evtx(TEST_EVTX, start="2019-07-19T15:11", end="2030-01-01")
    assert len(events) == 27


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_end_after_start():
    events = get_events_from_evtx(TEST_EVTX, start="2030-01-01", end="2019-07-19T15:11")
    assert len(events) == 27


@pytest.mark.skipif(not TEST_EVTX.exists(), reason=f"{TEST_EVTX} not found")
def test_evtx_contains_not_contains_identical():
    assert (
        len(
            get_events_from_evtx(
                TEST_EVTX, contains=["foo", "bar"], not_contains=["foo", "bar"]
            )
        )
        == 565
    )
    assert (
        len(
            get_events_from_evtx(
                TEST_EVTX, contains=["Foo", "bar"], not_contains=["foo", "Bar"]
            )
        )
        == 565
    )
    assert (
        len(
            get_events_from_evtx(
                TEST_EVTX, contains="foo, bar", not_contains=["Foo", "bar"]
            )
        )
        == 565
    )
    assert (
        len(
            get_events_from_evtx(
                TEST_EVTX, contains="'foo, bar'", not_contains=["Foo", "bar"]
            )
        )
        == 565
    )
