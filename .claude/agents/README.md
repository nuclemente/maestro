# Convenção de Agents (Maestro)

Cada agent é **um diretório** dentro de `.claude/agents/<nome-kebab>/`. Agents são executados via `claude-agent-sdk` (Python) pelo `app.services.agent_runner.AgentRunner`. Eles são acionados a partir do canal privado do Slack (`/loop` do Claude Code) e **nunca** tocam o `.db` direto — falam com o backend Maestro via HTTP (mesma API REST que o frontend usa).

## Layout

```
.claude/agents/<nome>/
├─ AGENT.md            # frontmatter YAML + system prompt
├─ scripts/            # tools Python específicas do agent (httpx → API local)
│  └─ <tool>.py
└─ tests/
   └─ test_<tool>.py
```

## AGENT.md — frontmatter obrigatório

```yaml
---
name: <nome-kebab>             # igual ao diretório
description: <frase curta>     # o que o agent orquestra
allowed-tools:                 # tools (Slack, Atlassian, Glean, etc.) + tools custom
  - mcp__plugin_slack_slack__slack_send_message
  - mcp__atlassian__searchJiraIssuesUsingJql
model: claude-sonnet-4-6       # opcional
---
```

## Regras

1. **Agent é orquestrador.** Multi-step, recebe contexto do canal, decide quais tools usar, responde no Slack.
2. **Sem acesso direto a `.db`.** Toda mutação/consulta de dado passa pela API REST do backend (httpx).
3. **Tools customizadas ficam em `scripts/`** do próprio agent. Cada tool tem teste pytest.
4. **Cálculos** seguem a mesma regra das skills: nunca no prompt — sempre em `scripts/*.py` com função pura.
5. **Validar execução manual** antes de marcar o agent como pronto.
