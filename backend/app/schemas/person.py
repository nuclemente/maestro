"""Schemas Pydantic para Person e PersonDraft.

Validação de e-mail é feita manualmente (regex simples) para evitar a dep
extra `email-validator` que o `EmailStr` do pydantic exige.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.person import RelationshipType

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        raise ValueError("email não pode ser vazio")
    if not _EMAIL_RE.match(cleaned):
        raise ValueError(f"email inválido: {value!r}")
    return cleaned


class PersonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., max_length=200)
    relationship: RelationshipType
    role: str | None = Field(default=None, max_length=120)
    slack_id: str | None = Field(default=None, max_length=40)
    jira_account_id: str | None = Field(default=None, max_length=80)
    github_handle: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    notes: str | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        return _normalize_email(v)  # type: ignore[return-value]


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=200)
    relationship: RelationshipType | None = None
    role: str | None = Field(default=None, max_length=120)
    slack_id: str | None = Field(default=None, max_length=40)
    jira_account_id: str | None = Field(default=None, max_length=80)
    github_handle: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    notes: str | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str | None) -> str | None:
        return _normalize_email(v)


class PersonRead(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class PersonDraftCreate(PersonBase):
    source: str = Field(default="manual", max_length=40)


class PersonDraftUpdate(PersonUpdate):
    """Update parcial de draft. Mesmos campos editáveis que `PersonUpdate`."""


class PersonDraftRead(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    proposed_at: datetime
