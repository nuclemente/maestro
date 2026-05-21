---
name: ping
description: Smoke skill — devolve o input com timestamp para validar a pipeline (CLI + skill_runner).
allowed-tools:
  - Bash(python:*)
---

# ping

Skill de fumaça (smoke) usada para validar a pipeline de execução de skills do Maestro
em duas frentes:

1. Via `claude` CLI / Claude Code (slash command `/ping`).
2. Via backend (`app.services.skill_runner.run_skill('ping', ...)`).

## Entrada

`$ARGUMENTS` é um JSON com a forma:

```json
{ "message": "<string>" }
```

## Comportamento

1. Leia `$ARGUMENTS`.
2. Execute o cálculo via script Python isolado:

   ```bash
   python -m scripts.echo --message "<message vinda de $ARGUMENTS>"
   ```

   (o script vive em `.claude/skills/ping/scripts/echo.py` — sempre invoque pelo path relativo desta skill).

3. Capture a stdout do script (é um JSON: `{ "echo": "<message>", "timestamp": "<iso8601>" }`).

4. Responda **somente** com um bloco JSON delimitado:

```json
{
  "ok": true,
  "data": {
    "echo": "<echoed message>",
    "timestamp": "<iso8601>"
  }
}
```

## Exemplo

Entrada:
```json
{ "message": "olá" }
```

Saída esperada (formato — timestamp varia):
```json
{ "ok": true, "data": { "echo": "olá", "timestamp": "2026-05-21T12:34:56Z" } }
```
