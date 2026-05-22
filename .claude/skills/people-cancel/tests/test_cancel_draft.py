"""Testes da skill people-cancel."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cancel_draft import cancel_draft  # noqa: E402


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_cancel_ok() -> None:
    def handler(request):
        assert request.method == "DELETE"
        assert request.url.path == "/people/drafts/d1"
        return httpx.Response(204)

    assert cancel_draft("d1", "http://x", client=_client(handler)) is True


def test_cancel_404() -> None:
    def handler(request):
        return httpx.Response(404, json={"detail": "draft not found"})

    with pytest.raises(RuntimeError, match="not found"):
        cancel_draft("missing", "http://x", client=_client(handler))


def test_cancel_validates_id() -> None:
    with pytest.raises(ValueError):
        cancel_draft("", "http://x")
