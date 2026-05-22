"""Skill people-show — GET /people/{id} ou /people/by-email/{email}."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0


def format_person(p: dict[str, Any]) -> str:
    """Render legível de uma pessoa. Pura."""
    lines = [f"{p.get('name', '?')} ({p.get('relationship', '?')})"]
    for key in ("email", "role", "slack_id", "jira_account_id", "github_handle", "start_date"):
        value = p.get(key)
        if value:
            lines.append(f"  {key}: {value}")
    if p.get("notes"):
        lines.append(f"  notes: {p['notes']}")
    return "\n".join(lines)


def resolve_url(base_url: str, *, person_id: str | None, email: str | None) -> str:
    base = base_url.rstrip("/")
    if person_id:
        return f"{base}/people/{person_id}"
    if email:
        return f"{base}/people/by-email/{email.strip().lower()}"
    raise ValueError("informe 'id' ou 'email' em $ARGUMENTS")


def fetch_person(
    *,
    person_id: str | None = None,
    email: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    url = resolve_url(base_url, person_id=person_id, email=email)
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.get(url)
        if resp.status_code == 404:
            raise RuntimeError("person not found")
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mostra uma pessoa do Maestro.")
    parser.add_argument("--payload", required=True, help="JSON com 'id' ou 'email'.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        person = fetch_person(
            person_id=raw.get("id"),
            email=raw.get("email"),
            base_url=args.base_url,
            timeout_s=args.timeout,
        )
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps({"ok": True, "data": person, "formatted": format_person(person)}, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
