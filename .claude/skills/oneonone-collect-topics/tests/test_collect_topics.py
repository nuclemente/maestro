"""Testes da skill oneonone-collect-topics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.collect_topics import build_dm_context, render_dm_template  # noqa: E402


def test_build_dm_context_with_date() -> None:
    ctx = build_dm_context(
        {"name": "Ana"}, {"scheduled_at": "2026-06-12T10:00:00Z"}
    )
    assert ctx["person_name"] == "Ana"
    assert ctx["session_date"] == "2026-06-12"
    assert ctx["next_session_human"] == "em 2026-06-12"


def test_build_dm_context_without_date() -> None:
    ctx = build_dm_context({"name": "Ana"}, {"scheduled_at": None})
    assert ctx["next_session_human"] == "ainda sem data"
    assert ctx["session_date"] == ""


def test_render_template_replaces_placeholders() -> None:
    template = "Oi {{person_name}}! Próxima: {{next_session_human}}."
    out = render_dm_template(template, {"person_name": "Ana", "next_session_human": "em 12/Jun"})
    assert out == "Oi Ana! Próxima: em 12/Jun."


def test_render_template_missing_placeholder_becomes_empty() -> None:
    template = "Oi {{person_name}}! {{em_name}} disse oi."
    out = render_dm_template(template, {"person_name": "Ana"})
    assert out == "Oi Ana!  disse oi."


def test_render_template_case_insensitive_keys() -> None:
    template = "Oi {{PERSON_NAME}}!"
    out = render_dm_template(template, {"PERSON_NAME": "Ana"})
    assert "Ana" in out
