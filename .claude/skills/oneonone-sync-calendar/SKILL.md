---
name: oneonone-sync-calendar
description: Sincroniza eventos `1:1 …` do Google Calendar com sessions de 1:1 no Maestro (upsert por external_event_id).
allowed-tools:
  - mcp__google-workspace__calendar_listEvents
  - mcp__google-workspace__calendar_list
  - Bash(python:*)
---

# oneonone-sync-calendar

Skill rodada em `/loop` próprio (ex.: `/loop 30m /oneonone-sync-calendar`).

A cada tick:

1. Lista eventos da agenda primária do EM via
   `mcp__google-workspace__calendar_listEvents` (janela: agora → +4 semanas).
2. Filtra os eventos cujo título começa com `1:1` (case-insensitive).
3. Para cada evento, identifica o attendee distinto do EM e tenta casar pelo
   `email` com `Person.email`. Sem match → registra em `unmatched_emails` e segue.
4. POSTa em `/people/{person_id}/oneonone-track/sessions/upsert-external`
   (idempotente por `external_event_id`).

> **Não destrutivo:** sessions sem `external_event_id` (criadas manualmente ou
> adhoc) ficam intactas. Sessions com `external_event_id` são reconciliadas
> (cancelled se evento foi removido — `status=cancelled` no payload).

## Entrada

`$ARGUMENTS` opcional:

```json
{
  "calendar_id": "primary",
  "horizon_days": 28,
  "em_email": "rodrigo@example.com"
}
```

`em_email` resolvido prioritariamente do payload, depois do env
`MAESTRO_EM_EMAIL`. Se nenhum dos dois, falhe com erro acionável.

## Comportamento

1. Listar eventos (MCP).
2. Extrair candidatos:
   ```bash
   python -m scripts.sync_calendar --extract --payload '{"events": [...], "em_email": "..."}'
   ```
3. Carregar pessoas e casar:
   ```bash
   python -m scripts.sync_calendar --match --payload '{"candidates": [...]}'
   ```
4. POSTar upserts:
   ```bash
   python -m scripts.sync_calendar --apply --payload '{"upserts": [...]}'
   ```

## Saída final

```json
{
  "ok": true,
  "data": {
    "events_seen": 12,
    "candidates": 4,
    "sessions_upserted": 4,
    "unmatched_emails": ["beto@externo.com"]
  }
}
```
