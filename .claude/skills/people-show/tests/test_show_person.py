"""Testes da skill people-show."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.show_person import format_person, resolve_url  # noqa: E402


def test_format_minimal() -> None:
    out = format_person({"name": "Alice", "relationship": "peer", "email": "a@x.com"})
    assert "Alice (peer)" in out
    assert "email: a@x.com" in out


def test_format_full_fields() -> None:
    out = format_person(
        {
            "name": "Bob",
            "relationship": "manager",
            "email": "b@x.com",
            "role": "Director",
            "slack_id": "U1",
            "notes": "skip-level do Q1",
        }
    )
    assert "role: Director" in out
    assert "notes: skip-level do Q1" in out


def test_resolve_url_by_id() -> None:
    assert resolve_url("http://x", person_id="abc", email=None) == "http://x/people/abc"


def test_resolve_url_by_email_normalizes() -> None:
    url = resolve_url("http://x", person_id=None, email="Alice@Example.COM")
    assert url == "http://x/people/by-email/alice@example.com"


def test_resolve_url_requires_one() -> None:
    with pytest.raises(ValueError):
        resolve_url("http://x", person_id=None, email=None)
