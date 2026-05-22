"""Skill oneonone-sync-calendar — extrai eventos `1:1`, casa por e-mail e upserta sessions."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
_TITLE_PREFIX = "1:1"


def extract_oneonone_events(
    events: list[dict[str, Any]], em_email: str
) -> list[dict[str, Any]]:
    """Filtra eventos cujo título começa com `1:1` e extrai o attendee distinto do EM.

    Retorna lista de candidatos: `{external_event_id, scheduled_at, status,
    title, attendee_email}`. **Pura**.
    """
    em_email = (em_email or "").strip().lower()
    candidates: list[dict[str, Any]] = []
    for ev in events:
        title = (ev.get("summary") or "").strip()
        if not title.lower().startswith(_TITLE_PREFIX):
            continue
        start = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date")
        if not start:
            continue
        eid = ev.get("id")
        if not eid:
            continue
        attendees = ev.get("attendees") or []
        other_email = None
        for att in attendees:
            email = (att.get("email") or "").strip().lower()
            if not email or email == em_email:
                continue
            other_email = email
            break
        ev_status = (ev.get("status") or "confirmed").lower()
        session_status = "cancelled" if ev_status == "cancelled" else "planned"
        candidates.append(
            {
                "external_event_id": eid,
                "scheduled_at": start,
                "status": session_status,
                "title": title,
                "attendee_email": other_email,
            }
        )
    return candidates


def match_candidates(
    candidates: list[dict[str, Any]], people: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Casa cada candidato com `Person.email`. Retorna `(matched, unmatched_emails)`. Pura."""
    by_email = {(p.get("email") or "").lower(): p for p in people if p.get("email")}
    matched: list[dict[str, Any]] = []
    unmatched: list[str] = []
    for cand in candidates:
        email = (cand.get("attendee_email") or "").lower()
        if not email:
            unmatched.append("")
            continue
        person = by_email.get(email)
        if person is None:
            unmatched.append(email)
            continue
        matched.append(
            {
                "person_id": person["id"],
                "external_event_id": cand["external_event_id"],
                "scheduled_at": cand["scheduled_at"],
                "status": cand["status"],
            }
        )
    return matched, unmatched


def apply_upserts(
    upserts: list[dict[str, Any]],
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> int:
    """POSTa cada upsert. Retorna a contagem aplicada. Idempotente no backend."""
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    applied = 0
    try:
        for up in upserts:
            person_id = up.pop("person_id")
            resp = http.post(
                f"{base}/people/{person_id}/oneonone-track/sessions/upsert-external",
                json=up,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
            applied += 1
    finally:
        if owns:
            http.close()
    return applied


def fetch_all_people(
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.get(f"{base_url.rstrip('/')}/people")
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sync Calendar → 1:1 sessions.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract", action="store_true")
    g.add_argument("--match", action="store_true")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--payload", required=True)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        if args.extract:
            em_email = raw.get("em_email") or os.environ.get("MAESTRO_EM_EMAIL") or ""
            if not em_email:
                raise ValueError("em_email não informado (payload ou env MAESTRO_EM_EMAIL)")
            candidates = extract_oneonone_events(raw.get("events") or [], em_email)
            data = {"candidates": candidates}
        elif args.match:
            candidates = raw.get("candidates") or []
            people = raw.get("people") or fetch_all_people(
                base_url=args.base_url, timeout_s=args.timeout
            )
            matched, unmatched = match_candidates(candidates, people)
            data = {"upserts": matched, "unmatched_emails": unmatched}
        else:
            upserts = raw.get("upserts") or []
            applied = apply_upserts(
                upserts, base_url=args.base_url, timeout_s=args.timeout
            )
            data = {"sessions_upserted": applied}
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
