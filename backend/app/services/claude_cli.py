"""Wrapper subprocess do `claude` CLI.

Roda o CLI em modo não-interativo (`-p`), com lista de tools permitidas e timeout
obrigatório. Herda as credenciais de `~/.claude` automaticamente."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.logging import get_logger

log = get_logger(__name__)


class ClaudeCLIError(RuntimeError):
    """Falha estruturada da execução do `claude` CLI."""

    def __init__(self, message: str, *, returncode: int | None = None, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class ClaudeRunResult:
    stdout: str
    stderr: str
    returncode: int


def run_claude(
    prompt: str,
    *,
    allowed_tools: list[str] | None = None,
    timeout_s: int | None = None,
    max_turns: int | None = None,
    cwd: str | Path | None = None,
    extra_args: list[str] | None = None,
) -> ClaudeRunResult:
    """Executa um prompt via `claude -p` e retorna o resultado.

    Levanta `ClaudeCLIError` em qualquer falha estruturada (não-zero exit,
    timeout, executável ausente).
    """
    settings = get_settings()
    cli = settings.claude_cli_path
    timeout = timeout_s or settings.claude_default_timeout_s
    turns = max_turns or settings.claude_default_max_turns

    cmd: list[str] = [cli, "-p", prompt, "--max-turns", str(turns), "--output-format", "text"]

    if allowed_tools:
        cmd.extend(["--allowed-tools", ",".join(allowed_tools)])

    if extra_args:
        cmd.extend(extra_args)

    log.info(
        "claude_cli.run",
        cli=cli,
        timeout_s=timeout,
        max_turns=turns,
        allowed_tools=allowed_tools or [],
        cwd=str(cwd) if cwd else None,
    )

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ClaudeCLIError(f"Executável claude não encontrado em {cli}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCLIError(
            f"claude CLI excedeu timeout de {timeout}s", returncode=None, stderr=""
        ) from exc

    if proc.returncode != 0:
        log.error(
            "claude_cli.failed",
            returncode=proc.returncode,
            stderr=proc.stderr[:500],
        )
        raise ClaudeCLIError(
            f"claude CLI falhou (exit={proc.returncode})",
            returncode=proc.returncode,
            stderr=proc.stderr,
        )

    log.info("claude_cli.ok", stdout_len=len(proc.stdout))
    return ClaudeRunResult(stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
