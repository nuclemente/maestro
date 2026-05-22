"""Skill people-add — validação pura + POST /people."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
REQUIRED = ("name", "email", "relationship")
RELATIONSHIPS = {"direct_report", "peer", "manager", "skip_level", "stakeholder", "other"}
OPTIONAL = ("role", "slack_id", "jira_account_id", "github_handle", "start_date", "notes")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Valida e normaliza o payload de cadastro. Pura."""
    if not isinstance(raw, dict):
        raise ValueError("payload precisa ser objeto JSON")

    missing = [k for k in REQUIRED if not raw.get(k)]
    if missing:
        raise ValueError(f"campos obrigatórios ausentes: {', '.join(missing)}")

    email = str(raw["email"]).strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError(f"email inválido: {raw['email']!r}")

    rel = str(raw["relationship"]).strip()
    if rel not in RELATIONSHIPS:
        raise ValueError(
            f"relationship inválido: {rel!r} (válidos: {', '.join(sorted(RELATIONSHIPS))})"
        )

    payload: dict[str, Any] = {
        "name": str(raw["name"]).strip(),
        "email": email,
        "relationship": rel,
    }
    for opt in OPTIONAL:
        if raw.get(opt) is not None:
            payload[opt] = raw[opt]
    return payload


def post_person(
    payload: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.post(base_url.rstrip("/") + "/people", json=payload)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = resp.text
            raise RuntimeError(f"HTTP {resp.status_code}: {detail}")
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cadastra uma pessoa no Maestro.")
    parser.add_argument("--payload", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        payload = validate_payload(raw)
        person = post_person(payload, args.base_url, timeout_s=args.timeout)
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    sys.stdout.write(json.dumps({"ok": True, "data": person}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
