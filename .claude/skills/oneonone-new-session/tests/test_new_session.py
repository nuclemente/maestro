"""Testes da skill oneonone-new-session."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.new_session import (  # noqa: E402
    build_session_payload,
    format_created,
    normalize_scheduled_at,
    resolve_person_ref,
)


def test_normalize_iso_passthrough() -> None:
    out = normalize_scheduled_at("2026-06-12T10:00:00+00:00")
    assert out.startswith("2026-06-12T10:00:00")


def test_normalize_iso_with_z() -> None:
    out = normalize_scheduled_at("2026-06-12T10:00:00Z")
    assert out.startswith("2026-06-12T10:00:00")


def test_normalize_human_format() -> None:
    out = normalize_scheduled_at("2026-06-12 10:00")
    assert out.startswith("2026-06-12T10:00:00")


def test_normalize_date_only() -> None:
    out = normalize_scheduled_at("2026-06-12")
    assert out.startswith("2026-06-12T00:00:00")


def test_normalize_empty_returns_none() -> None:
    assert normalize_scheduled_at("") is None
    assert normalize_scheduled_at(None) is None
    assert normalize_scheduled_at("   ") is None


def test_normalize_invalid_raises() -> None:
    with pytest.raises(ValueError, match="scheduled_at"):
        normalize_scheduled_at("not-a-date")


def test_build_session_default_status_planned() -> None:
    out = build_session_payload({})
    assert out == {"scheduled_at": None, "status": "planned"}


def test_build_session_accepts_done() -> None:
    out = build_session_payload({"status": "done", "scheduled_at": "2026-06-12"})
    assert out["status"] == "done"
    assert out["scheduled_at"].startswith("2026-06-12T")


def test_build_session_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        build_session_payload({"status": "wip"})


def test_format_created_with_date() -> None:
    out = format_created("Ana", {"scheduled_at": "2026-06-12T10:00:00+00:00"})
    assert "Ana" in out
    assert "2026-06-12 10:00" in out


def test_format_created_without_date() -> None:
    out = format_created("Ana", {"scheduled_at": None})
    assert "sem data" in out


def test_resolve_ref_uuid_and_email() -> None:
    assert resolve_person_ref("ana@x.com") == ("email", "ana@x.com")
    assert resolve_person_ref("11111111-2222-3333-4444-555555555555") == (
        "id",
        "11111111-2222-3333-4444-555555555555",
    )
