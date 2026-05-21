"""Smoke test do endpoint /health."""

from __future__ import annotations


def test_health_returns_ok(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "maestro-backend"
    assert "env" in payload
    assert "timestamp" in payload


def test_health_emits_correlation_header(client) -> None:
    response = client.get("/health")
    assert "x-correlation-id" in response.headers
    assert len(response.headers["x-correlation-id"]) > 0


def test_skill_runner_importable() -> None:
    from app.services.skill_runner import run_skill  # noqa: F401


def test_agent_runner_importable() -> None:
    from app.services.agent_runner import AgentRunner

    runner = AgentRunner()
    assert isinstance(runner.list_agents(), list)
