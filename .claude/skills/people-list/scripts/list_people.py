"""Skill people-list — função pura `format_people` + CLI httpx para /people."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
RELATIONSHIPS = {"direct_report", "peer", "manager", "skip_level", "stakeholder", "other"}


def format_people(items: list[dict[str, Any]]) -> str:
    """Render legível da lista — pura, sem efeitos colaterais."""
    if not items:
        return "(nenhuma pessoa cadastrada)"
    lines: list[str] = []
    for p in items:
        name = p.get("name", "?")
        rel = p.get("relationship", "?")
        role = p.get("role")
        suffix = f" — {role}" if role else ""
        lines.append(f"• {name} ({rel}){suffix}")
    return "\n".join(lines)


def fetch_people(
    base_url: str = DEFAULT_BASE_URL,
    *,
    relationship: str | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {}
    if relationship:
        if relationship not in RELATIONSHIPS:
            raise ValueError(f"relationship inválido: {relationship!r}")
        params["relationship"] = relationship

    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.get(base_url.rstrip("/") + "/people", params=params)
        resp.raise_for_status()
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lista pessoas cadastradas no Maestro.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--relationship", default=None)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        items = fetch_people(args.base_url, relationship=args.relationship, timeout_s=args.timeout)
    except (httpx.HTTPError, ValueError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    payload = {
        "ok": True,
        "data": {"count": len(items), "people": items, "formatted": format_people(items)},
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
