"""Teste da função `echo` da skill ping."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR.parent))

from scripts.echo import echo, main  # noqa: E402


def test_echo_returns_message_and_timestamp():
    fixed = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    result = echo("olá", now=fixed)
    assert result["echo"] == "olá"
    assert result["timestamp"] == "2026-05-21T12:00:00+00:00"


def test_echo_rejects_non_string():
    with pytest.raises(TypeError):
        echo(123)  # type: ignore[arg-type]


def test_main_emits_valid_json(capsys):
    rc = main(["--message", "hello"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    payload = json.loads(out)
    assert payload["echo"] == "hello"
    assert re.match(r"\d{4}-\d{2}-\d{2}T", payload["timestamp"])


def test_cli_invocation_via_subprocess():
    """Valida que `python -m scripts.echo` funciona, conforme SKILL.md instrui."""
    cwd = SCRIPTS_DIR.parent
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.echo", "--message", "ping-test"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["echo"] == "ping-test"
