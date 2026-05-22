"""Testes do router /oneonones + /people/{id}/oneonone-track."""

from __future__ import annotations


def _person_payload(email: str = "ana@example.com", **overrides) -> dict:
    base = {
        "name": "Ana",
        "email": email,
        "relationship": "direct_report",
        "slack_id": "UANA001",
    }
    base.update(overrides)
    return base


def _create_person(client, **overrides) -> dict:
    resp = client.post("/people", json=_person_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_track_lazy_create(client) -> None:
    person = _create_person(client)
    resp = client.get(f"/people/{person['id']}/oneonone-track")
    assert resp.status_code == 200
    track = resp.json()
    assert track["person_id"] == person["id"]
    # Idempotente — segundo GET devolve o mesmo track.
    resp2 = client.get(f"/people/{person['id']}/oneonone-track")
    assert resp2.json()["id"] == track["id"]


def test_track_404_for_unknown_person(client) -> None:
    resp = client.get("/people/00000000-0000-0000-0000-000000000000/oneonone-track")
    assert resp.status_code == 404


def test_session_create_and_list(client) -> None:
    person = _create_person(client)
    base = f"/people/{person['id']}/oneonone-track"

    resp = client.post(f"{base}/sessions", json={"scheduled_at": "2026-06-01T10:00:00Z"})
    assert resp.status_code == 201, resp.text
    sess_id = resp.json()["id"]

    listed = client.get(f"{base}/sessions").json()
    assert len(listed) == 1
    assert listed[0]["id"] == sess_id

    planned = client.get(f"{base}/sessions", params={"status": "planned"}).json()
    assert len(planned) == 1

    done = client.get(f"{base}/sessions", params={"status": "done"}).json()
    assert done == []


def test_session_detail_with_topics_and_transcript(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions",
        json={"scheduled_at": "2026-06-01T10:00:00Z"},
    ).json()
    sid = sess["id"]

    client.post(f"/oneonones/sessions/{sid}/topics", json={"title": "Carreira"})
    client.post(f"/oneonones/sessions/{sid}/topics", json={"title": "Projeto X", "body": "Risco no prazo"})

    client.put(
        f"/oneonones/sessions/{sid}/transcript",
        json={"raw_text": "Discutimos carreira e prazos do projeto."},
    )

    detail = client.get(f"/oneonones/sessions/{sid}").json()
    assert len(detail["topics"]) == 2
    assert detail["transcript"]["raw_text"].startswith("Discutimos")
    assert detail["transcript"]["analysis_stale"] is False


def test_topic_enrichment_put(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()
    topic = client.post(
        f"/oneonones/sessions/{sess['id']}/topics", json={"title": "Tema X"}
    ).json()

    enrichment = {
        "hits": [{"source": "glean", "title": "Doc Y", "url": "https://x", "snippet": "..."}],
        "summary": "Resumo curto",
        "errors": ["slack"],
    }
    resp = client.put(f"/oneonones/topics/{topic['id']}/enrichment", json=enrichment)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["enriched_at"] is not None
    assert body["enrichment"]["summary"] == "Resumo curto"
    assert body["enrichment"]["errors"] == ["slack"]


def test_transcript_edit_marks_stale(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()
    sid = sess["id"]

    client.put(f"/oneonones/sessions/{sid}/transcript", json={"raw_text": "Versão 1"})
    # Simula análise aplicada.
    client.put(
        f"/oneonones/sessions/{sid}/transcript/analysis",
        json={
            "summary": "ok",
            "follow_ups": [],
            "sentiment": "neutral",
            "suggested_topics": [],
            "action_items": [],
        },
    )
    after_analysis = client.get(f"/oneonones/sessions/{sid}").json()["transcript"]
    assert after_analysis["analysis_stale"] is False
    assert after_analysis["analyzed_at"] is not None

    client.put(f"/oneonones/sessions/{sid}/transcript", json={"raw_text": "Versão 2"})
    after_edit = client.get(f"/oneonones/sessions/{sid}").json()["transcript"]
    assert after_edit["analysis_stale"] is True


def test_analysis_creates_action_items_and_suggested_topics(client) -> None:
    person = _create_person(client)
    base = f"/people/{person['id']}/oneonone-track"
    done_sess = client.post(
        f"{base}/sessions", json={"scheduled_at": "2026-05-01T10:00:00Z", "status": "done"}
    ).json()
    next_sess = client.post(
        f"{base}/sessions", json={"scheduled_at": "2026-06-01T10:00:00Z"}
    ).json()

    client.put(
        f"/oneonones/sessions/{done_sess['id']}/transcript",
        json={"raw_text": "Falamos sobre X e Y."},
    )
    analysis = {
        "summary": "Conversa boa, dois follow-ups",
        "follow_ups": ["Marcar 1:1 com PM"],
        "sentiment": "positive",
        "suggested_topics": ["Roadmap Q3", "Carga de trabalho"],
        "action_items": [
            {"description": "EM revisar OKR", "owner": "em"},
            {"description": "Ana atualizar CV interno", "owner": "person"},
        ],
    }
    resp = client.put(
        f"/oneonones/sessions/{done_sess['id']}/transcript/analysis", json=analysis
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["analyzed_at"] is not None
    assert body["analysis_stale"] is False
    assert len(body["action_items"]) == 2

    # `suggested_topics` foram criados na próxima session planned.
    next_detail = client.get(f"/oneonones/sessions/{next_sess['id']}").json()
    titles = sorted(t["title"] for t in next_detail["topics"])
    assert titles == ["Carga de trabalho", "Roadmap Q3"]
    assert all(t["source"] == "from_transcript" for t in next_detail["topics"])


def test_action_item_toggle(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()
    client.put(f"/oneonones/sessions/{sess['id']}/transcript", json={"raw_text": "x"})
    client.put(
        f"/oneonones/sessions/{sess['id']}/transcript/analysis",
        json={
            "summary": "s",
            "follow_ups": [],
            "sentiment": "neutral",
            "suggested_topics": [],
            "action_items": [{"description": "Fazer A", "owner": "em"}],
        },
    )
    detail = client.get(f"/oneonones/sessions/{sess['id']}").json()
    item_id = detail["transcript"]["action_items"][0]["id"]

    resp = client.patch(f"/oneonones/action-items/{item_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_collection_request_blocks_double_open(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()

    body = {
        "person_id": person["id"],
        "slack_channel_id": "D123",
        "sent_message_ts": "1716000000.000100",
    }
    r1 = client.post(f"/oneonones/sessions/{sess['id']}/collection-request", json=body)
    assert r1.status_code == 201

    r2 = client.post(f"/oneonones/sessions/{sess['id']}/collection-request", json=body)
    assert r2.status_code == 409

    r3 = client.post(
        f"/oneonones/sessions/{sess['id']}/collection-request",
        json={**body, "sent_message_ts": "1716000100.000200", "force": True},
    )
    assert r3.status_code == 201, r3.text


def test_collection_ingest_creates_topics_and_closes(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()
    req = client.post(
        f"/oneonones/sessions/{sess['id']}/collection-request",
        json={
            "person_id": person["id"],
            "slack_channel_id": "D123",
            "sent_message_ts": "1716000000.000100",
        },
    ).json()

    resp = client.post(
        f"/oneonones/collection-requests/{req['id']}/ingest",
        json={"topics": ["carga", "ferramentas"], "close": True},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"

    detail = client.get(f"/oneonones/sessions/{sess['id']}").json()
    titles = sorted(t["title"] for t in detail["topics"])
    assert titles == ["carga", "ferramentas"]
    assert all(t["source"] == "slack_collection" for t in detail["topics"])


def test_session_upsert_external_is_idempotent(client) -> None:
    person = _create_person(client)
    base = f"/people/{person['id']}/oneonone-track"

    payload = {
        "external_event_id": "evt-abc",
        "scheduled_at": "2026-06-15T10:00:00Z",
        "status": "planned",
    }
    a = client.post(f"{base}/sessions/upsert-external", json=payload).json()
    b = client.post(
        f"{base}/sessions/upsert-external",
        json={**payload, "scheduled_at": "2026-06-15T11:00:00Z"},
    ).json()
    assert a["id"] == b["id"]
    assert b["scheduled_at"].startswith("2026-06-15T11:00:00")


def test_collection_awaiting_listing(client) -> None:
    person = _create_person(client)
    sess = client.post(
        f"/people/{person['id']}/oneonone-track/sessions", json={}
    ).json()
    client.post(
        f"/oneonones/sessions/{sess['id']}/collection-request",
        json={
            "person_id": person["id"],
            "slack_channel_id": "D123",
            "sent_message_ts": "1716000000.000100",
        },
    )
    open_reqs = client.get(
        "/oneonones/collection-requests", params={"status": "awaiting"}
    ).json()
    assert len(open_reqs) == 1
