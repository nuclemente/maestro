---
name: people-list
description: Lista as pessoas de interesse cadastradas no Maestro (filtro opcional por tipo de relação).
allowed-tools:
  - Bash(python:*)
---

# people-list

Lista pessoas chamando `GET /people` no backend local.

## Entrada

`$ARGUMENTS` é um JSON opcional:

```json
{ "relationship": "direct_report" }
```

Valores válidos: `direct_report`, `peer`, `manager`, `skip_level`, `stakeholder`, `other`.

## Comportamento

```bash
python -m scripts.list_people [--relationship <tipo>]
```

Capture o JSON do stdout e devolva-o.

## Saída

```json
{
  "ok": true,
  "data": {
    "count": 3,
    "people": [ { "id": "...", "name": "...", "email": "...", "relationship": "..." } ],
    "formatted": "• Alice (direct_report) — Senior SWE\n..."
  }
}
```

Em erro:

```json
{ "ok": false, "error": "<mensagem>" }
```
