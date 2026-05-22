"""Router /people — CRUD de pessoas + endpoints de drafts.

Drafts são idempotentes por e-mail: `POST /people/drafts` com e-mail já em
draft pendente devolve **200 + draft existente** em vez de criar duplicata
(decisão do refine — gap C4).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging import get_logger
from app.models.person import Person, PersonDraft, RelationshipType
from app.schemas.person import (
    PersonCreate,
    PersonDraftCreate,
    PersonDraftRead,
    PersonDraftUpdate,
    PersonRead,
    PersonUpdate,
)

router = APIRouter(prefix="/people", tags=["people"])
log = get_logger(__name__)


def _get_person_or_404(db: Session, person_id: str) -> Person:
    person = db.get(Person, person_id)
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="person not found")
    return person


def _get_draft_or_404(db: Session, draft_id: str) -> PersonDraft:
    draft = db.get(PersonDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="draft not found")
    return draft


# ---------- Drafts (rotas declaradas antes de /{id} para precedência) ----------


@router.get("/drafts", response_model=list[PersonDraftRead])
def list_drafts(db: Session = Depends(get_db)) -> list[PersonDraft]:
    return list(db.scalars(select(PersonDraft).order_by(PersonDraft.proposed_at.desc())).all())


@router.post("/drafts", response_model=PersonDraftRead)
def create_draft(
    payload: PersonDraftCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> PersonDraft:
    """Idempotente por e-mail — devolve 200 + existing se já houver draft pendente."""
    existing = db.scalar(select(PersonDraft).where(PersonDraft.email == payload.email))
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        log.info("people.draft.dedup", draft_id=existing.id, email=existing.email)
        return existing

    draft = PersonDraft(**payload.model_dump())
    db.add(draft)
    db.commit()
    db.refresh(draft)
    response.status_code = status.HTTP_201_CREATED
    log.info("people.draft.created", draft_id=draft.id, source=draft.source)
    return draft


@router.get("/drafts/{draft_id}", response_model=PersonDraftRead)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> PersonDraft:
    return _get_draft_or_404(db, draft_id)


@router.patch("/drafts/{draft_id}", response_model=PersonDraftRead)
def update_draft(
    draft_id: str,
    payload: PersonDraftUpdate,
    db: Session = Depends(get_db),
) -> PersonDraft:
    draft = _get_draft_or_404(db, draft_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(draft, field, value)
    db.commit()
    db.refresh(draft)
    log.info("people.draft.updated", draft_id=draft_id, fields=list(data.keys()))
    return draft


@router.post(
    "/drafts/{draft_id}/confirm",
    response_model=PersonRead,
    status_code=status.HTTP_201_CREATED,
)
def confirm_draft(draft_id: str, db: Session = Depends(get_db)) -> Person:
    draft = _get_draft_or_404(db, draft_id)

    existing = db.scalar(select(Person).where(Person.email == draft.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"person with email '{draft.email}' already exists (id={existing.id})",
        )

    person = Person(
        name=draft.name,
        email=draft.email,
        role=draft.role,
        relationship=draft.relationship,
        slack_id=draft.slack_id,
        jira_account_id=draft.jira_account_id,
        github_handle=draft.github_handle,
        start_date=draft.start_date,
        notes=draft.notes,
    )
    db.add(person)
    db.delete(draft)
    db.commit()
    db.refresh(person)
    log.info("people.draft.confirmed", draft_id=draft_id, person_id=person.id)
    return person


@router.delete(
    "/drafts/{draft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def cancel_draft(draft_id: str, db: Session = Depends(get_db)) -> Response:
    draft = _get_draft_or_404(db, draft_id)
    db.delete(draft)
    db.commit()
    log.info("people.draft.cancelled", draft_id=draft_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Pessoas ----------


@router.get("", response_model=list[PersonRead])
def list_people(
    relationship: RelationshipType | None = Query(default=None),
    q: str | None = Query(default=None, description="Busca por nome ou e-mail"),
    db: Session = Depends(get_db),
) -> list[Person]:
    stmt = select(Person)
    if relationship is not None:
        stmt = stmt.where(Person.relationship == relationship)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(Person.name.ilike(like), Person.email.ilike(like)))
    stmt = stmt.order_by(Person.name.asc())
    return list(db.scalars(stmt).all())


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def create_person(payload: PersonCreate, db: Session = Depends(get_db)) -> Person:
    existing = db.scalar(select(Person).where(Person.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"person with email '{payload.email}' already exists",
        )
    person = Person(**payload.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    log.info("people.created", person_id=person.id, relationship=person.relationship.value)
    return person


@router.get("/by-email/{email}", response_model=PersonRead)
def get_person_by_email(email: str, db: Session = Depends(get_db)) -> Person:
    person = db.scalar(select(Person).where(Person.email == email.lower()))
    if person is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="person not found")
    return person


@router.get("/{person_id}", response_model=PersonRead)
def get_person(person_id: str, db: Session = Depends(get_db)) -> Person:
    return _get_person_or_404(db, person_id)


@router.patch("/{person_id}", response_model=PersonRead)
def update_person(
    person_id: str,
    payload: PersonUpdate,
    db: Session = Depends(get_db),
) -> Person:
    person = _get_person_or_404(db, person_id)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] != person.email:
        clash = db.scalar(select(Person).where(Person.email == data["email"]))
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"another person already uses email '{data['email']}'",
            )

    for field, value in data.items():
        setattr(person, field, value)

    db.commit()
    db.refresh(person)
    log.info("people.updated", person_id=person.id, fields=list(data.keys()))
    return person


@router.delete(
    "/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_person(person_id: str, db: Session = Depends(get_db)) -> Response:
    person = _get_person_or_404(db, person_id)
    db.delete(person)
    db.commit()
    log.info("people.deleted", person_id=person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
