"""MCP server tests against a fake Boardly API and responder (httpx.MockTransport)."""

import asyncio
import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

import server

BOARD = {
    "columns": [
        {"id": "new", "title": "New"},
        {"id": "todo", "title": "To Do"},
        {"id": "in_progress", "title": "In Progress"},
        {"id": "done", "title": "Done"},
    ],
    "cards": [
        {"id": "c1", "title": "Write specs", "description": "x" * 1000, "column": "todo"},
        {"id": "c2", "title": "Ship", "description": "", "column": "done"},
    ],
}
seen: list[httpx.Request] = []


def handler(request: httpx.Request) -> httpx.Response:
    seen.append(request)
    path = request.url.path
    if path == "/api/board":
        return httpx.Response(200, json=BOARD)
    if path == "/api/cards" and request.method == "POST":
        body = json.loads(request.content)
        return httpx.Response(201, json={"id": "c3", **body})
    if path == "/api/cards/c1/move":
        return httpx.Response(200, json={**BOARD["cards"][0], **json.loads(request.content)})
    if path == "/api/cards/missing/move":
        return httpx.Response(404, json={"detail": "Card not found"})
    if path == "/incidents":
        return httpx.Response(200, json=[{"id": "i1", "status": "recovered"}])
    if path == "/incidents/i1":
        return httpx.Response(
            200,
            json={
                "id": "i1",
                "status": "recovered",
                "alert": {"labels": {"alertname": "Board actions failing (5xx)"}},
                "timeline": [{"at": "t", "status": "recovered", "note": "ok"}],
                "agent": {"model": "m", "cost_usd": 0.1},
            },
        )
    return httpx.Response(404, json={"detail": "not found"})


@pytest.fixture(autouse=True)
def fake_backends(monkeypatch):
    monkeypatch.setenv("BOARDLY_URL", "http://board.test")
    monkeypatch.setenv("RESPONDER_URL", "http://responder.test")
    seen.clear()
    server.configure(httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def run(coro):
    return asyncio.run(coro)


def test_get_board_counts_cards_and_clips_long_text():
    board = run(server.get_board())
    assert [c["count"] for c in board["columns"]] == [0, 1, 0, 1]
    assert len(board["cards"][0]["description"]) < 400
    assert seen[0].url == "http://board.test/api/board"


def test_create_card_strips_text_and_defaults_to_new():
    card = run(server.create_card("  Idea  "))
    assert card == {"id": "c3", "title": "Idea", "description": "", "column": "new"}


def test_create_card_rejects_empty_title_without_calling_the_api():
    with pytest.raises(ToolError):
        run(server.create_card("   "))
    assert seen == []


def test_move_card_reports_api_errors_as_tool_errors():
    assert run(server.move_card("c1", "done"))["column"] == "done"
    with pytest.raises(ToolError, match="404"):
        run(server.move_card("missing", "done"))


def test_ids_are_validated_before_building_urls():
    with pytest.raises(ToolError):
        run(server.move_card("../board", "done"))
    with pytest.raises(ToolError):
        run(server.get_incident("../../etc/passwd"))
    assert seen == []


def test_incident_tools_read_the_responder():
    assert run(server.list_incidents()) == [{"id": "i1", "status": "recovered"}]
    incident = run(server.get_incident("i1"))
    assert incident["alert"] == {"alertname": "Board actions failing (5xx)"}
    assert incident["agent"]["cost_usd"] == 0.1


def test_there_is_no_delete_tool():
    names = {t.name for t in run(server.mcp.list_tools())}
    assert names == {"get_board", "create_card", "move_card", "list_incidents", "get_incident"}
