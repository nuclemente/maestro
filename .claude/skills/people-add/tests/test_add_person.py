"""Testes da skill people-add."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.add_person import validate_payload  # noqa: E402


def test_validate_minimal() -> None:
    payload = validate_payload(
        {"name": "Alice", "email": "Alice@Example.COM", "relationship": "peer"}
    )
    assert payload["email"] == "alice@example.com"
    assert payload["relationship"] == "peer"


def test_validate_keeps_optional_fields() -> None:
    payload = validate_payload(
        {
            "name": "Bob",
            "email": "bob@x.com",
            "relationship": "manager",
            "role": "Tech Lead",
            "slack_id": "U999",
            "github_handle": "bob-gh",
        }
    )
    assert payload["role"] == "Tech Lead"
    assert payload["slack_id"] == "U999"
    assert payload["github_handle"] == "bob-gh"


def test_missing_required_fields() -> None:
    with pytest.raises(ValueError, match="campos obrigatórios"):
        validate_payload({"name": "X"})


def test_invalid_email() -> None:
    with pytest.raises(ValueError, match="email inválido"):
        validate_payload({"name": "X", "email": "not-email", "relationship": "peer"})


def test_invalid_relationship() -> None:
    with pytest.raises(ValueError, match="relationship inválido"):
        validate_payload({"name": "X", "email": "x@y.com", "relationship": "boss"})


def test_drops_none_optional_fields() -> None:
    payload = validate_payload(
        {
            "name": "Alice",
            "email": "a@x.com",
            "relationship": "peer",
            "role": None,
            "notes": None,
        }
    )
    assert "role" not in payload
    assert "notes" not in payload
