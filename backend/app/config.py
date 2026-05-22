"""Configuração de runtime — lê `.env` + `config.yaml` via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_YAML = PROJECT_ROOT / "config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"


def _load_yaml() -> dict:
    if not CONFIG_YAML.exists():
        raise FileNotFoundError(
            f"config.yaml não encontrado em {CONFIG_YAML}. "
            "Copie config.example.yaml ou rode bin/setup.sh."
        )
    with CONFIG_YAML.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


class Settings(BaseSettings):
    """Settings carregadas de `.env` (segredos) + `config.yaml` (runtime)."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        env_prefix="MAESTRO_",
        extra="ignore",
    )

    # Runtime
    env: str = Field(..., description="dev | prod")
    log_level: str = Field(..., description="DEBUG | INFO | WARNING | ERROR")
    log_format: str = Field(..., description="text | json")

    # Server
    backend_host: str
    backend_port: int
    frontend_origin: str

    # Storage
    db_path: str
    db_url: str | None = None

    # Claude CLI
    claude_cli_path: str
    claude_default_timeout_s: int
    claude_default_max_turns: int

    # Project
    project_root: str = str(PROJECT_ROOT)
    skills_dir: str
    agents_dir: str

    # Feature: ecossistema de 1:1
    em_email: str = ""
    oneonone_enrich_top_n: int = 3
    oneonone_transcript_chunk_tokens: int = 8000

    def resolved_db_url(self) -> str:
        if self.db_url:
            return self.db_url
        db_file = (PROJECT_ROOT / self.db_path).resolve()
        return f"sqlite:///{db_file}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    yaml_cfg = _load_yaml()
    return Settings(**yaml_cfg)
