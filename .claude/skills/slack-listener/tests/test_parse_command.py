"""Testes do parser de comandos do canal.

    python -m pytest .claude/skills/slack-listener/tests -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from scripts.parse_command import (  # noqa: E402
    COMMANDS,
    classify,
    is_command,
    main,
    parse,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        (":ping", True),
        ("  :help", True),
        ("almoço bom hoje", False),
        ("", False),
        ("::double", True),
        (":", True),
    ],
)
def test_is_command(text: str, expected: bool) -> None:
    assert is_command(text) is expected


def test_parse_returns_none_for_non_command() -> None:
    assert parse("oi pessoal") is None


def test_parse_extracts_command_and_args() -> None:
    assert parse(":ping") == ("ping", [])
    assert parse(":help") == ("help", [])
    assert parse(':echo "hello world" foo') == ("echo", ["hello world", "foo"])


def test_parse_empty_command_after_colon() -> None:
    assert parse(":") == ("", [])
    assert parse(":   ") == ("", [])


def test_parse_handles_unmatched_quotes_gracefully() -> None:
    cmd, args = parse(':echo "broken')
    assert cmd == "echo"
    assert args == []


def test_classify_ignored_without_colon() -> None:
    result = classify({"ts": "111.0", "text": "olá"})
    assert result == {"kind": "ignored", "ts": "111.0", "reason": "no-colon-prefix"}


def test_classify_known_command() -> None:
    result = classify({"ts": "222.0", "text": ":ping"})
    assert result == {
        "kind": "command",
        "ts": "222.0",
        "command": ":ping",
        "args": [],
        "known": True,
    }


def test_classify_unknown_command() -> None:
    result = classify({"ts": "333.0", "text": ":foobar arg1"})
    assert result["kind"] == "command"
    assert result["command"] == ":foobar"
    assert result["args"] == ["arg1"]
    assert result["known"] is False


def test_classify_empty_colon_only() -> None:
    result = classify({"ts": "444.0", "text": ":"})
    assert result == {"kind": "ignored", "ts": "444.0", "reason": "empty-command"}


def test_registered_commands_match_skill_md() -> None:
    """COMMANDS é a fonte de verdade — SKILL.md deve documentar este conjunto."""
    assert COMMANDS == (
        "ping",
        "help",
        "people",
        "add-person",
        "show-person",
        "update-person",
        "discover-person",
        "confirm-person",
        "cancel-person",
        "oneonone",
        "collect-topics",
        "close-collection",
        "add-topic",
        "prepare",
        "new-session",
    )


def test_oneonone_commands_classified() -> None:
    assert classify({"ts": "1.0", "text": ":oneonone ana@x.com"})["known"] is True
    assert classify({"ts": "2.0", "text": ":collect-topics ana@x.com --force"})["args"] == [
        "ana@x.com",
        "--force",
    ]
    assert classify({"ts": "3.0", "text": ':add-topic ana "Carreira no Q3"'})["args"] == [
        "ana",
        "Carreira no Q3",
    ]


def test_main_writes_json_to_stdout(capsys) -> None:
    rc = main(["--text", ":ping", "--ts", "111.0"])
    payload = json.loads(capsys.readouterr().out.strip())

    assert rc == 0
    assert payload["kind"] == "command"
    assert payload["command"] == ":ping"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
