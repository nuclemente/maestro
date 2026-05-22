"""Skill oneonone-close-collection — fecha CollectionRequest awaiting."""

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


def pick_awaiting_for_person(
    requests: list[dict[str, Any]], person_id: str
) -> dict[str, Any] | None:
    """Filtra CollectionRequest awaiting da pessoa. Pura."""
    candidates = [
        r
        for r in requests
        if r["person_id"] == person_id and r["status"] == "awaiting"
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda r: r["created_at"], reverse=True)[0]


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
        requests = http.get(
            f"{base}/oneonones/collection-requests", params={"status": "awaiting"}
        ).json()
        target = pick_awaiting_for_person(requests, person["id"])
        if target is None:
            raise RuntimeError("no awaiting collection")
        resp = http.post(f"{base}/oneonones/collection-requests/{target['id']}/close")
        resp.raise_for_status()
        return {
            "closed_request_id": target["id"],
            "formatted": f"🔕 Coleta de temas para {person['name']} fechada (sem reenviar).",
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fecha coleta awaiting sem reenviar DM.")
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
        data = _run(ref, args.base_url, timeout_s=args.timeout)
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
