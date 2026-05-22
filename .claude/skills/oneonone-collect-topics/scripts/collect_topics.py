"""Skill oneonone-collect-topics — resolve pessoa, renderiza DM, registra CollectionRequest.

Dividida em dois subcomandos para o caller (agent/skill) intercalar a chamada MCP de envio
de DM (que **só** o agent/skill no contexto Claude consegue chamar):

- `--resolve` : devolve `{ person, session, dm_channel_id, dm_text }` para o caller mandar a DM.
- `--register` : recebe `slack_channel_id` + `sent_message_ts` do caller e registra a
  `CollectionRequest` via POST no backend.
"""

from __future__ import annotations

import argparse
import json
import re
import string
import sys
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "dm_collect_topics.md"


def resolve_person_ref(ref: str) -> tuple[str, str]:
    cleaned = (ref or "").strip()
    if not cleaned:
        raise ValueError("ref vazia")
    if _UUID_RE.match(cleaned):
        return ("id", cleaned)
    if "@" in cleaned:
        return ("email", cleaned.lower())
    raise ValueError(f"ref inválida: {ref!r}")


def build_dm_context(
    person: dict[str, Any], session: dict[str, Any] | None
) -> dict[str, str]:
    """Monta o dict de placeholders. Pura."""
    sched = (session or {}).get("scheduled_at")
    if not sched:
        next_human = "ainda sem data"
        date_short = ""
    else:
        date_short = sched[:10]
        next_human = f"em {date_short}"
    return {
        "person_name": person.get("name", ""),
        "session_date": date_short,
        "next_session_human": next_human,
    }


class _SafeTemplate(string.Template):
    # Aceita {{name}} além do default ${name}.
    pattern = r"""
    \{\{(?:
      (?P<escaped>\{\{) |
      (?P<named>[_a-z][_a-z0-9]*)\}\} |
      (?P<braced>[_a-z][_a-z0-9]*)\}\} |
      (?P<invalid>)
    )
    """


def render_dm_template(template_text: str, ctx: dict[str, str]) -> str:
    """Renderiza o template substituindo `{{key}}` com fallback `''`. Pura."""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return ctx.get(key, "")

    return re.sub(r"\{\{\s*([_a-z][_a-z0-9]*)\s*\}\}", _replace, template_text, flags=re.IGNORECASE)


def _pick_next_planned(sessions: list[dict[str, Any]]) -> dict[str, Any] | None:
    planned = [s for s in sessions if s["status"] == "planned"]
    if not planned:
        return None
    return sorted(
        planned, key=lambda s: (s.get("scheduled_at") is None, s.get("scheduled_at") or "")
    )[0]


def _fetch_person(http: httpx.Client, base: str, ref: str) -> dict[str, Any]:
    kind, value = resolve_person_ref(ref)
    url = f"{base}/people/{value}" if kind == "id" else f"{base}/people/by-email/{value}"
    resp = http.get(url)
    if resp.status_code == 404:
        raise RuntimeError(f"pessoa não encontrada: {ref}")
    resp.raise_for_status()
    return resp.json()


def _ensure_planned_session(
    http: httpx.Client, base: str, person_id: str
) -> dict[str, Any]:
    sessions = http.get(
        f"{base}/people/{person_id}/oneonone-track/sessions",
        params={"status": "planned"},
    ).json()
    chosen = _pick_next_planned(sessions)
    if chosen is not None:
        return chosen
    resp = http.post(
        f"{base}/people/{person_id}/oneonone-track/sessions", json={}
    )
    resp.raise_for_status()
    return resp.json()


def resolve(
    ref: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
    template_path: Path = _TEMPLATE_PATH,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        person = _fetch_person(http, base, ref)
        if not person.get("slack_id"):
            raise RuntimeError(f"pessoa {person['name']} sem slack_id — não dá pra mandar DM")
        session = _ensure_planned_session(http, base, person["id"])
        ctx = build_dm_context(person, session)
        text = render_dm_template(template_path.read_text(encoding="utf-8"), ctx)
        return {
            "person": person,
            "session": session,
            "dm_channel_id": person["slack_id"],
            "dm_text": text,
        }
    finally:
        if owns:
            http.close()


def register(
    ref: str,
    slack_channel_id: str,
    sent_message_ts: str,
    *,
    force: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        person = _fetch_person(http, base, ref)
        session = _ensure_planned_session(http, base, person["id"])
        resp = http.post(
            f"{base}/oneonones/sessions/{session['id']}/collection-request",
            json={
                "person_id": person["id"],
                "slack_channel_id": slack_channel_id,
                "sent_message_ts": sent_message_ts,
                "force": force,
            },
        )
        if resp.status_code == 409:
            raise RuntimeError(
                "collection already awaiting (use force=true to reopen)"
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        req = resp.json()
        return {
            "request_id": req["id"],
            "session_id": req["session_id"],
            "channel_id": req["slack_channel_id"],
            "sent_message_ts": req["sent_message_ts"],
            "formatted": f"📨 DM enviada para {person['name']} — aguardando temas.",
        }
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Coleta de temas via DM no Slack.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--resolve", action="store_true", help="Resolve pessoa + renderiza DM.")
    g.add_argument("--register", action="store_true", help="Registra CollectionRequest.")
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
            raise ValueError("payload precisa de 'ref'")
        if args.resolve:
            data = resolve(ref, args.base_url, timeout_s=args.timeout)
        else:
            slack_channel_id = raw.get("slack_channel_id")
            sent_message_ts = raw.get("sent_message_ts")
            if not slack_channel_id or not sent_message_ts:
                raise ValueError(
                    "register requer 'slack_channel_id' e 'sent_message_ts' no payload"
                )
            data = register(
                ref,
                slack_channel_id,
                sent_message_ts,
                force=bool(raw.get("force", False)),
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
