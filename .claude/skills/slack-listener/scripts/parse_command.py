"""Parser determinístico das mensagens do canal.

Regra do projeto: nada de regex/lógica de negócio no prompt da skill — tudo
em script Python puro com teste. Este módulo expõe:

- `is_command(text)` → bool
- `parse(text)`      → ("ping", ["arg1", ...]) | None
- `classify(message)` → dict com `{ "kind": "command"|"ignored", ... }`

Comandos registrados ficam em `COMMANDS` (pode crescer por feature).
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Any

#: Comandos suportados. Features adicionam novos comandos aqui.
COMMANDS: tuple[str, ...] = (
    "ping",
    "help",
    # Feature: cadastro de pessoas de interesse.
    "people",
    "add-person",
    "show-person",
    "update-person",
    "discover-person",
    "confirm-person",
    "cancel-person",
)


def is_command(text: str) -> bool:
    """True se a mensagem é um comando do Maestro (prefixo `:` após strip)."""
    return text.lstrip().startswith(":")


def parse(text: str) -> tuple[str, list[str]] | None:
    """Quebra `:cmd arg1 arg2` em `("cmd", ["arg1", "arg2"])`.

    Retorna `None` se o texto não for comando. `shlex` lida com aspas.
    """
    if not is_command(text):
        return None

    stripped = text.lstrip()[1:].strip()
    if not stripped:
        return ("", [])

    try:
        tokens = shlex.split(stripped)
    except ValueError:
        # Aspas mal fechadas → trata como comando malformado.
        return (stripped.split()[0], [])

    if not tokens:
        return ("", [])
    return (tokens[0], tokens[1:])


def classify(message: dict[str, Any]) -> dict[str, Any]:
    """Classifica uma mensagem do Slack como comando ou ignorada.

    Espera ao menos `{"ts": "...", "text": "..."}` (forma simplificada).
    """
    ts = message.get("ts", "")
    text = message.get("text", "") or ""

    parsed = parse(text)
    if parsed is None:
        return {"kind": "ignored", "ts": ts, "reason": "no-colon-prefix"}

    cmd, args = parsed
    if not cmd:
        return {"kind": "ignored", "ts": ts, "reason": "empty-command"}

    return {
        "kind": "command",
        "ts": ts,
        "command": f":{cmd}",
        "args": args,
        "known": cmd in COMMANDS,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classifica uma mensagem do Slack.")
    parser.add_argument("--text", required=True, help="Conteúdo textual da mensagem.")
    parser.add_argument("--ts", default="", help="Timestamp da mensagem (opcional).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = classify({"ts": args.ts, "text": args.text})
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
