"""Modelos `Person` e `PersonDraft` — cadastro central de pessoas de interesse.

`Person` é fonte de verdade. Futuras features (1:1s, transcrições, feedbacks)
referenciam pela FK em `id`. `PersonDraft` é um buffer transient para propostas
do agente enriquecedor; promove para `Person` após confirmação do EM.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class RelationshipType(str, enum.Enum):
    direct_report = "direct_report"
    peer = "peer"
    manager = "manager"
    skip_level = "skip_level"
    stakeholder = "stakeholder"
    other = "other"


def _uuid() -> str:
    return str(uuid.uuid4())


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    relationship: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type"), nullable=False
    )
    slack_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    jira_account_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    github_handle: Mapped[str | None] = mapped_column(String(80), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PersonDraft(Base):
    __tablename__ = "person_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    relationship: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type"), nullable=False
    )
    slack_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    jira_account_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    github_handle: Mapped[str | None] = mapped_column(String(80), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual")
    proposed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
