"""Schemas Pydantic do ecossistema de 1:1."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.oneonone import (
    ActionItemOwner,
    ActionItemStatus,
    CollectionStatus,
    Sentiment,
    SessionStatus,
    TopicSource,
    TopicStatus,
)


# ---------- Track ----------


class OneOnOneTrackBase(BaseModel):
    notes: str | None = None


class OneOnOneTrackUpdate(OneOnOneTrackBase):
    pass


class OneOnOneTrackRead(OneOnOneTrackBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    person_id: str
    created_at: datetime
    updated_at: datetime


# ---------- Session ----------


class OneOnOneSessionCreate(BaseModel):
    scheduled_at: datetime | None = None
    status: SessionStatus = SessionStatus.planned
    external_event_id: str | None = Field(default=None, max_length=200)


class OneOnOneSessionUpdate(BaseModel):
    scheduled_at: datetime | None = None
    status: SessionStatus | None = None


class OneOnOneSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    track_id: str
    scheduled_at: datetime | None
    status: SessionStatus
    external_event_id: str | None
    created_at: datetime
    updated_at: datetime


# ---------- Topic ----------


class OneOnOneTopicCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str | None = None
    source: TopicSource = TopicSource.manual
    status: TopicStatus = TopicStatus.pending


class OneOnOneTopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    body: str | None = None
    status: TopicStatus | None = None


class EnrichmentHit(BaseModel):
    source: str = Field(..., max_length=40)
    title: str
    url: str | None = None
    snippet: str | None = None


class EnrichmentPayload(BaseModel):
    hits: list[EnrichmentHit] = Field(default_factory=list)
    summary: str | None = None
    errors: list[str] = Field(default_factory=list)


class OneOnOneTopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    title: str
    body: str | None
    source: TopicSource
    status: TopicStatus
    enrichment: dict[str, Any] | None
    enriched_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------- Transcript & ActionItem ----------


class OneOnOneTranscriptUpsert(BaseModel):
    raw_text: str = Field(..., min_length=1)


class AnalysisActionItem(BaseModel):
    description: str = Field(..., min_length=1)
    owner: ActionItemOwner = ActionItemOwner.em


class AnalysisPayload(BaseModel):
    """Conteúdo da análise produzida pela skill `oneonone-analyze-transcript`."""

    summary: str
    follow_ups: list[str] = Field(default_factory=list)
    sentiment: Sentiment
    suggested_topics: list[str] = Field(default_factory=list)
    action_items: list[AnalysisActionItem] = Field(default_factory=list)


class OneOnOneActionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transcript_id: str
    description: str
    owner: ActionItemOwner
    status: ActionItemStatus
    created_at: datetime
    updated_at: datetime


class OneOnOneActionItemUpdate(BaseModel):
    status: ActionItemStatus | None = None
    description: str | None = Field(default=None, min_length=1)


class OneOnOneTranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    raw_text: str
    analysis: dict[str, Any] | None
    analyzed_at: datetime | None
    analysis_stale: bool
    created_at: datetime
    updated_at: datetime
    action_items: list[OneOnOneActionItemRead] = Field(default_factory=list)


# ---------- Session detail (aggregate) ----------


class OneOnOneSessionDetail(OneOnOneSessionRead):
    topics: list[OneOnOneTopicRead] = Field(default_factory=list)
    transcript: OneOnOneTranscriptRead | None = None


# ---------- CollectionRequest ----------


class OneOnOneCollectionRequestCreate(BaseModel):
    person_id: str
    slack_channel_id: str = Field(..., max_length=64)
    sent_message_ts: str = Field(..., max_length=64)
    force: bool = False


class OneOnOneCollectionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    person_id: str
    slack_channel_id: str
    sent_message_ts: str
    status: CollectionStatus
    last_polled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IngestMessage(BaseModel):
    text: str
    ts: str = ""


class OneOnOneCollectionIngest(BaseModel):
    topics: list[str] = Field(default_factory=list)
    raw_messages: list[IngestMessage] = Field(default_factory=list)
    close: bool = False


# ---------- Calendar sync (utilizado pela skill `oneonone-sync-calendar`) ----------


class CalendarSessionUpsert(BaseModel):
    external_event_id: str = Field(..., max_length=200)
    scheduled_at: datetime
    status: SessionStatus = SessionStatus.planned
