---
name: oneonone-analyze-transcript
description: Analisa a transcrição de uma 1:1 (summary + action_items + follow_ups + sentiment + suggested_topics) e grava no backend.
allowed-tools:
  - Bash(python:*)
---

# oneonone-analyze-transcript

Disparada pelo endpoint `/oneonones/sessions/{id}/transcript/analyze` (via
`skill_runner` em `BackgroundTasks`).

A skill busca `raw_text` no backend, divide em chunks (env
`MAESTRO_ONEONONE_TRANSCRIPT_CHUNK_TOKENS`, default 8000), analisa cada chunk,
consolida via `merge_analyses` (puro) e faz PUT em
`/oneonones/sessions/{id}/transcript/analysis`.

> O backend já garante: PUT em `analysis` recria `OneOnOneActionItem`s e cria
> topics `from_transcript` na próxima session planned (sem dedup).

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "transcript_id": "<id>", "session_id": "<id>" }
```

## Comportamento

1. Carrega o transcript:
   ```bash
   python -m scripts.analyze_transcript --fetch --payload '{"session_id": "..."}'
   ```
   Devolve `{raw_text, person_name, prior_summary}`.

2. Para cada chunk:
   ```bash
   python -m scripts.analyze_transcript --build-prompt --payload '{
     "chunk_text": "...", "person_name": "...", "prior_summary": "..."
   }'
   ```
   Chama o Claude (este próprio agente) com o prompt resultante. Resultado: JSON
   com schema:
   ```json
   {
     "summary": "...",
     "follow_ups": ["..."],
     "sentiment": "positive|neutral|concern",
     "suggested_topics": ["..."],
     "action_items": [{"description": "...", "owner": "em|person|other"}]
   }
   ```

3. Consolida os parts:
   ```bash
   python -m scripts.analyze_transcript --merge --payload '{"parts": [{...}, {...}]}'
   ```

4. Valida e grava:
   ```bash
   python -m scripts.analyze_transcript --put --payload '{
     "session_id": "...", "analysis": {...}
   }'
   ```

## Saída

```json
{
  "ok": true,
  "data": {
    "transcript_id": "...",
    "session_id": "...",
    "chunks": 2,
    "action_items": 3,
    "suggested_topics": 2,
    "sentiment": "neutral"
  }
}
```
