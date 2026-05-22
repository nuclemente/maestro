---
name: people-show
description: Mostra os detalhes de uma pessoa cadastrada (por id ou e-mail).
allowed-tools:
  - Bash(python:*)
---

# people-show

Busca uma pessoa por `id` ou `email` e devolve a ficha completa.

## Entrada

`$ARGUMENTS` é um JSON com um dos campos:

```json
{ "id": "<uuid>" }
```

ou

```json
{ "email": "alice@example.com" }
```

## Comportamento

```bash
python -m scripts.show_person --payload '$ARGUMENTS'
```

## Saída

```json
{
  "ok": true,
  "data": { "id": "...", "name": "...", "email": "...", "...": "..." },
  "formatted": "Alice (direct_report)\n  email: alice@example.com\n  ..."
}
```
