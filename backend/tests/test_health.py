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


def test_slack_listener_skill_is_discoverable() -> None:
    """A skill `slack-listener` (executada pelo /loop do Claude Code) precisa
    estar descobrível desde a base, com tools MCP do Slack e scripts puros."""
    from pathlib import Path

    from app.config import get_settings
    from app.services.skill_runner import _parse_skill_md, _skill_dir

    skill_dir = _skill_dir("slack-listener")
    frontmatter, _ = _parse_skill_md(skill_dir / "SKILL.md")

    assert frontmatter["name"] == "slack-listener"
    assert any(
        t.startswith("mcp__plugin_slack_slack__")
        for t in frontmatter.get("allowed-tools", [])
    ), "slack-listener precisa de pelo menos uma tool MCP do Slack"

    settings = get_settings()
    root = Path(settings.project_root)
    assert (root / settings.skills_dir / "slack-listener" / "scripts" / "backend_ping.py").is_file()
    assert (root / settings.skills_dir / "slack-listener" / "scripts" / "parse_command.py").is_file()


def test_slack_channel_id_not_in_config() -> None:
    """O channel_id privado é dado sensível: NÃO entra em config.yaml nem em Settings.

    Convenção: vive em MEMORY.md (gitignored). A skill consulta MEMORY.md
    diretamente no contexto do Claude Code — não há lookup no backend.
    """
    from app.config import get_settings

    settings = get_settings()
    assert not hasattr(settings, "slack"), (
        "settings.slack não pode existir: canal Slack é dado sensível e "
        "vive em MEMORY.md, não em config.yaml."
    )
