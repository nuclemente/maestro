"""Testes da skill oneonone-close-collection."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.close_collection import pick_awaiting_for_person  # noqa: E402


def test_pick_returns_none_when_no_match() -> None:
    assert pick_awaiting_for_person([], "p1") is None
    assert (
        pick_awaiting_for_person(
            [{"id": "r1", "person_id": "p2", "status": "awaiting", "created_at": "2026"}],
            "p1",
        )
        is None
    )


def test_pick_filters_only_awaiting() -> None:
    requests = [
        {"id": "r1", "person_id": "p1", "status": "closed", "created_at": "2026-05-01"},
        {"id": "r2", "person_id": "p1", "status": "awaiting", "created_at": "2026-05-10"},
    ]
    assert pick_awaiting_for_person(requests, "p1")["id"] == "r2"


def test_pick_returns_most_recent() -> None:
    requests = [
        {"id": "r1", "person_id": "p1", "status": "awaiting", "created_at": "2026-05-01"},
        {"id": "r2", "person_id": "p1", "status": "awaiting", "created_at": "2026-05-10"},
    ]
    assert pick_awaiting_for_person(requests, "p1")["id"] == "r2"
