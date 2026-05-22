"""Testes do agente oneonone — `build_enrichment`."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.enrich_topic import build_enrichment  # noqa: E402


TOPIC = {"id": "t1", "title": "Carreira"}


def test_build_caps_per_source() -> None:
    glean = [{"title": f"G{i}", "url": f"https://g/{i}"} for i in range(5)]
    out = build_enrichment(TOPIC, glean_hits=glean, top_n=3)
    glean_only = [h for h in out["hits"] if h["source"] == "glean"]
    assert len(glean_only) == 3


def test_build_normalizes_titles_and_snippets() -> None:
    glean = [{"title": " Doc X ", "snippet": "x" * 500}]
    out = build_enrichment(TOPIC, glean_hits=glean)
    h = out["hits"][0]
    assert h["title"] == "Doc X"
    assert h["snippet"].endswith("...")
    assert len(h["snippet"]) == 300


def test_build_includes_errors_sorted_unique() -> None:
    out = build_enrichment(TOPIC, errors=["slack", "glean", "slack"])
    assert out["errors"] == ["glean", "slack"]


def test_build_handles_empty_inputs() -> None:
    out = build_enrichment(TOPIC)
    assert out["hits"] == []
    assert out["errors"] == []
    assert out["summary"] is None


def test_build_summary_trimmed_or_none() -> None:
    assert build_enrichment(TOPIC, summary="  ")["summary"] is None
    assert build_enrichment(TOPIC, summary="  ok  ")["summary"] == "ok"


def test_norm_picks_url_fallback() -> None:
    slack = [{"text": "msg sobre tema", "permalink": "https://slack/x"}]
    out = build_enrichment(TOPIC, slack_hits=slack)
    assert out["hits"][0]["url"] == "https://slack/x"
    assert "msg sobre tema" in out["hits"][0]["snippet"]
