"""Ferramenta do agente `slack-listener`: pinga o backend Maestro via REST.

Mantemos o IO isolado em script Python (regra do projeto: nada de cálculo /
chamada HTTP no prompt). O agente apenas executa:

    python -m scripts.backend_ping

e captura o JSON do stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 5.0


def ping(base_url: str = DEFAULT_BASE_URL, *, timeout_s: float = DEFAULT_TIMEOUT_S, client: httpx.Client | None = None) -> dict[str, Any]:
    """Chama `GET <base_url>/health` e devolve um envelope determinístico.

    Sempre retorna um dict com `ok: bool`. Em sucesso, `data` traz o JSON do
    backend; em falha, `error` traz a mensagem.

    `client` é injetável para facilitar testes (não monkey-patcham httpx).
    """

    url = base_url.rstrip("/") + "/health"
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        response = http.get(url)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"backend_unreachable: {exc.__class__.__name__}: {exc}"}
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"backend_invalid_json: {exc}"}
    finally:
        if owns_client:
            http.close()

    return {"ok": True, "data": payload}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ping no backend Maestro (/health).")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL base do backend.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S, help="Timeout em segundos.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = ping(args.base_url, timeout_s=args.timeout)
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
