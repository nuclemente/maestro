# Convenção de Skills (Maestro)

Cada skill é **um diretório** dentro de `.claude/skills/<nome-kebab>/`. A mesma skill é descobrível e executável diretamente pelo `claude` CLI / Claude Code (slash command) **e** pelo backend via `app.services.skill_runner.run_skill(...)`. Não há duplicação.

## Layout

```
.claude/skills/<nome>/
├─ SKILL.md            # frontmatter YAML + corpo
├─ scripts/            # cálculos Python ISOLADOS por skill
│  └─ <calc>.py        # função pura + CLI (`python -m`) + sem efeitos colaterais
└─ tests/
   └─ test_<calc>.py   # pytest cobrindo o(s) script(s)
```

## SKILL.md — frontmatter obrigatório

```yaml
---
name: <nome-kebab>             # igual ao nome do diretório
description: <frase curta>     # o que a skill faz, em 1 linha
allowed-tools:                 # lista de tools permitidas (Slack, Atlassian, Bash, etc.)
  - mcp__plugin_slack_slack__slack_send_message
  - Bash(python:*)
model: claude-sonnet-4-6       # opcional — default segue o CLI
---
```

## Contrato de I/O

- **Entrada:** `params` (dict) é injetado no corpo como `$ARGUMENTS` (JSON).
- **Saída:** a skill **deve** terminar com um bloco delimitado:

  ```json
  { "ok": true, "data": { ... } }
  ```

  O `skill_runner` extrai esse bloco e devolve como `dict`. Se ausente ou JSON inválido, `SkillContractError` é levantado.

## Regras

1. **Não fazer cálculo no prompt.** Qualquer aritmética/regra de negócio fica em `scripts/*.py` (função pura + CLI + teste).
2. **Cada script tem teste pytest.** Sem teste, a skill não é considerada pronta.
3. **Documentar exemplos** de input/output no corpo do `SKILL.md`.
4. **Validar execução manual** via `claude` CLI antes de marcar a skill como pronta.
5. **Sem credenciais no SKILL.md** — segredos vêm do `.env` / `~/.claude`.

## Exemplo de execução

```bash
# Via Claude Code (slash command)
/ping {"message": "hello"}

# Via backend
python -c "from app.services.skill_runner import run_skill; print(run_skill('ping', {'message': 'hello'}))"
```
