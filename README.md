# Maestro

Assistente **local-first** para Engineering Management. Duas superfícies: uma Web (React) e um canal privado do Slack acionado pelo `/loop` do Claude Code.

> Esta é a **base** do projeto. Features (cadastro de pessoas, agenda enriquecida, 1:1s, performance, radar de temas, plano da semana, to-do, etc.) são adicionadas incrementalmente.

## Setup em 3 comandos

```bash
bin/setup.sh         # cria venv, instala backend + frontend, roda migrations
bin/start.sh         # sobe backend (:8001) + frontend (:5173)
curl http://localhost:8001/health   # smoke check
```

Depois abra http://localhost:5173 — você verá a Home minimalista com **header + drawer** + botão "Testar backend" que chama `/health` via proxy.

## Stack

- **Backend:** FastAPI · SQLAlchemy 2 · Alembic · SQLite · structlog · pydantic-settings · claude-agent-sdk.
- **Frontend:** React 18 · Vite 5 · Tailwind 3 · react-router-dom · react-hot-toast · lucide-react · vitest.
- **IA:** Claude CLI (subprocess) para skills · Claude Agent SDK para agents · MCPs (Slack, Atlassian, Google, Glean).

## Estrutura

Veja [PLAN.md](PLAN.md) e [ARCHITECTURE.md](ARCHITECTURE.md) para o detalhamento. Resumo:

```
bin/             setup.sh, start.sh
backend/         FastAPI app + Alembic + tests
frontend/        Vite + React + Tailwind
.claude/
  skills/        SKILL.md + scripts/ + tests/ (uma por feature)
  agents/        AGENT.md + scripts/ + tests/
  commands/      slash-commands utilitários
  settings.json  allowlist mínima
data/            SQLite (gerado em runtime)
config.yaml      config de runtime
.env             segredos (gitignored)
```

## Documentos

- [`CLAUDE.md`](CLAUDE.md) — instruções específicas do projeto para o Claude Code.
- [`MEMORY.md`](MEMORY.md) — perfil do operador + decisões persistentes.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — fluxos Web/Slack, padrão skill vs agent, tokens NuDS.
- [`.claude/skills/README.md`](.claude/skills/README.md) e [`.claude/agents/README.md`](.claude/agents/README.md) — convenções de IA.

## Smoke da pipeline

A skill `ping` valida que tudo funciona ponta-a-ponta:

```bash
# Teste do script Python
pytest .claude/skills/ping/tests/

# Via backend
python -c "from app.services.skill_runner import run_skill; print(run_skill('ping', {'message': 'hello'}))"

# Via Claude Code (interativo)
claude
> /ping {"message": "hello"}
```

## Troubleshooting

- **`config.yaml não encontrado`** — copie do repositório (`cp config.yaml.example config.yaml`) ou rode `bin/setup.sh`.
- **Porta 8001/5173 ocupada** — ajuste `MAESTRO_BACKEND_PORT` / `MAESTRO_FRONTEND_PORT` no `.env`.
- **Nu Sans não aparece** — coloque os `.woff2` em `frontend/public/fonts/`. Sem eles, fallback `system-ui` é usado.
- **MCPs não respondem** — herança de `~/.claude` é necessária. Verifique se as integrações estão autenticadas com `claude /login`.
