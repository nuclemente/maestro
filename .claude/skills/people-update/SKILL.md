---
name: people-update
description: Atualiza campos de uma pessoa já cadastrada (PATCH /people/{id}).
allowed-tools:
  - Bash(python:*)
---

# people-update

Atualização parcial — só os campos enviados são modificados.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{
  "id": "<uuid>",
  "fields": {
    "role": "Tech Lead",
    "notes": "promovida em 2026-Q1"
  }
}
```

Campos editáveis: `name`, `email`, `relationship`, `role`, `slack_id`,
`jira_account_id`, `github_handle`, `start_date`, `notes`.

## Comportamento

```bash
python -m scripts.update_person --payload '$ARGUMENTS'
```

## Saída

```json
{ "ok": true, "data": { "id": "...", "updated_fields": ["role", "notes"], "person": { ... } } }
```
