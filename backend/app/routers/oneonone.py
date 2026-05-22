"""Routers do ecossistema de 1:1.

Dois prefixos:
- `/people/{person_id}/oneonone-track`   — track lazy (cria se não existe)
- `/oneonones/...`                       — endpoints de session/topic/transcript/
                                            action-item/collection-request

Sem `cadence` no modelo: a agenda real vem do Google Calendar (`oneonone-sync-calendar`
faz upsert via `external_event_id`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging import get_logger
from app.models.oneonone import (
    ActionItemOwner,
    ActionItemStatus,
    CollectionStatus,
    OneOnOneActionItem,
    OneOnOneCollectionRequest,
    OneOnOneSession,
    OneOnOneTopic,
    OneOnOneTrack,
    OneOnOneTranscript,
    SessionStatus,
    TopicSource,
)
from app.models.person import Person
from app.schemas.oneonone import (
    AnalysisPayload,
    CalendarSessionUpsert,
    EnrichmentPayload,
    OneOnOneActionItemRead,
    OneOnOneActionItemUpdate,
    OneOnOneCollectionIngest,
    OneOnOneCollectionRequestCreate,
    OneOnOneCollectionRequestRead,
    OneOnOneSessionCreate,
    OneOnOneSessionDetail,
    OneOnOneSessionRead,
    OneOnOneSessionUpdate,
    OneOnOneTopicCreate,
    OneOnOneTopicRead,
    OneOnOneTopicUpdate,
    OneOnOneTrackRead,
    OneOnOneTrackUpdate,
    OneOnOneTranscriptRead,
    OneOnOneTranscriptUpsert,
)

log = get_logger(__name__)

# Routers separados — um sob `/people/{id}/oneonone-track`, outro sob `/oneonones`.
track_router = APIRouter(prefix="/people/{person_id}/oneonone-track", tags=["oneonone"])
core_router = APIRouter(prefix="/oneonones", tags=["oneonone"])


# ---------- helpers ----------


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_person_or_404(db: Session, person_id: str) -> Person:
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="person not found")
    return person


def _get_or_create_track(db: Session, person_id: str) -> OneOnOneTrack:
    _get_person_or_404(db, person_id)
    track = db.scalar(select(OneOnOneTrack).where(OneOnOneTrack.person_id == person_id))
    if track is None:
        track = OneOnOneTrack(person_id=person_id)
        db.add(track)
        db.commit()
        db.refresh(track)
        log.info("oneonone.track.created", track_id=track.id, person_id=person_id)
    return track


def _get_session_or_404(db: Session, session_id: str) -> OneOnOneSession:
    sess = db.get(OneOnOneSession, session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="session not found")
    return sess


def _get_topic_or_404(db: Session, topic_id: str) -> OneOnOneTopic:
    topic = db.get(OneOnOneTopic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="topic not found")
    return topic


def _build_session_detail(db: Session, sess: OneOnOneSession) -> OneOnOneSessionDetail:
    topics = list(
        db.scalars(
            select(OneOnOneTopic)
            .where(OneOnOneTopic.session_id == sess.id)
            .order_by(OneOnOneTopic.created_at.asc())
        ).all()
    )
    transcript = db.scalar(
        select(OneOnOneTranscript).where(OneOnOneTranscript.session_id == sess.id)
    )
    transcript_read: OneOnOneTranscriptRead | None = None
    if transcript is not None:
        items = list(
            db.scalars(
                select(OneOnOneActionItem)
                .where(OneOnOneActionItem.transcript_id == transcript.id)
                .order_by(OneOnOneActionItem.created_at.asc())
            ).all()
        )
        transcript_read = OneOnOneTranscriptRead.model_validate(
            {
                **{c.name: getattr(transcript, c.name) for c in transcript.__table__.columns},
                "action_items": [OneOnOneActionItemRead.model_validate(i) for i in items],
            }
        )
    return OneOnOneSessionDetail.model_validate(
        {
            **{c.name: getattr(sess, c.name) for c in sess.__table__.columns},
            "topics": [OneOnOneTopicRead.model_validate(t) for t in topics],
            "transcript": transcript_read,
        }
    )


# ---------- Track ----------


@track_router.get("", response_model=OneOnOneTrackRead)
def get_track(person_id: str, db: Session = Depends(get_db)) -> OneOnOneTrack:
    return _get_or_create_track(db, person_id)


@track_router.patch("", response_model=OneOnOneTrackRead)
def update_track(
    person_id: str,
    payload: OneOnOneTrackUpdate,
    db: Session = Depends(get_db),
) -> OneOnOneTrack:
    track = _get_or_create_track(db, person_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(track, field, value)
    db.commit()
    db.refresh(track)
    log.info("oneonone.track.updated", track_id=track.id, fields=list(data.keys()))
    return track


@track_router.get("/sessions", response_model=list[OneOnOneSessionRead])
def list_sessions(
    person_id: str,
    status_filter: SessionStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[OneOnOneSession]:
    track = _get_or_create_track(db, person_id)
    stmt = select(OneOnOneSession).where(OneOnOneSession.track_id == track.id)
    if status_filter is not None:
        stmt = stmt.where(OneOnOneSession.status == status_filter)
    stmt = stmt.order_by(OneOnOneSession.scheduled_at.desc().nulls_last()).limit(limit)
    return list(db.scalars(stmt).all())


@track_router.post(
    "/sessions",
    response_model=OneOnOneSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    person_id: str,
    payload: OneOnOneSessionCreate,
    db: Session = Depends(get_db),
) -> OneOnOneSession:
    track = _get_or_create_track(db, person_id)
    sess = OneOnOneSession(track_id=track.id, **payload.model_dump())
    db.add(sess)
    db.commit()
    db.refresh(sess)
    log.info(
        "oneonone.session.created",
        session_id=sess.id,
        track_id=track.id,
        scheduled_at=sess.scheduled_at.isoformat() if sess.scheduled_at else None,
        external_event_id=sess.external_event_id,
    )
    return sess


@track_router.post(
    "/sessions/upsert-external",
    response_model=OneOnOneSessionRead,
)
def upsert_external_session(
    person_id: str,
    payload: CalendarSessionUpsert,
    db: Session = Depends(get_db),
) -> OneOnOneSession:
    """Usado pela skill `oneonone-sync-calendar`. Idempotente por `external_event_id`."""
    track = _get_or_create_track(db, person_id)
    sess = db.scalar(
        select(OneOnOneSession).where(
            OneOnOneSession.external_event_id == payload.external_event_id
        )
    )
    if sess is None:
        sess = OneOnOneSession(
            track_id=track.id,
            scheduled_at=payload.scheduled_at,
            status=payload.status,
            external_event_id=payload.external_event_id,
        )
        db.add(sess)
        action = "created"
    else:
        sess.scheduled_at = payload.scheduled_at
        sess.status = payload.status
        action = "updated"
    db.commit()
    db.refresh(sess)
    log.info(
        "oneonone.session.synced",
        session_id=sess.id,
        external_event_id=sess.external_event_id,
        action=action,
    )
    return sess


# ---------- Session ----------


@core_router.get("/sessions/{session_id}", response_model=OneOnOneSessionDetail)
def get_session_detail(session_id: str, db: Session = Depends(get_db)) -> OneOnOneSessionDetail:
    sess = _get_session_or_404(db, session_id)
    return _build_session_detail(db, sess)


@core_router.patch("/sessions/{session_id}", response_model=OneOnOneSessionRead)
def update_session(
    session_id: str,
    payload: OneOnOneSessionUpdate,
    db: Session = Depends(get_db),
) -> OneOnOneSession:
    sess = _get_session_or_404(db, session_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(sess, field, value)
    db.commit()
    db.refresh(sess)
    log.info("oneonone.session.updated", session_id=sess.id, fields=list(data.keys()))
    return sess


@core_router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_session(session_id: str, db: Session = Depends(get_db)) -> Response:
    sess = _get_session_or_404(db, session_id)
    db.delete(sess)
    db.commit()
    log.info("oneonone.session.deleted", session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Topic ----------


@core_router.post(
    "/sessions/{session_id}/topics",
    response_model=OneOnOneTopicRead,
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    session_id: str,
    payload: OneOnOneTopicCreate,
    db: Session = Depends(get_db),
) -> OneOnOneTopic:
    _get_session_or_404(db, session_id)
    topic = OneOnOneTopic(session_id=session_id, **payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    log.info(
        "oneonone.topic.created",
        topic_id=topic.id,
        session_id=session_id,
        source=topic.source.value,
    )
    return topic


@core_router.patch("/topics/{topic_id}", response_model=OneOnOneTopicRead)
def update_topic(
    topic_id: str,
    payload: OneOnOneTopicUpdate,
    db: Session = Depends(get_db),
) -> OneOnOneTopic:
    topic = _get_topic_or_404(db, topic_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    log.info("oneonone.topic.updated", topic_id=topic.id, fields=list(data.keys()))
    return topic


@core_router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_topic(topic_id: str, db: Session = Depends(get_db)) -> Response:
    topic = _get_topic_or_404(db, topic_id)
    db.delete(topic)
    db.commit()
    log.info("oneonone.topic.deleted", topic_id=topic_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@core_router.put("/topics/{topic_id}/enrichment", response_model=OneOnOneTopicRead)
def put_topic_enrichment(
    topic_id: str,
    payload: EnrichmentPayload,
    db: Session = Depends(get_db),
) -> OneOnOneTopic:
    topic = _get_topic_or_404(db, topic_id)
    topic.enrichment = payload.model_dump()
    topic.enriched_at = _utcnow()
    db.commit()
    db.refresh(topic)
    log.info(
        "oneonone.topic.enriched",
        topic_id=topic.id,
        hits=len(payload.hits),
        errors=payload.errors,
    )
    return topic


# ---------- Transcript ----------


@core_router.put(
    "/sessions/{session_id}/transcript",
    response_model=OneOnOneTranscriptRead,
)
def upsert_transcript(
    session_id: str,
    payload: OneOnOneTranscriptUpsert,
    db: Session = Depends(get_db),
) -> OneOnOneTranscriptRead:
    sess = _get_session_or_404(db, session_id)
    existing = db.scalar(
        select(OneOnOneTranscript).where(OneOnOneTranscript.session_id == sess.id)
    )
    if existing is None:
        transcript = OneOnOneTranscript(session_id=sess.id, raw_text=payload.raw_text)
        db.add(transcript)
        log.info("oneonone.transcript.attached", session_id=sess.id, new=True)
    else:
        transcript = existing
        if transcript.raw_text != payload.raw_text:
            transcript.raw_text = payload.raw_text
            # Marca como stale para a UI; análise não roda aqui.
            if transcript.analyzed_at is not None:
                transcript.analysis_stale = True
        log.info(
            "oneonone.transcript.attached",
            session_id=sess.id,
            new=False,
            stale=transcript.analysis_stale,
        )
    db.commit()
    db.refresh(transcript)
    items = list(
        db.scalars(
            select(OneOnOneActionItem)
            .where(OneOnOneActionItem.transcript_id == transcript.id)
            .order_by(OneOnOneActionItem.created_at.asc())
        ).all()
    )
    return OneOnOneTranscriptRead.model_validate(
        {
            **{c.name: getattr(transcript, c.name) for c in transcript.__table__.columns},
            "action_items": [OneOnOneActionItemRead.model_validate(i) for i in items],
        }
    )


@core_router.put(
    "/sessions/{session_id}/transcript/analysis",
    response_model=OneOnOneTranscriptRead,
)
def put_transcript_analysis(
    session_id: str,
    payload: AnalysisPayload,
    db: Session = Depends(get_db),
) -> OneOnOneTranscriptRead:
    """Grava análise gerada pela skill. Transacional: substitui action_items
    e cria topics `from_transcript` na próxima session planned (sem dedup)."""
    sess = _get_session_or_404(db, session_id)
    transcript = db.scalar(
        select(OneOnOneTranscript).where(OneOnOneTranscript.session_id == sess.id)
    )
    if transcript is None:
        raise HTTPException(status_code=404, detail="transcript not found for session")

    transcript.analysis = payload.model_dump(mode="json")
    transcript.analyzed_at = _utcnow()
    transcript.analysis_stale = False

    # Recria action_items: simples e idempotente para re-análises.
    for existing in db.scalars(
        select(OneOnOneActionItem).where(OneOnOneActionItem.transcript_id == transcript.id)
    ):
        db.delete(existing)
    for item in payload.action_items:
        db.add(
            OneOnOneActionItem(
                transcript_id=transcript.id,
                description=item.description,
                owner=item.owner,
            )
        )

    # Cria topics `from_transcript` na próxima session planned (mesma track).
    next_planned = db.scalar(
        select(OneOnOneSession)
        .where(
            OneOnOneSession.track_id == sess.track_id,
            OneOnOneSession.status == SessionStatus.planned,
            OneOnOneSession.id != sess.id,
        )
        .order_by(OneOnOneSession.scheduled_at.asc().nulls_last())
    )
    if next_planned is None:
        # Sem próxima planned — cria adhoc.
        next_planned = OneOnOneSession(track_id=sess.track_id)
        db.add(next_planned)
        db.flush()
    for suggested in payload.suggested_topics:
        db.add(
            OneOnOneTopic(
                session_id=next_planned.id,
                title=suggested,
                source=TopicSource.from_transcript,
            )
        )

    db.commit()
    db.refresh(transcript)
    log.info(
        "oneonone.transcript.analyzed",
        session_id=sess.id,
        transcript_id=transcript.id,
        action_items=len(payload.action_items),
        suggested_topics=len(payload.suggested_topics),
        sentiment=payload.sentiment.value,
    )

    items = list(
        db.scalars(
            select(OneOnOneActionItem)
            .where(OneOnOneActionItem.transcript_id == transcript.id)
            .order_by(OneOnOneActionItem.created_at.asc())
        ).all()
    )
    return OneOnOneTranscriptRead.model_validate(
        {
            **{c.name: getattr(transcript, c.name) for c in transcript.__table__.columns},
            "action_items": [OneOnOneActionItemRead.model_validate(i) for i in items],
        }
    )


@core_router.post(
    "/sessions/{session_id}/transcript/analyze",
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_transcript_analysis(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Dispara a skill `oneonone-analyze-transcript` em background.
    UI faz polling no GET session detail até `analyzed_at` mudar.
    """
    transcript = db.scalar(
        select(OneOnOneTranscript).where(OneOnOneTranscript.session_id == session_id)
    )
    if transcript is None:
        raise HTTPException(status_code=404, detail="transcript not found for session")

    from app.services.skill_runner import run_skill  # local import — evita ciclo

    def _job() -> None:
        try:
            run_skill(
                "oneonone-analyze-transcript",
                {"transcript_id": transcript.id, "session_id": session_id},
            )
        except Exception:
            log.exception("oneonone.transcript.analyze.failed", transcript_id=transcript.id)

    background_tasks.add_task(_job)
    log.info("oneonone.transcript.analysis_started", transcript_id=transcript.id)
    return {"ok": True, "transcript_id": transcript.id}


@core_router.patch("/action-items/{item_id}", response_model=OneOnOneActionItemRead)
def update_action_item(
    item_id: str,
    payload: OneOnOneActionItemUpdate,
    db: Session = Depends(get_db),
) -> OneOnOneActionItem:
    item = db.get(OneOnOneActionItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="action item not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    log.info(
        "oneonone.action_item.toggled",
        item_id=item.id,
        status=item.status.value,
    )
    return item


# ---------- Collection Request (Slack DM de coleta) ----------


@core_router.post(
    "/sessions/{session_id}/collection-request",
    response_model=OneOnOneCollectionRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_collection_request(
    session_id: str,
    payload: OneOnOneCollectionRequestCreate,
    db: Session = Depends(get_db),
) -> OneOnOneCollectionRequest:
    sess = _get_session_or_404(db, session_id)
    _get_person_or_404(db, payload.person_id)

    existing = db.scalar(
        select(OneOnOneCollectionRequest).where(
            OneOnOneCollectionRequest.session_id == sess.id,
            OneOnOneCollectionRequest.status == CollectionStatus.awaiting,
        )
    )
    if existing is not None:
        if not payload.force:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"collection request already awaiting for session "
                    f"(id={existing.id}); use force=true to reopen"
                ),
            )
        existing.status = CollectionStatus.closed
        db.flush()
        log.info("oneonone.collection.closed", request_id=existing.id, reason="force")

    req = OneOnOneCollectionRequest(
        session_id=sess.id,
        person_id=payload.person_id,
        slack_channel_id=payload.slack_channel_id,
        sent_message_ts=payload.sent_message_ts,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    log.info(
        "oneonone.collection.requested",
        request_id=req.id,
        session_id=sess.id,
        person_id=payload.person_id,
    )
    return req


@core_router.get(
    "/collection-requests",
    response_model=list[OneOnOneCollectionRequestRead],
)
def list_collection_requests(
    status_filter: CollectionStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[OneOnOneCollectionRequest]:
    stmt = select(OneOnOneCollectionRequest)
    if status_filter is not None:
        stmt = stmt.where(OneOnOneCollectionRequest.status == status_filter)
    stmt = stmt.order_by(OneOnOneCollectionRequest.created_at.desc())
    return list(db.scalars(stmt).all())


@core_router.post(
    "/collection-requests/{request_id}/close",
    response_model=OneOnOneCollectionRequestRead,
)
def close_collection_request(
    request_id: str, db: Session = Depends(get_db)
) -> OneOnOneCollectionRequest:
    req = db.get(OneOnOneCollectionRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="collection request not found")
    req.status = CollectionStatus.closed
    db.commit()
    db.refresh(req)
    log.info("oneonone.collection.closed", request_id=req.id, reason="explicit")
    return req


@core_router.post(
    "/collection-requests/{request_id}/ingest",
    response_model=OneOnOneCollectionRequestRead,
)
def ingest_collection_request(
    request_id: str,
    payload: OneOnOneCollectionIngest,
    db: Session = Depends(get_db),
) -> OneOnOneCollectionRequest:
    req = db.get(OneOnOneCollectionRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="collection request not found")
    if req.status != CollectionStatus.awaiting:
        raise HTTPException(status_code=409, detail="collection request is not awaiting")

    for title in payload.topics:
        db.add(
            OneOnOneTopic(
                session_id=req.session_id,
                title=title,
                source=TopicSource.slack_collection,
            )
        )
    req.last_polled_at = _utcnow()
    if payload.close:
        req.status = CollectionStatus.closed

    db.commit()
    db.refresh(req)
    log.info(
        "oneonone.collection.ingested",
        request_id=req.id,
        topics_added=len(payload.topics),
        closed=payload.close,
    )
    return req
