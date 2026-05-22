---
name: oneonone-show
description: Mostra a Track de 1:1 de uma pessoa com a próxima session, topics pendentes e último resumo.
allowed-tools:
  - Bash(python:*)
---

# oneonone-show

Resolve a pessoa por `id` ou `email` e devolve um briefing curto da Track de 1:1
(próxima session, contadores de topics, último resumo conhecido).

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>" }
```

## Comportamento

```bash
python -m scripts.show_oneonone --payload '$ARGUMENTS'
```

## Saída

```json
{
  "ok": true,
  "data": {
    "person": { "id": "...", "name": "...", "email": "..." },
    "track":  { "id": "...", "notes": "..." },
    "next_session":  { "id": "...", "scheduled_at": "..." },
    "topics_pending": 2,
    "last_done": { "id": "...", "scheduled_at": "...", "summary": "..." },
    "formatted": "🎯 1:1 com Ana — próxima 12/Jun • 2 topics pending"
  }
}
```
