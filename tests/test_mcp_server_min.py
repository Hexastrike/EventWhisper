import eventwhisper.mcp.server as server


def test_list_evtx_files_passthrough(monkeypatch):
    calls = {}

    def fake_list(directory, recursive=False):
        calls["directory"] = directory
        calls["recursive"] = recursive
        return ["a.evtx"]

    # Patch the IO impl the wrapper calls
    monkeypatch.setattr(server, "_list_evtx_files_impl", fake_list)

    out = server._list_evtx_files_tool(r"C:\logs", recursive=True)
    assert out == ["a.evtx"]
    assert calls == {"directory": r"C:\logs", "recursive": True}


def test_filter_evtx_events_provider_only(monkeypatch):
    captured = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return ["ok"]

    # Patch the IO impl the wrapper calls
    monkeypatch.setattr(server, "_get_events_from_evtx_impl", fake_get)

    out = server._get_events_from_evtx_tool(provider="Security.evtx")
    assert out == ["ok"]
    assert captured == {"provider": "Security.evtx"}


def test_tools_registered():
    assert server.mcp.get_tool("list_evtx_files") is not None
    assert server.mcp.get_tool("filter_evtx_events") is not None
