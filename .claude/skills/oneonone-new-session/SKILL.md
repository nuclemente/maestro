---
name: oneonone-new-session
description: Cria manualmente uma session de 1:1 para uma pessoa (com data opcional).
allowed-tools:
  - Bash(python:*)
---

# oneonone-new-session

Cria uma `OneOnOneSession` direta no backend. Útil para o EM agendar uma 1:1
adhoc sem depender do Google Calendar (a `oneonone-sync-calendar` continua não
destrutiva sobre estas).

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>", "scheduled_at": "2026-06-12T10:00:00Z", "status": "planned" }
```

- `ref` obrigatório.
- `scheduled_at` opcional (ISO 8601 ou `YYYY-MM-DD HH:MM`). Ausente → session **adhoc**.
- `status` opcional (default `planned`).

## Comportamento

```bash
python -m scripts.new_session --payload '$ARGUMENTS'
```

## Saída

```json
{
  "ok": true,
  "data": {
    "session": { "id": "...", "scheduled_at": "...", "status": "planned" },
    "formatted": "🗓 Nova 1:1 com Ana criada (2026-06-12 10:00)."
  }
}
```
