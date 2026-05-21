"""Fixtures pytest compartilhadas."""

from __future__ import annotations

import os

import pytest

# Garante que o engine SQLAlchemy fique em memória durante os testes,
# sem tocar no `data/maestro.db` real.
os.environ.setdefault("MAESTRO_DB_URL", "sqlite:///:memory:")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
