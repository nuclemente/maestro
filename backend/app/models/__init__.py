"""Base declarativa do SQLAlchemy. Modelos de feature são adicionados nos próprios módulos."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Importações para o Alembic descobrir os modelos via `Base.metadata`.
from app.models import person  # noqa: E402, F401
from app.models import oneonone  # noqa: E402, F401

__all__ = ["Base"]
