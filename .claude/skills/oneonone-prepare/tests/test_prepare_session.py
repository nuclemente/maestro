"""Testes da skill oneonone-prepare."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.prepare_session import (  # noqa: E402
    build_agent_prompt,
    format_briefing,
)


def test_build_agent_prompt_includes_all_fields() -> None:
    out = build_agent_prompt("s1", "C123", "ts.1", top_n=5)
    assert out == {
        "session_id": "s1",
        "channel_id": "C123",
        "thread_ts": "ts.1",
        "top_n": 5,
    }


def test_format_briefing_counts_enriched() -> None:
    detail = {
        "topics": [
            {"title": "A", "enriched_at": "2026-05-22", "enrichment": {"hits": [{}, {}]}},
            {"title": "B", "enriched_at": None},
            {"title": "C", "enriched_at": "2026-05-22", "enrichment": {"hits": [{}, {}, {}]}},
        ]
    }
    out = format_briefing(detail, "Ana")
    assert "2 topics enriched" in out
    assert "1 topics ainda sem enrichment" in out
    assert "A" in out
    assert "(2 hits)" in out


def test_format_briefing_shows_errors() -> None:
    detail = {
        "topics": [
            {
                "title": "A",
                "enriched_at": "2026-05-22",
                "enrichment": {"hits": [{}], "errors": ["glean", "slack"]},
            }
        ]
    }
    out = format_briefing(detail, "Bob")
    assert "falhas: glean, slack" in out


def test_format_briefing_empty_session() -> None:
    out = format_briefing({"topics": []}, "Carla")
    assert "0 topics enriched" in out
