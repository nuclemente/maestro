"""Testes da skill oneonone-add-topic."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.add_topic import (  # noqa: E402
    _pick_next_planned,
    build_topic_payload,
    resolve_person_ref,
)


def test_build_topic_minimal() -> None:
    out = build_topic_payload({"title": "  Carreira  "})
    assert out == {"title": "Carreira", "source": "manual"}


def test_build_topic_with_body() -> None:
    out = build_topic_payload({"title": "X", "body": "  detalhes  "})
    assert out == {"title": "X", "body": "detalhes", "source": "manual"}


def test_build_topic_missing_title() -> None:
    with pytest.raises(ValueError, match="title é obrigatório"):
        build_topic_payload({"body": "só corpo"})


def test_build_topic_title_too_long() -> None:
    with pytest.raises(ValueError, match="300 caracteres"):
        build_topic_payload({"title": "x" * 301})


def test_resolve_person_ref_email_and_uuid() -> None:
    assert resolve_person_ref("ana@x.com") == ("email", "ana@x.com")
    uuid = "11111111-2222-3333-4444-555555555555"
    assert resolve_person_ref(uuid) == ("id", uuid)


def test_pick_next_planned_picks_earliest_scheduled() -> None:
    sessions = [
        {"id": "a", "status": "planned", "scheduled_at": "2026-07-01T10:00:00Z"},
        {"id": "b", "status": "planned", "scheduled_at": "2026-06-15T10:00:00Z"},
        {"id": "c", "status": "done", "scheduled_at": "2026-05-01T10:00:00Z"},
    ]
    assert _pick_next_planned(sessions)["id"] == "b"


def test_pick_next_planned_handles_null_scheduled() -> None:
    sessions = [
        {"id": "a", "status": "planned", "scheduled_at": None},
        {"id": "b", "status": "planned", "scheduled_at": "2026-06-15T10:00:00Z"},
    ]
    # `b` deve ser escolhido pois tem data; `a` (adhoc) vai pro fim.
    assert _pick_next_planned(sessions)["id"] == "b"


def test_pick_next_planned_returns_none() -> None:
    assert _pick_next_planned([{"id": "x", "status": "done"}]) is None
