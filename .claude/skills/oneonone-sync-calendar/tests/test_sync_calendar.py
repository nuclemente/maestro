"""Testes da skill oneonone-sync-calendar."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.sync_calendar import (  # noqa: E402
    extract_oneonone_events,
    match_candidates,
)


def _ev(eid: str, summary: str, start: str, attendees, status: str = "confirmed") -> dict:
    return {
        "id": eid,
        "summary": summary,
        "start": {"dateTime": start},
        "attendees": [{"email": e} for e in attendees],
        "status": status,
    }


EM = "rodrigo@example.com"


def test_extract_filters_by_title_prefix() -> None:
    events = [
        _ev("e1", "1:1 Ana", "2026-06-12T10:00:00Z", [EM, "ana@x.com"]),
        _ev("e2", "Sprint planning", "2026-06-12T11:00:00Z", [EM]),
        _ev("e3", "1:1 com Bob", "2026-06-13T10:00:00Z", [EM, "bob@x.com"]),
    ]
    out = extract_oneonone_events(events, EM)
    assert [c["external_event_id"] for c in out] == ["e1", "e3"]


def test_extract_picks_attendee_distinct_from_em() -> None:
    events = [_ev("e1", "1:1 Ana", "2026-06-12T10:00:00Z", [EM, "ana@x.com"])]
    out = extract_oneonone_events(events, EM)
    assert out[0]["attendee_email"] == "ana@x.com"


def test_extract_marks_cancelled() -> None:
    events = [
        _ev("e1", "1:1 Ana", "2026-06-12T10:00:00Z", [EM, "ana@x.com"], status="cancelled")
    ]
    out = extract_oneonone_events(events, EM)
    assert out[0]["status"] == "cancelled"


def test_extract_handles_event_without_attendee() -> None:
    events = [_ev("e1", "1:1", "2026-06-12T10:00:00Z", [EM])]
    out = extract_oneonone_events(events, EM)
    assert out[0]["attendee_email"] is None


def test_match_returns_upserts_and_unmatched() -> None:
    candidates = [
        {
            "external_event_id": "e1",
            "scheduled_at": "2026-06-12T10:00:00Z",
            "status": "planned",
            "attendee_email": "ana@x.com",
        },
        {
            "external_event_id": "e2",
            "scheduled_at": "2026-06-13T10:00:00Z",
            "status": "planned",
            "attendee_email": "beto@externo.com",
        },
    ]
    people = [{"id": "p-ana", "email": "ana@x.com"}]
    matched, unmatched = match_candidates(candidates, people)
    assert len(matched) == 1
    assert matched[0]["person_id"] == "p-ana"
    assert unmatched == ["beto@externo.com"]


def test_match_skips_empty_attendee() -> None:
    candidates = [
        {
            "external_event_id": "e1",
            "scheduled_at": "2026-06-12T10:00:00Z",
            "status": "planned",
            "attendee_email": None,
        }
    ]
    matched, unmatched = match_candidates(candidates, [])
    assert matched == []
    assert unmatched == [""]
