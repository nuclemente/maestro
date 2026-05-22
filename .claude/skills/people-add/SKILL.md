---
name: people-add
description: Cadastra uma nova pessoa de interesse no Maestro (POST /people).
allowed-tools:
  - Bash(python:*)
---

# people-add

Cadastra uma pessoa diretamente em `Person`. Use o agente `people` quando o cadastro
precisar de descoberta/enriquecimento prévio.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{
  "name": "Alice Lima",
  "email": "alice@example.com",
  "relationship": "direct_report",
  "role": "Senior SWE",
  "slack_id": "U001",
  "jira_account_id": "557058:abc",
  "github_handle": "alice-gh",
  "start_date": "2025-01-15",
  "notes": "primeira contratação do squad"
}
```

Campos obrigatórios: `name`, `email`, `relationship`. Os demais são opcionais.

## Comportamento

```bash
python -m scripts.add_person --payload '$ARGUMENTS'
```

## Saída

```json
{ "ok": true, "data": { "id": "...", "name": "...", "email": "...", "relationship": "..." } }
```
