"""Cliente HTTP do agente `oneonone` — fala com a API REST local do Maestro.

Subcomandos:
  - `session-detail --session-id <id>`        → GET /oneonones/sessions/{id}
  - `put-enrichment --topic-id <id> --payload '<json>'`  → PUT /oneonones/topics/{id}/enrichment
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0


def session_detail(
    session_id: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.get(f"{base_url.rstrip('/')}/oneonones/sessions/{session_id}")
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()
    finally:
        if owns:
            http.close()


def put_enrichment(
    topic_id: str,
    payload: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.put(
            f"{base_url.rstrip('/')}/oneonones/topics/{topic_id}/enrichment",
            json=payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="API client do agente oneonone.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sd = sub.add_parser("session-detail")
    sd.add_argument("--session-id", required=True)

    pe = sub.add_parser("put-enrichment")
    pe.add_argument("--topic-id", required=True)
    pe.add_argument("--payload", required=True)

    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "session-detail":
            data = session_detail(args.session_id, args.base_url, timeout_s=args.timeout)
        else:
            payload = json.loads(args.payload)
            data = put_enrichment(
                args.topic_id, payload, args.base_url, timeout_s=args.timeout
            )
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
