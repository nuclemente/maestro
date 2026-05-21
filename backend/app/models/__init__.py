"""Base declarativa do SQLAlchemy. Modelos de feature são adicionados nos próprios módulos."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


__all__ = ["Base"]
