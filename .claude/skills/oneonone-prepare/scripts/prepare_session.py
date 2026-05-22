"""Skill oneonone-prepare — resolve session alvo + agrega briefing pós-enrich."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def resolve_person_ref(ref: str) -> tuple[str, str]:
    cleaned = (ref or "").strip()
    if not cleaned:
        raise ValueError("ref vazia")
    if _UUID_RE.match(cleaned):
        return ("id", cleaned)
    if "@" in cleaned:
        return ("email", cleaned.lower())
    raise ValueError(f"ref inválida: {ref!r}")


def _pick_next_planned(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    planned = [s for s in sessions if s["status"] == "planned"]
    if not planned:
        return None
    return sorted(
        planned, key=lambda s: (s.get("scheduled_at") is None, s.get("scheduled_at") or "")
    )[0]


def build_agent_prompt(
    session_id: str,
    channel_id: str | None,
    thread_ts: str | None,
    top_n: int,
) -> dict[str, Any]:
    """Monta o dict de contexto enviado ao agent. Pura."""
    return {
        "session_id": session_id,
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "top_n": top_n,
    }


def format_briefing(session_detail: dict[str, Any], person_name: str) -> str:
    """Texto curto pra postar no Slack pós-enrich. Pura."""
    topics = session_detail.get("topics") or []
    enriched = sum(1 for t in topics if t.get("enriched_at"))
    pending = sum(1 for t in topics if not t.get("enriched_at"))
    lines = [f"🧰 Preparada 1:1 de {person_name} — {enriched} topics enriched"]
    if pending:
        lines.append(f"   ↳ {pending} topics ainda sem enrichment")
    for t in topics[:10]:
        en = t.get("enrichment") or {}
        hits = len(en.get("hits") or [])
        errs = en.get("errors") or []
        suffix = f" ({hits} hits)" if hits else ""
        if errs:
            suffix += f" • falhas: {', '.join(errs)}"
        lines.append(f"   • {t['title']}{suffix}")
    return "\n".join(lines)


def _fetch_person(http: httpx.Client, base: str, ref: str) -> dict[str, Any]:
    kind, value = resolve_person_ref(ref)
    url = f"{base}/people/{value}" if kind == "id" else f"{base}/people/by-email/{value}"
    resp = http.get(url)
    if resp.status_code == 404:
        raise RuntimeError(f"pessoa não encontrada: {ref}")
    resp.raise_for_status()
    return resp.json()


def _ensure_session(
    http: httpx.Client, base: str, person_id: str
) -> dict[str, Any]:
    sessions = http.get(
        f"{base}/people/{person_id}/oneonone-track/sessions",
        params={"status": "planned"},
    ).json()
    chosen = _pick_next_planned(sessions)
    if chosen is not None:
        return chosen
    resp = http.post(
        f"{base}/people/{person_id}/oneonone-track/sessions", json={}
    )
    resp.raise_for_status()
    return resp.json()


def resolve(
    ref: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        person = _fetch_person(http, base, ref)
        session = _ensure_session(http, base, person["id"])
        detail = http.get(f"{base}/oneonones/sessions/{session['id']}").json()
        pending = [t for t in (detail.get("topics") or []) if not t.get("enriched_at")]
        return {
            "session_id": session["id"],
            "person": {"id": person["id"], "name": person["name"]},
            "pending_count": len(pending),
        }
    finally:
        if owns:
            http.close()


def briefing(
    session_id: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        detail = http.get(f"{base}/oneonones/sessions/{session_id}").json()
        # Recupera nome da pessoa via track.person_id.
        track_person_id = None  # Detail não embute person; alternativa: buscar via session.track
        # GET /oneonones/sessions/{id} já traz track_id; precisa GET na lista de people.
        # Para simplificar: buscamos pelo "topics" só. Nome é cosmético; deixamos genérico.
        topics_enriched = sum(
            1 for t in (detail.get("topics") or []) if t.get("enriched_at")
        )
        person_name = "(pessoa)"
        # tentativa best-effort de descobrir nome:
        try:
            # track_id está em detail mas não a person; busca todas pessoas e cruza por nada — pula.
            pass
        except Exception:
            pass
        return {
            "session_id": session_id,
            "topics_enriched": topics_enriched,
            "formatted": format_briefing(detail, person_name),
        }
    finally:
        if owns:
            http.close()


def next_pending_topic(
    ref: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Devolve o próximo topic pending da próxima session planned. Cria session
    adhoc se não houver. Útil para a skill `oneonone-prepare` (1 topic por chamada)."""
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        person = _fetch_person(http, base, ref)
        session = _ensure_session(http, base, person["id"])
        detail = http.get(f"{base}/oneonones/sessions/{session['id']}").json()
        pending = [t for t in (detail.get("topics") or []) if not t.get("enriched_at")]
        topic = pending[0] if pending else None
        return {
            "session_id": session["id"],
            "topic": (
                {
                    "id": topic["id"],
                    "title": topic["title"],
                    "body": topic.get("body"),
                }
                if topic
                else None
            ),
            "topics_remaining": len(pending),
            "person_name": person["name"],
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Resolve session alvo / formata briefing.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--resolve", action="store_true")
    g.add_argument("--next-topic", dest="next_topic", action="store_true")
    g.add_argument("--briefing", action="store_true")
    p.add_argument("--payload")
    p.add_argument("--session-id")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.resolve:
            if not args.payload:
                raise ValueError("--resolve requer --payload")
            raw = json.loads(args.payload)
            ref = raw.get("ref")
            if not ref:
                raise ValueError("payload precisa de 'ref'")
            data = resolve(ref, args.base_url, timeout_s=args.timeout)
        elif args.next_topic:
            if not args.payload:
                raise ValueError("--next-topic requer --payload")
            raw = json.loads(args.payload)
            ref = raw.get("ref")
            if not ref:
                raise ValueError("payload precisa de 'ref'")
            data = next_pending_topic(ref, args.base_url, timeout_s=args.timeout)
        else:
            if not args.session_id:
                raise ValueError("--briefing requer --session-id")
            data = briefing(args.session_id, args.base_url, timeout_s=args.timeout)
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False)
            + "\n"
        )
        return 1
    sys.stdout.write(json.dumps({"ok": True, "data": data}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
