"""Echo determinístico — função pura + CLI.

Função pura `echo()` é o ponto de teste; a CLI `python -m scripts.echo`
embrulha a função num formato consumível pela skill ping.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone


def echo(message: str, *, now: datetime | None = None) -> dict:
    """Devolve `{echo, timestamp}` — função pura, sem efeitos colaterais."""
    if not isinstance(message, str):
        raise TypeError("message precisa ser string")
    ts = (now or datetime.now(timezone.utc)).isoformat()
    return {"echo": message, "timestamp": ts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Echo determinístico para a skill ping.")
    parser.add_argument("--message", required=True, help="Mensagem a ecoar")
    args = parser.parse_args(argv)

    result = echo(args.message)
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
