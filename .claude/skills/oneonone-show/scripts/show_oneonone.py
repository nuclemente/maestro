"""Skill oneonone-show — briefing rápido da Track de 1:1 de uma pessoa."""

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
    """Decide se a ref é id (UUID) ou email. Pura."""
    cleaned = (ref or "").strip()
    if not cleaned:
        raise ValueError("ref vazia")
    if _UUID_RE.match(cleaned):
        return ("id", cleaned)
    if "@" in cleaned:
        return ("email", cleaned.lower())
    raise ValueError(f"ref inválida: {ref!r} (use UUID ou e-mail)")


def format_briefing(
    person: dict[str, Any],
    next_session: dict[str, Any] | None,
    topics_pending: int,
    last_done: dict[str, Any] | None,
) -> str:
    """Monta uma linha curta para o Slack. Pura."""
    name = person.get("name", "?")
    if next_session is None:
        prox = "sem sessão agendada"
    else:
        sched = next_session.get("scheduled_at")
        prox = f"próxima {sched[:10]}" if sched else "próxima (sem data)"
    base = f"🎯 1:1 com {name} — {prox} • {topics_pending} topics pending"
    if last_done and last_done.get("summary"):
        base += f"\n   · último: {last_done['summary'][:120]}"
    return base


def _fetch_person(
    kind: str, ref: str, base_url: str, http: httpx.Client
) -> dict[str, Any]:
    url = (
        f"{base_url}/people/{ref}" if kind == "id" else f"{base_url}/people/by-email/{ref}"
    )
    resp = http.get(url)
    if resp.status_code == 404:
        raise RuntimeError(f"pessoa não encontrada: {ref}")
    resp.raise_for_status()
    return resp.json()


def _fetch_briefing(
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
        kind, value = resolve_person_ref(ref)
        person = _fetch_person(kind, value, base, http)
        track = http.get(f"{base}/people/{person['id']}/oneonone-track").json()
        sessions_planned = http.get(
            f"{base}/people/{person['id']}/oneonone-track/sessions",
            params={"status": "planned"},
        ).json()
        sessions_done = http.get(
            f"{base}/people/{person['id']}/oneonone-track/sessions",
            params={"status": "done", "limit": 1},
        ).json()

        # Próxima planned = a com scheduled_at mais cedo (lista vem ordenada desc).
        next_sess = None
        if sessions_planned:
            next_sess = sorted(
                sessions_planned,
                key=lambda s: (s.get("scheduled_at") is None, s.get("scheduled_at") or ""),
            )[0]

        topics_pending = 0
        if next_sess is not None:
            detail = http.get(f"{base}/oneonones/sessions/{next_sess['id']}").json()
            topics_pending = sum(
                1 for t in detail.get("topics", []) if t["status"] == "pending"
            )

        last_done = None
        if sessions_done:
            done_detail = http.get(
                f"{base}/oneonones/sessions/{sessions_done[0]['id']}"
            ).json()
            transcript = done_detail.get("transcript") or {}
            analysis = transcript.get("analysis") or {}
            last_done = {
                "id": sessions_done[0]["id"],
                "scheduled_at": sessions_done[0].get("scheduled_at"),
                "summary": analysis.get("summary"),
            }

        formatted = format_briefing(person, next_sess, topics_pending, last_done)
        return {
            "person": {"id": person["id"], "name": person["name"], "email": person["email"]},
            "track": {"id": track["id"], "notes": track.get("notes")},
            "next_session": next_sess,
            "topics_pending": topics_pending,
            "last_done": last_done,
            "formatted": formatted,
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Briefing de 1:1 para uma pessoa.")
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
        data = _fetch_briefing(ref, args.base_url, timeout_s=args.timeout)
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
