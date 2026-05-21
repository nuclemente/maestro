"""Agent runner — wrapper sobre `claude-agent-sdk` (Python).

Agents ficam em `.claude/agents/<nome>/AGENT.md` (mesmo formato com frontmatter).
Tools customizadas Python ficam em `.claude/agents/<nome>/scripts/` e devem chamar
a API REST local (httpx) — agents **nunca** tocam o `.db` diretamente.

Esta classe é apenas a fundação: a integração real com o SDK é finalizada quando
o primeiro agent real for criado (a ponte com Slack hoje é uma **skill** rodada
pelo `/loop` do Claude Code, não um agent — ver `.claude/skills/slack-listener`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.config import get_settings
from app.logging import get_logger

log = get_logger(__name__)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


class AgentNotFoundError(FileNotFoundError):
    pass


class AgentContractError(ValueError):
    pass


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    allowed_tools: list[str]
    model: str | None
    system_prompt: str
    directory: Path


class AgentRunner:
    """Carrega definições de agent e (futuramente) executa via `claude-agent-sdk`.

    A execução concreta é plugada quando o primeiro agent real for criado.
    Para a base, garantimos parsing e descoberta.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.base_dir = Path(settings.project_root) / settings.agents_dir

    def load(self, agent_name: str) -> AgentDefinition:
        agent_dir = self.base_dir / agent_name
        agent_md = agent_dir / "AGENT.md"
        if not agent_md.is_file():
            raise AgentNotFoundError(f"Agent '{agent_name}' não encontrado em {agent_dir}")

        raw = agent_md.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(raw)
        if not match:
            raise AgentContractError(f"AGENT.md de {agent_name} sem frontmatter YAML")

        fm = yaml.safe_load(match.group(1)) or {}
        body = match.group(2).strip()

        allowed = fm.get("allowed-tools") or []
        if isinstance(allowed, str):
            allowed = [t.strip() for t in allowed.split(",") if t.strip()]

        if "name" not in fm or "description" not in fm:
            raise AgentContractError(
                f"AGENT.md de {agent_name} precisa de 'name' e 'description' no frontmatter"
            )

        return AgentDefinition(
            name=fm["name"],
            description=fm["description"],
            allowed_tools=allowed,
            model=fm.get("model"),
            system_prompt=body,
            directory=agent_dir,
        )

    def list_agents(self) -> list[str]:
        if not self.base_dir.is_dir():
            return []
        return sorted(
            d.name
            for d in self.base_dir.iterdir()
            if d.is_dir() and (d / "AGENT.md").is_file()
        )

    async def run(self, agent_name: str, message: str, *, context: dict[str, Any] | None = None) -> Any:
        """Execução real via `claude-agent-sdk`. Implementação será plugada
        quando o primeiro agent real for criado. Mantemos o método aqui para
        que o contrato fique visível desde a base."""
        raise NotImplementedError(
            "AgentRunner.run será implementado junto do primeiro agent real"
        )
