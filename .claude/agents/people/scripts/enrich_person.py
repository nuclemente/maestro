"""Consolida sinais de Glean/Slack/Atlassian numa proposta de draft.

Função pura `build_proposal` — única superfície testada. CLI consome JSON
com os hits coletados pelo agente e imprime o payload consolidado.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _first_str(*values: Any) -> str | None:
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def build_proposal(
    *,
    name: str,
    glean_hits: list[dict[str, Any]] | None = None,
    slack_hits: list[dict[str, Any]] | None = None,
    jira_hits: list[dict[str, Any]] | None = None,
    relationship: str = "other",
    source: str = "agent:people",
) -> dict[str, Any]:
    """Constrói o payload `PersonDraftCreate` a partir dos sinais coletados.

    Cada hit é um dict com campos opcionais (`email`, `slack_id`, `role`,
    `jira_account_id`, `github_handle`, `squad`). Escolhe o primeiro valor
    não-vazio para cada campo, na ordem fornecida.

    Slack tem prioridade sobre Glean para `email` (mais autoritativo).
    """
    glean = glean_hits or []
    slack = slack_hits or []
    jira = jira_hits or []

    email = _first_str(
        *(h.get("email") for h in slack),
        *(h.get("email") for h in glean),
    )
    slack_id = _first_str(*(h.get("slack_id") or h.get("id") for h in slack))
    role = _first_str(*(h.get("role") or h.get("title") for h in glean + slack))
    jira_account_id = _first_str(*(h.get("jira_account_id") or h.get("accountId") for h in jira))
    github_handle = _first_str(*(h.get("github_handle") for h in glean))
    squad = _first_str(*(h.get("squad") or h.get("team") for h in glean))

    notes_parts: list[str] = []
    if squad:
        notes_parts.append(f"squad: {squad}")

    payload: dict[str, Any] = {
        "name": name.strip(),
        "email": email or "",
        "relationship": relationship,
        "source": source,
    }
    if role:
        payload["role"] = role
    if slack_id:
        payload["slack_id"] = slack_id
    if jira_account_id:
        payload["jira_account_id"] = jira_account_id
    if github_handle:
        payload["github_handle"] = github_handle
    if notes_parts:
        payload["notes"] = " | ".join(notes_parts)

    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consolida sinais em proposta de draft.")
    parser.add_argument(
        "--payload",
        required=True,
        help='JSON com {"name", "relationship"?, "glean_hits"?, "slack_hits"?, "jira_hits"?}',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        name = raw.get("name") or ""
        if not name:
            raise ValueError("campo 'name' é obrigatório")
        proposal = build_proposal(
            name=name,
            glean_hits=raw.get("glean_hits"),
            slack_hits=raw.get("slack_hits"),
            jira_hits=raw.get("jira_hits"),
            relationship=raw.get("relationship") or "other",
            source=raw.get("source") or "agent:people",
        )
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False) + "\n"
        )
        return 1

    sys.stdout.write(json.dumps({"ok": True, "data": proposal}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
