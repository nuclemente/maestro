"""Skill people-update — validação pura + PATCH /people/{id}."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0

EDITABLE = {
    "name", "email", "relationship", "role", "slack_id",
    "jira_account_id", "github_handle", "start_date", "notes",
}
RELATIONSHIPS = {"direct_report", "peer", "manager", "skip_level", "stakeholder", "other"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_update(raw: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Valida payload de update. Retorna (person_id, fields). Pura."""
    if not isinstance(raw, dict):
        raise ValueError("payload precisa ser objeto JSON")

    person_id = raw.get("id")
    if not person_id or not isinstance(person_id, str):
        raise ValueError("campo 'id' é obrigatório (string)")

    fields = raw.get("fields") or {}
    if not isinstance(fields, dict) or not fields:
        raise ValueError("campo 'fields' precisa ser objeto não-vazio")

    unknown = set(fields) - EDITABLE
    if unknown:
        raise ValueError(f"campos não editáveis: {', '.join(sorted(unknown))}")

    cleaned: dict[str, Any] = {}
    for k, v in fields.items():
        if k == "email" and v is not None:
            email = str(v).strip().lower()
            if not _EMAIL_RE.match(email):
                raise ValueError(f"email inválido: {v!r}")
            cleaned[k] = email
        elif k == "relationship" and v is not None:
            if v not in RELATIONSHIPS:
                raise ValueError(f"relationship inválido: {v!r}")
            cleaned[k] = v
        else:
            cleaned[k] = v

    return person_id, cleaned


def patch_person(
    person_id: str,
    fields: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.patch(f"{base_url.rstrip('/')}/people/{person_id}", json=fields)
        if resp.status_code == 404:
            raise RuntimeError("person not found")
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
    parser = argparse.ArgumentParser(description="Atualiza campos de uma pessoa.")
    parser.add_argument("--payload", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        person_id, fields = validate_update(raw)
        person = patch_person(person_id, fields, args.base_url, timeout_s=args.timeout)
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps(
            {
                "ok": True,
                "data": {"id": person_id, "updated_fields": sorted(fields.keys()), "person": person},
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
