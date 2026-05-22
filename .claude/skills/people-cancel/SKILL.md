---
name: people-cancel
description: Descarta um draft de pessoa pendente (DELETE /people/drafts/{id}).
allowed-tools:
  - Bash(python:*)
---

# people-cancel

Cancela um draft proposto pelo agente `people`.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "draft_id": "<uuid>" }
```

## Comportamento

```bash
python -m scripts.cancel_draft --draft-id <uuid>
```

## Saída

```json
{ "ok": true, "data": { "draft_id": "<uuid>", "cancelled": true } }
```
