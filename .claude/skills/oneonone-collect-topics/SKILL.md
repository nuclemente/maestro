---
name: oneonone-collect-topics
description: Dispara coleta de temas por DM no Slack para a próxima 1:1 da pessoa (registra CollectionRequest).
allowed-tools:
  - mcp__plugin_slack_slack__slack_send_message
  - Bash(python:*)
---

# oneonone-collect-topics

Envia uma DM para a pessoa pedindo os temas da próxima 1:1. Registra
`CollectionRequest` no backend (status=awaiting). A varredura das respostas
acontece pela skill paralela `oneonone-ingest-dms`.

> **Pré-requisitos:** Person.slack_id presente. Pessoa precisa ter uma session
> `planned`; se não tiver, a skill cria session **adhoc** (`scheduled_at=null`)
> antes de seguir.
>
> **Bloqueio:** se já houver `CollectionRequest` `awaiting` para a próxima session,
> a skill devolve erro. Use `--force` (no payload) para fechar a anterior e
> reenviar a DM.

## Template editável

O texto da DM mora em
`.claude/skills/oneonone-collect-topics/templates/dm_collect_topics.md` e usa
placeholders `{{person_name}}`, `{{session_date}}`, `{{next_session_human}}`.
Edite à vontade — a skill renderiza com `string.Template` (substituição literal,
sem código). Placeholders ausentes viram string vazia.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>", "force": false }
```

## Comportamento

1. Resolve a pessoa por `ref`.
2. Garante session planned (cria adhoc se necessário).
3. Renderiza a DM via `python -m scripts.collect_topics --resolve --payload '$ARGUMENTS'`.
4. Envia DM via `mcp__plugin_slack_slack__slack_send_message` com `channel_id =
   person.slack_id`. O `ts` retornado vai ser usado como `sent_message_ts`.
5. Registra a `CollectionRequest`:
   ```bash
   python -m scripts.collect_topics --register --payload '{"ref": "...", "force": false,
       "slack_channel_id": "<DM channel>", "sent_message_ts": "<ts>"}'
   ```

## Saída

```json
{
  "ok": true,
  "data": {
    "request_id": "...",
    "session_id": "...",
    "channel_id": "<slack DM>",
    "sent_message_ts": "...",
    "formatted": "📨 DM enviada para Ana — aguardando temas."
  }
}
```

Em conflito (sem `--force`):

```json
{ "ok": false, "error": "collection already awaiting (use force=true to reopen)" }
```
