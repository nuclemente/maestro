"""Testes do router /people e endpoints de drafts."""

from __future__ import annotations


def _payload(email: str = "alice@example.com", **overrides) -> dict:
    base = {
        "name": "Alice",
        "email": email,
        "relationship": "direct_report",
        "role": "Senior SWE",
        "slack_id": "U001",
        "jira_account_id": "557058:abc",
        "github_handle": "alice-gh",
        "start_date": "2025-01-15",
        "notes": "primeira contratação do squad",
    }
    base.update(overrides)
    return base


def test_create_and_list_person(client) -> None:
    resp = client.post("/people", json=_payload())
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["id"]
    assert created["email"] == "alice@example.com"
    assert created["relationship"] == "direct_report"

    listed = client.get("/people").json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]


def test_email_uniqueness(client) -> None:
    client.post("/people", json=_payload())
    dup = client.post("/people", json=_payload(name="Outra"))
    assert dup.status_code == 409


def test_invalid_email_rejected(client) -> None:
    resp = client.post("/people", json=_payload(email="not-an-email"))
    assert resp.status_code == 422


def test_filter_by_relationship(client) -> None:
    client.post("/people", json=_payload(email="a@x.com", relationship="direct_report"))
    client.post("/people", json=_payload(email="b@x.com", name="Bob", relationship="peer"))

    peers = client.get("/people", params={"relationship": "peer"}).json()
    assert len(peers) == 1
    assert peers[0]["email"] == "b@x.com"


def test_search_query(client) -> None:
    client.post("/people", json=_payload(email="alice@x.com", name="Alice Lima"))
    client.post("/people", json=_payload(email="bob@x.com", name="Bob Souza"))

    hits = client.get("/people", params={"q": "alice"}).json()
    assert len(hits) == 1
    assert hits[0]["name"] == "Alice Lima"


def test_get_update_delete(client) -> None:
    created = client.post("/people", json=_payload()).json()
    pid = created["id"]

    got = client.get(f"/people/{pid}").json()
    assert got["name"] == "Alice"

    patched = client.patch(f"/people/{pid}", json={"role": "Tech Lead"}).json()
    assert patched["role"] == "Tech Lead"

    deleted = client.delete(f"/people/{pid}")
    assert deleted.status_code == 204
    assert client.get(f"/people/{pid}").status_code == 404


def test_get_by_email(client) -> None:
    client.post("/people", json=_payload(email="case@x.com"))
    found = client.get("/people/by-email/case@x.com")
    assert found.status_code == 200
    assert found.json()["email"] == "case@x.com"


def test_draft_lifecycle(client) -> None:
    draft = client.post(
        "/people/drafts",
        json={
            "name": "Carlos",
            "email": "carlos@example.com",
            "relationship": "peer",
            "source": "agent:people",
        },
    )
    assert draft.status_code == 201, draft.text
    did = draft.json()["id"]

    listed = client.get("/people/drafts").json()
    assert len(listed) == 1

    confirmed = client.post(f"/people/drafts/{did}/confirm")
    assert confirmed.status_code == 201, confirmed.text
    person = confirmed.json()
    assert person["email"] == "carlos@example.com"

    # Draft removido após confirmação.
    assert client.get(f"/people/drafts/{did}").status_code == 404
    assert client.get("/people/drafts").json() == []


def test_draft_dedup_returns_existing_with_200(client) -> None:
    """Idempotência: POST /people/drafts com e-mail já em draft pendente
    devolve 200 + draft existente, não cria duplicata."""
    first = client.post(
        "/people/drafts",
        json={"name": "Dani", "email": "dani@x.com", "relationship": "peer"},
    )
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = client.post(
        "/people/drafts",
        json={"name": "Dani 2", "email": "dani@x.com", "relationship": "manager"},
    )
    assert second.status_code == 200, second.text  # NÃO 201, NÃO 409
    assert second.json()["id"] == first_id  # mesmo registro
    assert client.get("/people/drafts").json().__len__() == 1


def test_draft_patch(client) -> None:
    draft = client.post(
        "/people/drafts",
        json={"name": "Edu", "email": "edu@x.com", "relationship": "stakeholder"},
    ).json()

    patched = client.patch(
        f"/people/drafts/{draft['id']}",
        json={"role": "PM", "notes": "skip-level alterado"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["role"] == "PM"
    assert body["notes"] == "skip-level alterado"


def test_confirm_draft_conflicts_with_existing_email(client) -> None:
    client.post("/people", json=_payload(email="conflict@x.com"))
    draft = client.post(
        "/people/drafts",
        json={"name": "Dup", "email": "conflict@x.com", "relationship": "stakeholder"},
    ).json()

    resp = client.post(f"/people/drafts/{draft['id']}/confirm")
    assert resp.status_code == 409


def test_cancel_draft(client) -> None:
    draft = client.post(
        "/people/drafts",
        json={"name": "Cancel", "email": "cancel@x.com", "relationship": "other"},
    ).json()

    resp = client.delete(f"/people/drafts/{draft['id']}")
    assert resp.status_code == 204
    assert client.get(f"/people/drafts/{draft['id']}").status_code == 404
