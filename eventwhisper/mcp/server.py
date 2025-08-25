"""
EventWhisper — MCP server for Windows Event Logs
================================================

This module exposes TWO MCP tools:

1) list_evtx_files
   - List *.evtx files in a directory (optionally recursive).
   - Returns: list[str] of file paths.

2) filter_evtx_events
   - Filter Windows Event Log records with optional time bounds, Event IDs, keyword
     filters, and *field projection* (via dotted paths).
   - Returns: list[str] where each element is a JSON string of a single event (full
     event or projection).

How to run (locally)
--------------------
    poetry run python -m eventwhisper.mcp.server

Claude Desktop config (example)
-------------------------------
Add to your Claude config:
{
  "mcpServers": {
    "eventwhisper": {
      "command": "python",
      "args": ["-m", "eventwhisper.mcp.server"]
    }
  }
}

Calling the tools (quick examples)
----------------------------------
Use tool "list_evtx_files" with:
{"directory":"C:\\PicoCTF\\Event-Viewing","recursive":true}

Use tool "filter_evtx_events" with:
{
  "provider": "C:\\PicoCTF\\Event-Viewing\\Security.evtx",
  "results_limit": 25,
  "event_ids": [4624, 4625],
  "fields": [
    "Event.System.EventID",
    "Event.System.TimeCreated.#attributes.SystemTime",
    "Event.EventData.TargetUserName",
    "Event.EventData.IpAddress",
    "Event.EventData.LogonType"
  ]
}

IMPORTANT: fields MUST be dotted paths under `Event.*`
------------------------------------------------------
Common mappings you’ll want:

- Timestamp
  Event.System.TimeCreated.#attributes.SystemTime

- Event ID
  Event.System.EventID

- Logon-related fields
  Event.EventData.TargetUserName
  Event.EventData.IpAddress
  Event.EventData.WorkstationName
  Event.EventData.SourceNetworkAddress
  Event.EventData.LogonType

- Process creation (4688)
  Event.EventData.SubjectUserName
  Event.EventData.NewProcessName
  Event.EventData.CommandLine

Time filtering semantics (handled by IO layer)
----------------------------------------------
- If BOTH `start` and `end` are omitted: no time filter.
- If ONLY `start` is provided: include events where event_time >= start.
- If ONLY `end` is provided:   include events where event_time <= end.
- If BOTH provided: inclusive range [start, end] (swapped if reversed).

Parameters & normalization
--------------------------
The IO layer is defensive. It accepts strings (even with backticks/quotes) for many
parameters and normalizes them. You can safely pass:
- provider: "C:\\path\\to\\file.evtx" or "`C:\\path\\to\\file.evtx`"
- results_limit:  "10" or "`10`" or 10
- event_ids: "[4624,4672]" or "`[4624,4672]`" or [4624, 4672]
- contains / not_contains: a string or a JSON list

One-shot, summary-friendly prompts (for your recording)
-------------------------------------------------------
- “List all EVTX files in C:\\PicoCTF\\Event-Viewing (recursive).”
- “Show 5 recent events from C:\\PicoCTF\\Event-Viewing\\Windows_Logs.evtx and summarize by EventID.”
- “Find suspicious logons in Security.evtx (4625 failed, 4672 admin, 4624 LogonType 10). Show time, user, IP, then summarize counts by EventID and user.”
- “RDP-only view from Security.evtx (LogonType 10). Show time, TargetUserName, LogonType, IpAddress (latest 50).”
- “Process creations (4688) with powershell/cmd/rundll32/regsvr32/mshta. Show time, user, NewProcessName, CommandLine (limit 50), then summarize by process and user.”
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

# Alias the IO-layer functions to avoid name clashes
from eventwhisper.evtxio.evtxio import (
    get_events_from_evtx as _get_events_from_evtx_impl,
)
from eventwhisper.evtxio.evtxio import (
    list_evtx_files as _list_evtx_files_impl,
)

mcp = FastMCP("EventWhisper")


def _list_evtx_files_tool(directory: str, recursive: bool = False) -> list[str]:
    """List .evtx files under a directory."""
    return _list_evtx_files_impl(directory, recursive=recursive)


def _get_events_from_evtx_tool(
    provider: str | Path,
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    results_limit: int | str | None = None,
    event_ids: int | str | Sequence[int] | Sequence[str] | None = None,
    contains: str | Sequence[str] | None = None,
    not_contains: str | Sequence[str] | None = None,
    fields: str | Sequence[str] | None = None,
) -> list[str]:
    """Pass-through to IO layer. All normalization is handled by eventwhisper.evtxio.evtxio."""
    kwargs: dict = {"provider": provider}
    if start is not None:
        kwargs["start"] = start
    if end is not None:
        kwargs["end"] = end
    if results_limit is not None:
        kwargs["results_limit"] = results_limit
    if event_ids is not None:
        kwargs["event_ids"] = event_ids
    if contains is not None:
        kwargs["contains"] = contains
    if not_contains is not None:
        kwargs["not_contains"] = not_contains
    if fields is not None:
        kwargs["fields"] = fields

    return _get_events_from_evtx_impl(**kwargs)


# Register tools with distinct variable names to avoid F811
MCP_LIST_EVTX_FILES = mcp.tool(name="list_evtx_files")(_list_evtx_files_tool)
MCP_FILTER_EVTX_EVENTS = mcp.tool(name="filter_evtx_events")(_get_events_from_evtx_tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
