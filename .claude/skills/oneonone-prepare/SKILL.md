---
name: oneonone-prepare
description: Enriquece UM topic pending da próxima session de 1:1 consultando Glean, Slack e Atlassian. Frontend/caller chama repetidamente até `topics_remaining == 0`.
allowed-tools:
  - mcp__glean_default__search
  - mcp__plugin_slack_slack__slack_search_public
  - mcp__atlassian__search
  - Bash(python:*)
model: claude-sonnet-4-6
---

# oneonone-prepare

**Unidade de trabalho atômica.** Cada execução enriquece **um único topic pending**
da próxima session planned da pessoa. O caller (UI ou skill) chama repetidamente
até `topics_remaining == 0`.

> Mantenha o trabalho curto pra caber em poucos turns do `claude -p`. Use 1 chamada
> por MCP (sem chat de síntese) + 1 chamada ao script de PUT. Cap: ~6 turns.

## Entrada

`$ARGUMENTS` é um JSON:

```json
{ "ref": "<id|email>" }
```

## Comportamento (siga exatamente esta ordem)

1. **Resolver o próximo topic pending:**

   ```bash
   python -m scripts.prepare_session --next-topic --payload '$ARGUMENTS'
   ```

   Saída esperada (bloco ```json```):

   ```json
   { "ok": true, "data": {
     "session_id": "...",
     "topic": { "id": "...", "title": "...", "body": "..." } | null,
     "topics_remaining": 3,
     "person_name": "Ana"
   }}
   ```

   Se `topic` for `null` (não há mais topics pending), devolva direto:

   ```json
   { "ok": true, "data": { "session_id": "...", "topic_id": null, "topics_remaining": 0, "formatted": "✅ Tudo pronto." } }
   ```

   **Não rode os MCPs nesse caso.** Encerre.

2. **Consultar Glean** com `query=topic.title` (em 1 chamada, sem retry):
   - `mcp__glean_default__search` com `query=<topic.title>`. Pegue os 3 primeiros hits.
   - Se falhar, registre `"glean"` em `errors` e siga.

3. **Consultar Slack** (1 chamada):
   - `mcp__plugin_slack_slack__slack_search_public` com `query=<topic.title>`. Pegue
     os 3 primeiros message hits.
   - Se falhar, registre `"slack"` em `errors`.

4. **Consultar Atlassian** (1 chamada):
   - `mcp__atlassian__search` com `query=<topic.title>`. Pegue os 3 primeiros hits.
   - Se falhar, registre `"atlassian"` em `errors`.

5. **Consolidar e gravar** (1 script):

   ```bash
   python -m scripts.enrich_topic --topic-id <topic.id> --payload '{
     "topic": {"id": "<topic.id>", "title": "<topic.title>"},
     "glean_hits": [<até 3 itens com title/url/snippet>],
     "slack_hits": [<até 3 itens>],
     "atlassian_hits": [<até 3 itens>],
     "errors": [<lista>],
     "top_n": 3
   }'
   ```

   O script faz o PUT em `/oneonones/topics/{id}/enrichment` e devolve o topic
   atualizado.

6. **Devolver** bloco JSON final:

   ```json
   { "ok": true, "data": {
     "session_id": "...",
     "topic_id": "<id>",
     "topic_title": "...",
     "hits": 7,
     "errors": ["..."],
     "topics_remaining": 2,
     "formatted": "🧰 Enriquecido: <title> (7 hits, faltam 2)"
   }}
   ```

   Em erro fatal (pessoa não encontrada, etc.):

   ```json
   { "ok": false, "error": "<mensagem>" }
   ```

## Regras

1. **Um topic por chamada.** Não tente processar todos numa só execução.
2. **Cálculo no script** (`enrich_topic.py`) — não monte o payload no prompt.
3. **Erro parcial é OK.** Salve enrichment com `errors=[...]` se uma fonte falhar.
4. **Sempre encerre com bloco ```json```.** Sem isso, o `skill_runner` falha.
