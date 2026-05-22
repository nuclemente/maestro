"""Cliente HTTP do agente `people` — fala com a API REST local do Maestro.

Subcomandos:
  - `draft-create --payload '<json>'`       → POST /people/drafts (idempotente)
  - `draft-list`                            → GET  /people/drafts
  - `person-list [--relationship X]`        → GET  /people
  - `draft-confirm --draft-id <id>`         → POST /people/drafts/{id}/confirm
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0


def create_draft(
    payload: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.post(f"{base_url.rstrip('/')}/people/drafts", json=payload)
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


def list_drafts(
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.get(f"{base_url.rstrip('/')}/people/drafts")
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            http.close()


def list_people(
    base_url: str = DEFAULT_BASE_URL,
    *,
    relationship: str | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        params = {"relationship": relationship} if relationship else {}
        resp = http.get(f"{base_url.rstrip('/')}/people", params=params)
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            http.close()


def confirm_draft(
    draft_id: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.post(f"{base_url.rstrip('/')}/people/drafts/{draft_id}/confirm")
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


def _emit(payload: dict[str, Any], *, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"ok": ok, "data": payload}, ensure_ascii=False) + "\n")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HTTP client do agente `people`.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("draft-create")
    p_create.add_argument("--payload", required=True)

    sub.add_parser("draft-list")

    p_pl = sub.add_parser("person-list")
    p_pl.add_argument("--relationship", default=None)

    p_conf = sub.add_parser("draft-confirm")
    p_conf.add_argument("--draft-id", required=True)

    args = parser.parse_args(argv)

    try:
        if args.cmd == "draft-create":
            payload = json.loads(args.payload)
            return _emit(create_draft(payload, args.base_url, timeout_s=args.timeout))
        if args.cmd == "draft-list":
            drafts = list_drafts(args.base_url, timeout_s=args.timeout)
            return _emit({"drafts": drafts, "count": len(drafts)})
        if args.cmd == "person-list":
            people = list_people(args.base_url, relationship=args.relationship, timeout_s=args.timeout)
            return _emit({"people": people, "count": len(people)})
        if args.cmd == "draft-confirm":
            return _emit(confirm_draft(args.draft_id, args.base_url, timeout_s=args.timeout))
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
