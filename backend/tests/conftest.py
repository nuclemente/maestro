"""Fixtures pytest compartilhadas."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# SQLite em arquivo temporário (não `:memory:`) para que o TestClient enxergue
# as mesmas tabelas em todas as conexões abertas por requests sequenciais.
_TMP_DB = Path(tempfile.gettempdir()) / "maestro_pytest.db"
os.environ.setdefault("MAESTRO_DB_URL", f"sqlite:///{_TMP_DB}")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.db import engine
    from app.main import app
    from app.models import Base

    # Estado limpo por teste — drop antes para garantir migração em branco.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestClient(app)
    finally:
        Base.metadata.drop_all(bind=engine)
