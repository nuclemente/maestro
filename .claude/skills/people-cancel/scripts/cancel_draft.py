"""Skill people-cancel — DELETE /people/drafts/{id}."""

from __future__ import annotations

import argparse
import json
import sys

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0


def cancel_draft(
    draft_id: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> bool:
    if not draft_id or not isinstance(draft_id, str):
        raise ValueError("draft_id é obrigatório (string)")

    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.delete(f"{base_url.rstrip('/')}/people/drafts/{draft_id}")
        if resp.status_code == 404:
            raise RuntimeError("draft not found")
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return True
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cancela um draft de pessoa.")
    parser.add_argument("--draft-id", required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        cancel_draft(args.draft_id, args.base_url, timeout_s=args.timeout)
    except (ValueError, RuntimeError, httpx.HTTPError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps({"ok": True, "data": {"draft_id": args.draft_id, "cancelled": True}}, ensure_ascii=False) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
