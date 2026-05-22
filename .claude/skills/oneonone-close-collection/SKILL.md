---
name: oneonone-close-collection
description: Fecha a CollectionRequest 'awaiting' da próxima session de 1:1 sem reenviar DM.
allowed-tools:
  - Bash(python:*)
---

# oneonone-close-collection

Útil quando o EM já obteve os temas por outro canal ou quer abandonar a coleta
pendente sem usar `:collect-topics --force` (que reenvia DM).

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>" }
```

## Comportamento

```bash
python -m scripts.close_collection --payload '$ARGUMENTS'
```

## Saída

```json
{
  "ok": true,
  "data": {
    "closed_request_id": "...",
    "formatted": "🔕 Coleta de temas para Ana fechada (sem reenviar)."
  }
}
```

Se não houver coleta awaiting, devolve `{ "ok": false, "error": "no awaiting collection" }`.
