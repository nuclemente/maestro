---
name: oneonone-ingest-dms
description: Loop dedicado que varre CollectionRequests awaiting, lê DMs do Slack e ingere respostas como topics.
allowed-tools:
  - mcp__plugin_slack_slack__slack_read_channel
  - Bash(python:*)
---

# oneonone-ingest-dms

Skill rodada em `/loop` próprio (paralelo ao `slack-listener`). A cada tick:

1. Lista `CollectionRequest`s `awaiting` no backend.
2. Para cada uma, lê a DM da pessoa via
   `mcp__plugin_slack_slack__slack_read_channel` com
   `channel_id = request.slack_channel_id` (id da DM com a pessoa).
3. Filtra mensagens posteriores a `request.sent_message_ts` cujo autor seja a
   pessoa (não o bot).
4. Parseia as mensagens em uma lista de temas via
   `python -m scripts.ingest_dms --parse --payload '{...}'`.
5. Decide se fecha a coleta (heurística: mensagem contém "pronto"/"acabou"/"done"/
   "é isso" OU `last_polled_at` há mais de 24h).
6. POSTa em `/oneonones/collection-requests/{id}/ingest` com `topics + close`.

> **Requer escopo `im:history`** no token Slack do MCP. Se um GET retornar 403,
> registra erro e segue para o próximo request.

## Entrada

`$ARGUMENTS` é um JSON opcional. Sem campos obrigatórios; útil para overrides
em testes:

```json
{ "base_url": "http://127.0.0.1:8001" }
```

## Comportamento

Para cada `request` retornado por `GET /oneonones/collection-requests?status=awaiting`:

- Chame `mcp__plugin_slack_slack__slack_read_channel` com `channel_id` da
  request e `limit=50`.
- Chame o parser:
  ```bash
  python -m scripts.ingest_dms --parse --payload '{
    "messages": [{"user": "U123", "ts": "...", "text": "..."}, ...],
    "person_slack_id": "U123",
    "since_ts": "<sent_message_ts>",
    "last_polled_at": "<iso8601|null>"
  }'
  ```
  Retorna `{"topics": [...], "close": bool}`.
- Chame o registrador:
  ```bash
  python -m scripts.ingest_dms --post --payload '{
    "request_id": "<id>",
    "topics": [...],
    "close": true
  }'
  ```

## Saída final

```json
{
  "ok": true,
  "data": {
    "processed": 3,
    "topics_added": 7,
    "closed": 1,
    "errors": []
  }
}
```
