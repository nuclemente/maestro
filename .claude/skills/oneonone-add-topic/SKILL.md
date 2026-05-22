---
name: oneonone-add-topic
description: Adiciona um tema manual à próxima session de 1:1 de uma pessoa (cria session adhoc se não houver planned).
allowed-tools:
  - Bash(python:*)
---

# oneonone-add-topic

Adiciona um `OneOnOneTopic` (source=manual) à próxima session `planned` da pessoa.
Se a pessoa não tiver session planned, cria uma session **adhoc** (sem `scheduled_at`).

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>", "title": "Carreira no Q3", "body": null }
```

`title` é obrigatório. `body` é opcional.

## Comportamento

```bash
python -m scripts.add_topic --payload '$ARGUMENTS'
```

## Saída

```json
{
  "ok": true,
  "data": {
    "topic": { "id": "...", "title": "...", "session_id": "..." },
    "session": { "id": "...", "scheduled_at": "..." },
    "created_session": false,
    "formatted": "✅ Tema 'Carreira no Q3' adicionado à 1:1 de Ana"
  }
}
```
