"""Skill oneonone-ingest-dms — parsing puro + POST de ingestão.

Dois subcomandos:

- `--parse` : recebe `{messages, person_slack_id, since_ts, last_polled_at?}` e devolve
  `{topics: [...], close: bool}`. **Pura** (sem I/O).
- `--post`  : recebe `{request_id, topics, close}` e POSTa em
  `/oneonones/collection-requests/{id}/ingest`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0

_NEGATIVE_HINTS = {"ok", "ok!", "nada", "não tenho", "nao tenho", "sem temas"}
_CLOSE_HINTS = {"pronto", "acabou", "done", "é isso", "eh isso", "finalizei"}
_STALE_HOURS = 24


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def parse_topics_from_messages(
    messages: list[dict[str, Any]],
    person_slack_id: str,
    since_ts: str,
) -> list[str]:
    """Extrai uma lista de temas das DMs da pessoa após `since_ts`. Pura.

    - Considera só mensagens cujo `user` == `person_slack_id` e `ts > since_ts`.
    - Quebra cada texto por linhas; remove bullets `-`, `*`, `•`, números (`1.`).
    - Descarta linhas vazias, frases negativas e hints de fechamento (sozinhas).
    """
    topics: list[str] = []
    for msg in messages:
        if msg.get("user") != person_slack_id:
            continue
        if str(msg.get("ts", "")) <= str(since_ts):
            continue
        for line in (msg.get("text") or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Remove bullets/numeração.
            for prefix in ("- ", "* ", "• ", "· "):
                if stripped.startswith(prefix):
                    stripped = stripped[len(prefix):].strip()
                    break
            else:
                # Numeração tipo "1.", "2)".
                if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
                    stripped = stripped[2:].strip()
            low = _normalize(stripped)
            if not stripped or low in _NEGATIVE_HINTS or low in _CLOSE_HINTS:
                continue
            topics.append(stripped)
    return topics


def should_close(
    messages: list[dict[str, Any]],
    person_slack_id: str,
    since_ts: str,
    last_polled_at: str | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Decide se a coleta deve ser fechada. Pura."""
    now = now or datetime.now(timezone.utc)
    for msg in messages:
        if msg.get("user") != person_slack_id:
            continue
        if str(msg.get("ts", "")) <= str(since_ts):
            continue
        low = _normalize(msg.get("text", ""))
        if any(hint in low for hint in _CLOSE_HINTS):
            return True
    if last_polled_at:
        try:
            dt = datetime.fromisoformat(last_polled_at.replace("Z", "+00:00"))
        except ValueError:
            dt = None
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            hours = (now - dt).total_seconds() / 3600
            if hours > _STALE_HOURS:
                return True
    return False


def post_ingest(
    request_id: str,
    topics: list[str],
    close: bool,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.post(
            f"{base_url.rstrip('/')}/oneonones/collection-requests/{request_id}/ingest",
            json={"topics": topics, "close": close},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingestão de DMs de coleta de temas.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--parse", action="store_true")
    g.add_argument("--post", action="store_true")
    p.add_argument("--payload", required=True)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        if args.parse:
            messages = raw.get("messages") or []
            person_slack_id = raw.get("person_slack_id") or ""
            since_ts = str(raw.get("since_ts") or "")
            last_polled_at = raw.get("last_polled_at")
            topics = parse_topics_from_messages(messages, person_slack_id, since_ts)
            close = should_close(messages, person_slack_id, since_ts, last_polled_at)
            data = {"topics": topics, "close": close}
        else:
            request_id = raw.get("request_id")
            topics = raw.get("topics") or []
            close = bool(raw.get("close", False))
            if not request_id:
                raise ValueError("post requer 'request_id'")
            data = post_ingest(
                request_id,
                topics,
                close,
                base_url=args.base_url,
                timeout_s=args.timeout,
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
