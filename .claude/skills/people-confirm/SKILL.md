---
name: people-confirm
description: Promove um draft de pessoa para Person (POST /people/drafts/{id}/confirm).
allowed-tools:
  - Bash(python:*)
---

# people-confirm

Confirma um draft proposto pelo agente `people` (modo enriquecedor) e o promove
para a tabela `Person`. O draft é apagado após a confirmação.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "draft_id": "<uuid>" }
```

## Comportamento

```bash
python -m scripts.confirm_draft --draft-id <uuid>
```

## Saída

```json
{ "ok": true, "data": { "person": { "id": "...", "name": "...", "email": "..." } } }
```
