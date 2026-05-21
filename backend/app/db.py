"""SQLAlchemy engine + sessão + dependência `get_db`."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base

_settings = get_settings()

engine = create_engine(
    _settings.resolved_db_url(),
    connect_args={"check_same_thread": False} if _settings.resolved_db_url().startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria as tabelas declaradas em `Base.metadata`. Usado apenas em dev/testes;
    em produção use Alembic."""
    Base.metadata.create_all(bind=engine)
