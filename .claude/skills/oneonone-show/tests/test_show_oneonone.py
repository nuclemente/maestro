"""Testes da skill oneonone-show."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.show_oneonone import format_briefing, resolve_person_ref  # noqa: E402


def test_resolve_uuid() -> None:
    kind, value = resolve_person_ref("11111111-2222-3333-4444-555555555555")
    assert kind == "id"
    assert value == "11111111-2222-3333-4444-555555555555"


def test_resolve_email_lowercases() -> None:
    kind, value = resolve_person_ref("  Ana@Example.COM ")
    assert kind == "email"
    assert value == "ana@example.com"


def test_resolve_invalid() -> None:
    with pytest.raises(ValueError, match="ref inválida"):
        resolve_person_ref("ana")


def test_resolve_empty() -> None:
    with pytest.raises(ValueError, match="ref vazia"):
        resolve_person_ref("")


def test_format_briefing_no_session() -> None:
    out = format_briefing({"name": "Ana"}, None, 0, None)
    assert "Ana" in out
    assert "sem sessão" in out


def test_format_briefing_with_next_and_last() -> None:
    out = format_briefing(
        {"name": "Ana"},
        {"scheduled_at": "2026-06-12T10:00:00Z"},
        2,
        {"summary": "Boa conversa sobre OKR"},
    )
    assert "próxima 2026-06-12" in out
    assert "2 topics pending" in out
    assert "Boa conversa" in out
