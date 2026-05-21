"""Skill runner — descobre e executa skills em `.claude/skills/<nome>/SKILL.md`.

Cada skill é um diretório com `SKILL.md` (frontmatter YAML + corpo) e, opcionalmente,
`scripts/*.py` (cálculos isolados). A mesma skill é executável diretamente via
`claude` CLI / Claude Code (slash command) **e** via este runner — sem duplicação.

Contrato:
    - Entrada: `params` (dict serializável em JSON) é injetado no prompt como
      `$ARGUMENTS`.
    - Saída: a skill deve retornar um bloco JSON delimitado por ```json ... ```.
      Esse bloco é parseado e devolvido como dict.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from app.config import get_settings
from app.logging import get_logger
from app.services.claude_cli import ClaudeCLIError, run_claude

log = get_logger(__name__)


class SkillNotFoundError(FileNotFoundError):
    pass


class SkillContractError(ValueError):
    """A skill rodou mas não devolveu o JSON esperado."""


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
_JSON_BLOCK_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


def _skill_dir(skill_name: str) -> Path:
    settings = get_settings()
    base = Path(settings.project_root) / settings.skills_dir
    path = base / skill_name
    if not path.is_dir() or not (path / "SKILL.md").is_file():
        raise SkillNotFoundError(f"Skill '{skill_name}' não encontrada em {path}")
    return path


def _parse_skill_md(skill_md: Path) -> tuple[dict, str]:
    raw = skill_md.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        raise SkillContractError(f"SKILL.md de {skill_md.parent.name} sem frontmatter YAML")
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    return frontmatter, body


def _extract_json_block(stdout: str) -> dict:
    match = _JSON_BLOCK_RE.search(stdout)
    if not match:
        raise SkillContractError("Resposta da skill não contém bloco ```json```")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise SkillContractError(f"JSON inválido na saída da skill: {exc}") from exc


def run_skill(
    skill_name: str,
    params: dict[str, Any] | None = None,
    *,
    allowed_tools: list[str] | None = None,
    timeout_s: int | None = None,
    max_turns: int | None = None,
) -> dict:
    """Executa a skill `skill_name` com `params` (injetados como $ARGUMENTS JSON).

    Retorna o bloco JSON parseado emitido pela skill.
    """
    skill_dir = _skill_dir(skill_name)
    frontmatter, body = _parse_skill_md(skill_dir / "SKILL.md")

    effective_tools = allowed_tools or frontmatter.get("allowed-tools") or []
    if isinstance(effective_tools, str):
        effective_tools = [t.strip() for t in effective_tools.split(",") if t.strip()]

    args_json = json.dumps(params or {}, ensure_ascii=False)
    prompt = body.replace("$ARGUMENTS", args_json)

    log.info(
        "skill.run",
        skill=skill_name,
        params_keys=list((params or {}).keys()),
        allowed_tools=effective_tools,
    )

    try:
        result = run_claude(
            prompt,
            allowed_tools=effective_tools,
            timeout_s=timeout_s,
            max_turns=max_turns,
            cwd=skill_dir,
        )
    except ClaudeCLIError as exc:
        log.error("skill.failed", skill=skill_name, error=str(exc))
        raise

    parsed = _extract_json_block(result.stdout)
    log.info("skill.ok", skill=skill_name, output_keys=list(parsed.keys()))
    return parsed
