"""Testes da skill people-confirm."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.confirm_draft import confirm_draft  # noqa: E402


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_confirm_returns_person() -> None:
    def handler(request):
        assert request.url.path == "/people/drafts/d1/confirm"
        return httpx.Response(201, json={"id": "p1", "email": "a@x.com"})

    person = confirm_draft("d1", "http://x", client=_client(handler))
    assert person == {"id": "p1", "email": "a@x.com"}


def test_confirm_404() -> None:
    def handler(request):
        return httpx.Response(404, json={"detail": "draft not found"})

    with pytest.raises(RuntimeError, match="draft not found"):
        confirm_draft("missing", "http://x", client=_client(handler))


def test_confirm_409() -> None:
    def handler(request):
        return httpx.Response(409, json={"detail": "email taken"})

    with pytest.raises(RuntimeError, match="conflict"):
        confirm_draft("d1", "http://x", client=_client(handler))


def test_confirm_validates_id() -> None:
    with pytest.raises(ValueError):
        confirm_draft("", "http://x")
