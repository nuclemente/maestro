"""Testes da skill people-update."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.update_person import validate_update  # noqa: E402


def test_validate_minimal() -> None:
    pid, fields = validate_update({"id": "abc", "fields": {"role": "Tech Lead"}})
    assert pid == "abc"
    assert fields == {"role": "Tech Lead"}


def test_validate_normalizes_email() -> None:
    _, fields = validate_update({"id": "x", "fields": {"email": "Alice@X.COM"}})
    assert fields["email"] == "alice@x.com"


def test_validate_relationship_value() -> None:
    _, fields = validate_update({"id": "x", "fields": {"relationship": "manager"}})
    assert fields["relationship"] == "manager"


def test_missing_id() -> None:
    with pytest.raises(ValueError, match="id"):
        validate_update({"fields": {"role": "X"}})


def test_empty_fields() -> None:
    with pytest.raises(ValueError, match="fields"):
        validate_update({"id": "x", "fields": {}})


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValueError, match="não editáveis"):
        validate_update({"id": "x", "fields": {"salary": 100}})


def test_invalid_relationship() -> None:
    with pytest.raises(ValueError, match="relationship"):
        validate_update({"id": "x", "fields": {"relationship": "boss"}})
