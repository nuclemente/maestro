"""Testes da skill oneonone-ingest-dms."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ingest_dms import parse_topics_from_messages, should_close  # noqa: E402

PERSON = "U_PERSON"


def test_parse_ignores_messages_before_since() -> None:
    messages = [
        {"user": PERSON, "ts": "1000.000", "text": "carreira"},
        {"user": PERSON, "ts": "1500.000", "text": "carga"},
    ]
    out = parse_topics_from_messages(messages, PERSON, "1200.000")
    assert out == ["carga"]


def test_parse_ignores_bot_messages() -> None:
    messages = [
        {"user": "U_BOT", "ts": "2000.000", "text": "Oi! me manda temas..."},
        {"user": PERSON, "ts": "2500.000", "text": "ferramentas"},
    ]
    assert parse_topics_from_messages(messages, PERSON, "1000.000") == ["ferramentas"]


def test_parse_splits_lines_and_strips_bullets() -> None:
    messages = [
        {
            "user": PERSON,
            "ts": "3000.000",
            "text": "- carreira\n* carga de trabalho\n1. roadmap\nferramentas",
        },
    ]
    out = parse_topics_from_messages(messages, PERSON, "1000.000")
    assert out == ["carreira", "carga de trabalho", "roadmap", "ferramentas"]


def test_parse_drops_negative_and_close_hints() -> None:
    messages = [
        {"user": PERSON, "ts": "3000.000", "text": "ok"},
        {"user": PERSON, "ts": "3100.000", "text": "pronto"},
        {"user": PERSON, "ts": "3200.000", "text": "carreira"},
    ]
    assert parse_topics_from_messages(messages, PERSON, "1000.000") == ["carreira"]


def test_should_close_on_keyword() -> None:
    messages = [{"user": PERSON, "ts": "3000.000", "text": "é isso, pode fechar"}]
    assert should_close(messages, PERSON, "1000.000", None) is True


def test_should_close_after_24h() -> None:
    now = datetime(2026, 5, 22, 12, 0, tzinfo=timezone.utc)
    old = "2026-05-20T11:00:00+00:00"  # +49h
    assert (
        should_close([], PERSON, "1000.000", old, now=now) is True
    )


def test_should_not_close_when_no_signal() -> None:
    messages = [{"user": PERSON, "ts": "3000.000", "text": "carreira"}]
    assert should_close(messages, PERSON, "1000.000", None) is False
