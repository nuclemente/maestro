"""Skill oneonone-new-session — cria session manualmente para a 1:1 de uma pessoa."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_VALID_STATUS = {"planned", "done", "cancelled"}


def resolve_person_ref(ref: str) -> tuple[str, str]:
    cleaned = (ref or "").strip()
    if not cleaned:
        raise ValueError("ref vazia")
    if _UUID_RE.match(cleaned):
        return ("id", cleaned)
    if "@" in cleaned:
        return ("email", cleaned.lower())
    raise ValueError(f"ref inválida: {ref!r}")


def normalize_scheduled_at(value: Any) -> str | None:
    """Aceita None, ISO 8601, ou `YYYY-MM-DD HH:MM`. Devolve ISO ou None. Pura."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # ISO 8601 direto.
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            # Tenta `YYYY-MM-DD HH:MM` ou `YYYY-MM-DD`.
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(s, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"scheduled_at inválido: {value!r}")
        return dt.isoformat()
    raise ValueError(f"scheduled_at deve ser string ou None, veio {type(value).__name__}")


def build_session_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Valida e monta o payload da session. Pura."""
    if not isinstance(raw, dict):
        raise ValueError("payload precisa ser objeto JSON")
    status = (raw.get("status") or "planned").strip().lower()
    if status not in _VALID_STATUS:
        raise ValueError(
            f"status inválido: {status!r} (válidos: {sorted(_VALID_STATUS)})"
        )
    return {
        "scheduled_at": normalize_scheduled_at(raw.get("scheduled_at")),
        "status": status,
    }


def format_created(person_name: str, session: dict[str, Any]) -> str:
    """Linha curta pro Slack. Pura."""
    sched = session.get("scheduled_at")
    if sched:
        sched_short = sched[:16].replace("T", " ")
        return f"🗓 Nova 1:1 com {person_name} criada ({sched_short})."
    return f"🗓 Nova 1:1 com {person_name} criada (sem data)."


def _fetch_person(http: httpx.Client, base: str, ref: str) -> dict[str, Any]:
    kind, value = resolve_person_ref(ref)
    url = f"{base}/people/{value}" if kind == "id" else f"{base}/people/by-email/{value}"
    resp = http.get(url)
    if resp.status_code == 404:
        raise RuntimeError(f"pessoa não encontrada: {ref}")
    resp.raise_for_status()
    return resp.json()


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
        sess_payload = build_session_payload(payload)
        resp = http.post(
            f"{base}/people/{person['id']}/oneonone-track/sessions",
            json=sess_payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        session = resp.json()
        return {
            "session": session,
            "formatted": format_created(person["name"], session),
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Cria uma session de 1:1 manualmente.")
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
