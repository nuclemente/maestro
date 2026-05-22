"""Modelos do ecossistema de 1:1.

Hierarquia: `OneOnOneTrack` (1:1 com `Person`) → `OneOnOneSession`s → `OneOnOneTopic`s.
Cada session pode ter no máximo um `OneOnOneTranscript`, que por sua vez contém N
`OneOnOneActionItem`s. `OneOnOneCollectionRequest` registra cada DM de coleta de
temas enviada via Slack — restrito a 1 `awaiting` por session via índice condicional.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class SessionStatus(str, enum.Enum):
    planned = "planned"
    done = "done"
    cancelled = "cancelled"


class TopicStatus(str, enum.Enum):
    pending = "pending"
    discussed = "discussed"
    parked = "parked"


class TopicSource(str, enum.Enum):
    manual = "manual"
    slack_collection = "slack_collection"
    from_transcript = "from_transcript"


class CollectionStatus(str, enum.Enum):
    awaiting = "awaiting"
    closed = "closed"


class Sentiment(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    concern = "concern"


class ActionItemOwner(str, enum.Enum):
    em = "em"
    person = "person"
    other = "other"


class ActionItemStatus(str, enum.Enum):
    open = "open"
    done = "done"


def _uuid() -> str:
    return str(uuid.uuid4())


class OneOnOneTrack(Base):
    __tablename__ = "oneonone_tracks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    person_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OneOnOneSession(Base):
    __tablename__ = "oneonone_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    track_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("oneonone_tracks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        nullable=False,
        default=SessionStatus.planned,
    )
    external_event_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_sessions_track_status", "track_id", "status"),)


class OneOnOneTopic(Base):
    __tablename__ = "oneonone_topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("oneonone_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[TopicSource] = mapped_column(
        Enum(TopicSource, name="topic_source"),
        nullable=False,
        default=TopicSource.manual,
    )
    status: Mapped[TopicStatus] = mapped_column(
        Enum(TopicStatus, name="topic_status"),
        nullable=False,
        default=TopicStatus.pending,
    )
    enrichment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OneOnOneTranscript(Base):
    __tablename__ = "oneonone_transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("oneonone_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OneOnOneActionItem(Base):
    __tablename__ = "oneonone_action_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    transcript_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("oneonone_transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[ActionItemOwner] = mapped_column(
        Enum(ActionItemOwner, name="action_item_owner"),
        nullable=False,
        default=ActionItemOwner.em,
    )
    status: Mapped[ActionItemStatus] = mapped_column(
        Enum(ActionItemStatus, name="action_item_status"),
        nullable=False,
        default=ActionItemStatus.open,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OneOnOneCollectionRequest(Base):
    __tablename__ = "oneonone_collection_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("oneonone_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slack_channel_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sent_message_ts: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[CollectionStatus] = mapped_column(
        Enum(CollectionStatus, name="collection_status"),
        nullable=False,
        default=CollectionStatus.awaiting,
    )
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "uq_collection_awaiting_per_session",
            "session_id",
            unique=True,
            sqlite_where=text("status = 'awaiting'"),
        ),
    )
