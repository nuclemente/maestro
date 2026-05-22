"""Testes do enrich_person — função pura build_proposal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.enrich_person import build_proposal  # noqa: E402


def test_minimal_proposal() -> None:
    out = build_proposal(name="Alice", relationship="direct_report")
    assert out["name"] == "Alice"
    assert out["relationship"] == "direct_report"
    assert out["source"] == "agent:people"


def test_merges_glean_and_slack_signals() -> None:
    out = build_proposal(
        name="Bob",
        glean_hits=[{"role": "Senior SWE", "github_handle": "bob-gh", "squad": "platform"}],
        slack_hits=[{"slack_id": "U001", "email": "bob@example.com"}],
        jira_hits=[{"accountId": "557058:xyz"}],
        relationship="peer",
    )
    assert out["email"] == "bob@example.com"
    assert out["slack_id"] == "U001"
    assert out["role"] == "Senior SWE"
    assert out["github_handle"] == "bob-gh"
    assert out["jira_account_id"] == "557058:xyz"
    assert "squad: platform" in out["notes"]


def test_slack_email_takes_precedence() -> None:
    out = build_proposal(
        name="Carol",
        slack_hits=[{"email": "carol@slack.com"}],
        glean_hits=[{"email": "carol@docs.com"}],
    )
    assert out["email"] == "carol@slack.com"


def test_empty_hits_yields_no_optional_fields() -> None:
    out = build_proposal(name="Dan")
    assert "role" not in out
    assert "slack_id" not in out
    assert "github_handle" not in out
    assert out["email"] == ""
