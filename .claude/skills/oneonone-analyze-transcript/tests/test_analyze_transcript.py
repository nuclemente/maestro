"""Testes da skill oneonone-analyze-transcript."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_transcript import (  # noqa: E402
    build_analysis_prompt,
    chunk_transcript,
    merge_analyses,
    validate_analysis_payload,
)


def test_chunk_short_returns_single() -> None:
    assert chunk_transcript("oi, tudo bem?") == ["oi, tudo bem?"]


def test_chunk_long_splits_paragraphs() -> None:
    para = "x" * 100
    text = "\n\n".join([para] * 20)
    chunks = chunk_transcript(text, max_tokens=50)  # 50 tokens ≈ 200 chars
    assert len(chunks) > 1
    assert all(len(c) <= 200 * 2 for c in chunks)  # margem para parágrafos curtos


def test_chunk_huge_paragraph_is_cut() -> None:
    text = "x" * 5000
    chunks = chunk_transcript(text, max_tokens=100)  # 100 * 4 = 400 chars
    assert all(len(c) <= 400 for c in chunks)


def test_build_prompt_includes_person_and_text() -> None:
    out = build_analysis_prompt("conversa X", "Ana")
    assert "Ana" in out
    assert "conversa X" in out
    assert "sentiment" in out


def test_build_prompt_with_prior_summary() -> None:
    out = build_analysis_prompt("conversa X", "Ana", prior_summary="último resumo")
    assert "último resumo" in out


def test_validate_minimal() -> None:
    out = validate_analysis_payload(
        {
            "summary": "ok",
            "sentiment": "neutral",
            "action_items": [],
            "follow_ups": [],
            "suggested_topics": [],
        }
    )
    assert out["summary"] == "ok"
    assert out["sentiment"] == "neutral"


def test_validate_missing_summary() -> None:
    with pytest.raises(ValueError, match="summary"):
        validate_analysis_payload({"sentiment": "neutral"})


def test_validate_invalid_sentiment() -> None:
    with pytest.raises(ValueError, match="sentiment"):
        validate_analysis_payload({"summary": "x", "sentiment": "happy"})


def test_validate_action_items_drops_missing_and_defaults_owner() -> None:
    out = validate_analysis_payload(
        {
            "summary": "x",
            "sentiment": "neutral",
            "action_items": [
                {"description": "fazer A", "owner": "em"},
                {"description": "", "owner": "person"},
                {"description": "fazer B"},
                {"description": "fazer C", "owner": "invalid"},
            ],
        }
    )
    items = out["action_items"]
    assert [i["description"] for i in items] == ["fazer A", "fazer B", "fazer C"]
    assert [i["owner"] for i in items] == ["em", "em", "em"]


def test_merge_single_part_just_validates() -> None:
    part = {"summary": "s", "sentiment": "positive"}
    merged = merge_analyses([part])
    assert merged["summary"] == "s"
    assert merged["sentiment"] == "positive"


def test_merge_concatenates_and_picks_worst_sentiment() -> None:
    parts = [
        {"summary": "p1", "sentiment": "positive"},
        {"summary": "p2", "sentiment": "concern"},
        {"summary": "p3", "sentiment": "neutral"},
    ]
    merged = merge_analyses(parts)
    assert merged["sentiment"] == "concern"
    assert "p1" in merged["summary"] and "p2" in merged["summary"]
    assert merged["summary"].startswith("(múltiplos trechos)")


def test_merge_dedups_lists() -> None:
    parts = [
        {
            "summary": "s",
            "sentiment": "neutral",
            "follow_ups": ["X"],
            "suggested_topics": ["A"],
            "action_items": [{"description": "fazer Z"}],
        },
        {
            "summary": "s2",
            "sentiment": "neutral",
            "follow_ups": ["x"],  # case-insensitive dedup
            "suggested_topics": ["A", "B"],
            "action_items": [{"description": "fazer Z"}],
        },
    ]
    merged = merge_analyses(parts)
    assert merged["follow_ups"] == ["X"]
    assert merged["suggested_topics"] == ["A", "B"]
    assert len(merged["action_items"]) == 1
