"""Testes da skill people-list."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.list_people import format_people  # noqa: E402


def test_format_empty() -> None:
    assert format_people([]) == "(nenhuma pessoa cadastrada)"


def test_format_with_role() -> None:
    items = [{"name": "Alice", "relationship": "direct_report", "role": "Senior SWE"}]
    out = format_people(items)
    assert "Alice" in out
    assert "direct_report" in out
    assert "Senior SWE" in out


def test_format_without_role() -> None:
    items = [{"name": "Bob", "relationship": "peer"}]
    out = format_people(items)
    assert out.startswith("• Bob (peer)")
    assert "—" not in out
