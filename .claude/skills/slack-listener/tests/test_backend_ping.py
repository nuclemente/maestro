"""Testes do `backend_ping` — função pura via cliente httpx injetado.

Rodam isolados sem subir o backend. Para executar:

    python -m pytest .claude/agents/slack-listener/tests -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

# Permite `import scripts.backend_ping` quando rodando direto via pytest.
SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from scripts.backend_ping import ping, main  # noqa: E402


def _mock_client(handler) -> httpx.Client:
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


def test_ping_returns_ok_envelope_on_2xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "service": "maestro-backend",
                "env": "test",
                "timestamp": "2026-05-21T00:00:00Z",
            },
        )

    with _mock_client(handler) as client:
        result = ping("http://127.0.0.1:8001", client=client)

    assert result["ok"] is True
    assert result["data"]["service"] == "maestro-backend"
    assert result["data"]["status"] == "ok"


def test_ping_returns_error_envelope_on_5xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="boom")

    with _mock_client(handler) as client:
        result = ping("http://127.0.0.1:8001", client=client)

    assert result["ok"] is False
    assert "backend_unreachable" in result["error"]


def test_ping_returns_error_when_backend_offline() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with _mock_client(handler) as client:
        result = ping("http://127.0.0.1:8001", client=client)

    assert result["ok"] is False
    assert result["error"].startswith("backend_unreachable")


def test_main_writes_json_to_stdout(monkeypatch, capsys) -> None:
    def fake_ping(base_url: str, *, timeout_s: float = 5.0, client=None):  # noqa: ARG001
        return {"ok": True, "data": {"status": "ok"}}

    monkeypatch.setattr("scripts.backend_ping.ping", fake_ping)

    rc = main(["--base-url", "http://x", "--timeout", "1.0"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())

    assert rc == 0
    assert payload == {"ok": True, "data": {"status": "ok"}}


def test_main_returns_nonzero_on_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "scripts.backend_ping.ping",
        lambda *a, **k: {"ok": False, "error": "down"},
    )

    rc = main([])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == 1
    assert payload == {"ok": False, "error": "down"}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
