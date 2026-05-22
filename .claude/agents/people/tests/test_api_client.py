"""Testes do api_client do agente people — usa MockTransport do httpx."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.api_client import confirm_draft, create_draft, list_drafts, list_people  # noqa: E402


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_create_draft_returns_id() -> None:
    captured: dict = {}

    def handler(request):
        captured["body"] = request.content
        return httpx.Response(201, json={"id": "d1", "name": "Alice"})

    out = create_draft(
        {"name": "Alice", "email": "a@x.com", "relationship": "peer"},
        "http://x",
        client=_client(handler),
    )
    assert out["id"] == "d1"
    assert b"Alice" in captured["body"]


def test_create_draft_dedup_returns_200() -> None:
    def handler(request):
        return httpx.Response(200, json={"id": "existing", "name": "Bob"})

    out = create_draft({"name": "Bob", "email": "b@x.com", "relationship": "peer"},
                       "http://x", client=_client(handler))
    assert out["id"] == "existing"


def test_list_drafts() -> None:
    def handler(request):
        assert request.url.path == "/people/drafts"
        return httpx.Response(200, json=[{"id": "d1"}, {"id": "d2"}])

    drafts = list_drafts("http://x", client=_client(handler))
    assert len(drafts) == 2


def test_list_people_with_filter() -> None:
    def handler(request):
        assert request.url.params.get("relationship") == "peer"
        return httpx.Response(200, json=[{"id": "p1"}])

    out = list_people("http://x", relationship="peer", client=_client(handler))
    assert out[0]["id"] == "p1"


def test_create_draft_raises_on_error() -> None:
    def handler(request):
        return httpx.Response(422, json={"detail": "invalid"})

    with pytest.raises(RuntimeError, match="HTTP 422"):
        create_draft({"name": ""}, "http://x", client=_client(handler))


def test_confirm_draft_returns_person() -> None:
    def handler(request):
        assert "confirm" in request.url.path
        return httpx.Response(201, json={"id": "p1", "email": "a@x.com"})

    person = confirm_draft("d1", "http://x", client=_client(handler))
    assert person["id"] == "p1"
