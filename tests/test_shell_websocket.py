"""WebSocket tests for interactive shell terminal behavior."""

from unittest.mock import AsyncMock, Mock

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from hiveden.shell.models import ShellSession, ShellType
from hiveden.shell.websocket import ShellWebSocketHandler


def _build_client_and_manager():
    """Create a test app, websocket handler, and mocked shell manager."""
    app = FastAPI()

    manager = Mock()
    manager.get_session.return_value = ShellSession(
        session_id="session-1",
        shell_type=ShellType.LOCAL,
        target="localhost",
        user="root",
        working_dir="/tmp",
        environment={},
        active=True,
        metadata={},
    )
    manager.start_interactive_session = AsyncMock()
    manager.send_interactive_input = AsyncMock()
    manager.resize_interactive_session = AsyncMock()
    manager.stop_interactive_session = AsyncMock()
    manager.close_session = Mock()

    async def empty_stream(_session_id):
        if False:
            yield None

    manager.stream_interactive_output.side_effect = empty_stream

    handler = ShellWebSocketHandler(manager)

    @app.websocket("/ws/{session_id}")
    async def ws_endpoint(websocket, session_id: str):
        await handler.handle_session(websocket, session_id)

    return TestClient(app), manager


def test_interactive_input_and_resize_messages_are_forwarded():
    """Forward terminal input and resize events to interactive manager methods."""
    client, manager = _build_client_and_manager()

    with client.websocket_connect("/ws/session-1") as ws:
        session_info = ws.receive_json()
        assert session_info["type"] == "session_info"

        ws.send_json({"type": "input", "data": "ls -la\r"})
        ws.send_json({"type": "resize", "cols": 132, "rows": 40})
        ws.send_json({"type": "close"})

        closed = ws.receive_json()
        assert closed["type"] == "session_closed"

    manager.start_interactive_session.assert_awaited_once_with(
        session_id="session-1",
        cols=120,
        rows=30,
    )
    manager.send_interactive_input.assert_awaited_with("session-1", "ls -la\r")
    manager.resize_interactive_session.assert_awaited_once_with(
        "session-1",
        cols=132,
        rows=40,
    )
    manager.close_session.assert_called_once_with("session-1")
    manager.stop_interactive_session.assert_awaited_once_with("session-1")


def test_command_message_is_translated_to_terminal_input():
    """Translate legacy command messages into interactive input + newline."""
    client, manager = _build_client_and_manager()

    with client.websocket_connect("/ws/session-1") as ws:
        _ = ws.receive_json()

        ws.send_json({"type": "command", "command": "pwd"})

        started = ws.receive_json()
        completed = ws.receive_json()
        assert started["type"] == "command_started"
        assert completed["type"] == "command_completed"

        ws.send_json({"type": "close"})
        _ = ws.receive_json()

    manager.send_interactive_input.assert_any_await("session-1", "pwd")
    manager.send_interactive_input.assert_any_await("session-1", "\n")
