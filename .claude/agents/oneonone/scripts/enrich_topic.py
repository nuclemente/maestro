"""Função pura `build_enrichment` para o agente `oneonone`.

Consolida hits de Glean/Slack/Atlassian num payload
`{hits: [...], summary, errors: [...]}` aceito pelo backend.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

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
    """Monta o payload de enrichment. Pura.

    Cada fonte é limitada a `top_n`. `errors` é a lista de fontes que falharam.
    `summary` é opcional (a sintese do Glean chat, se disponível).
    """
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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Constrói payload de enrichment de topic.")
    p.add_argument("--payload", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        topic = raw.get("topic") or {}
        if not topic.get("id") or not topic.get("title"):
            raise ValueError("payload precisa de topic.{id,title}")
        data = build_enrichment(
            topic,
            glean_hits=raw.get("glean_hits"),
            slack_hits=raw.get("slack_hits"),
            atlassian_hits=raw.get("atlassian_hits"),
            errors=raw.get("errors"),
            top_n=int(raw.get("top_n") or _DEFAULT_TOP_N),
            summary=raw.get("summary"),
        )
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False)
            + "\n"
        )
        return 1
    sys.stdout.write(json.dumps({"ok": True, "data": data}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
