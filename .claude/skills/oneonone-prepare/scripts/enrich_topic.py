"""Função pura `build_enrichment` + I/O de PUT — usado pela skill oneonone-prepare.

Cópia local do script do agente `oneonone` (mesmo contrato + os mesmos testes).
A cópia é deliberada: cada skill deve ter seus scripts em `scripts/` próprio,
sem dependência cross-skill (regra do projeto).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
_DEFAULT_TOP_N = int(os.environ.get("MAESTRO_ONEONONE_ENRICH_TOP_N", "3"))


def _norm_hit(source: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Normaliza um hit de MCP para o formato do backend. Pura."""
    title = (
        raw.get("title")
        or raw.get("name")
        or raw.get("summary")
        or (raw.get("text") or "")[:80]
        or "(sem título)"
    )
    url = raw.get("url") or raw.get("permalink") or raw.get("link")
    snippet = (
        raw.get("snippet")
        or raw.get("description")
        or raw.get("text")
        or ""
    )
    if isinstance(snippet, str) and len(snippet) > 300:
        snippet = snippet[:297] + "..."
    return {
        "source": source,
        "title": str(title).strip()[:200],
        "url": url,
        "snippet": snippet or None,
    }


def build_enrichment(
    topic: dict[str, Any],
    glean_hits: list[dict[str, Any]] | None = None,
    slack_hits: list[dict[str, Any]] | None = None,
    atlassian_hits: list[dict[str, Any]] | None = None,
    errors: list[str] | None = None,
    top_n: int = _DEFAULT_TOP_N,
    summary: str | None = None,
) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for source, raw_hits in (
        ("glean", glean_hits or []),
        ("slack", slack_hits or []),
        ("atlassian", atlassian_hits or []),
    ):
        for raw in (raw_hits or [])[:top_n]:
            if not isinstance(raw, dict):
                continue
            hits.append(_norm_hit(source, raw))
    return {
        "hits": hits,
        "summary": (summary or "").strip() or None,
        "errors": sorted(set(errors or [])),
    }


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
    p = argparse.ArgumentParser(description="Build + PUT enrichment de um topic.")
    p.add_argument("--payload", required=True)
    p.add_argument("--topic-id", required=True)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        topic = raw.get("topic") or {"id": args.topic_id, "title": "?"}
        enrichment = build_enrichment(
            topic,
            glean_hits=raw.get("glean_hits"),
            slack_hits=raw.get("slack_hits"),
            atlassian_hits=raw.get("atlassian_hits"),
            errors=raw.get("errors"),
            top_n=int(raw.get("top_n") or _DEFAULT_TOP_N),
            summary=raw.get("summary"),
        )
        data = put_enrichment(
            args.topic_id, enrichment, args.base_url, timeout_s=args.timeout
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
