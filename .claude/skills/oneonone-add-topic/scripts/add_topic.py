"""Skill oneonone-add-topic — adiciona topic manual à próxima session planned."""

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


def build_topic_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Valida e normaliza o payload do topic. Pura."""
    if not isinstance(raw, dict):
        raise ValueError("payload precisa ser objeto JSON")
    title = (raw.get("title") or "").strip()
    if not title:
        raise ValueError("title é obrigatório")
    if len(title) > 300:
        raise ValueError("title acima de 300 caracteres")
    out: dict[str, Any] = {"title": title, "source": "manual"}
    body = raw.get("body")
    if body:
        out["body"] = str(body).strip()
    return out


def _pick_next_planned(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pega a session planned com `scheduled_at` mais cedo (None vai pro fim). Pura."""
    planned = [s for s in sessions if s["status"] == "planned"]
    if not planned:
        return None
    return sorted(
        planned, key=lambda s: (s.get("scheduled_at") is None, s.get("scheduled_at") or "")
    )[0]


def _fetch_person(http: httpx.Client, base: str, ref: str) -> dict[str, Any]:
    kind, value = resolve_person_ref(ref)
    url = f"{base}/people/{value}" if kind == "id" else f"{base}/people/by-email/{value}"
    resp = http.get(url)
    if resp.status_code == 404:
        raise RuntimeError(f"pessoa não encontrada: {ref}")
    resp.raise_for_status()
    return resp.json()


def _ensure_planned_session(
    http: httpx.Client, base: str, person_id: str
) -> tuple[dict[str, Any], bool]:
    """Retorna (session, created_adhoc)."""
    sessions = http.get(
        f"{base}/people/{person_id}/oneonone-track/sessions",
        params={"status": "planned"},
    ).json()
    chosen = _pick_next_planned(sessions)
    if chosen is not None:
        return chosen, False
    created = http.post(
        f"{base}/people/{person_id}/oneonone-track/sessions", json={}
    )
    created.raise_for_status()
    return created.json(), True


def _run(
    ref: str,
    payload: dict[str, Any],
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
        topic_payload = build_topic_payload(payload)
        session, created_adhoc = _ensure_planned_session(http, base, person["id"])
        resp = http.post(
            f"{base}/oneonones/sessions/{session['id']}/topics", json=topic_payload
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        topic = resp.json()
        formatted = f"✅ Tema '{topic['title']}' adicionado à 1:1 de {person['name']}"
        if created_adhoc:
            formatted += " (session adhoc criada)"
        return {
            "topic": topic,
            "session": session,
            "created_session": created_adhoc,
            "formatted": formatted,
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Adiciona um topic manual à próxima 1:1.")
    p.add_argument("--payload", required=True)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        ref = raw.get("ref") or raw.get("id") or raw.get("email")
        if not ref:
            raise ValueError("payload precisa de 'ref' (id ou email)")
        data = _run(ref, raw, args.base_url, timeout_s=args.timeout)
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
