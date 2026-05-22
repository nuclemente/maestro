---
name: slack-listener
description: Skill rodada pelo /loop do Claude Code — lê mensagens novas no canal privado do EM e responde apenas a comandos que iniciam com ":".
allowed-tools:
  - mcp__plugin_slack_slack__slack_read_channel
  - mcp__plugin_slack_slack__slack_send_message
  - Bash(python:*)
model: claude-sonnet-4-6
---

# slack-listener (smoke)

Skill executada periodicamente pelo `/loop` do Claude Code (no terminal local
do EM). Cada tick faz uma varredura no **canal privado do EM** e age
**somente** sobre comandos iniciados por `:`.

> O Slack é **canal de entrada**, não app. Mensagens normais são ignoradas
> (não geram resposta). Comandos são prefixados por `:` (ex.: `:ping`,
> `:help`). Comportamentos reais (1:1, transcrição, tarefas) entram **por
> feature** e adicionam novos `:comandos` aqui.

## Onde achar o `channel_id`

O ID do canal privado é **sensível** e mora em `MEMORY.md` (gitignored),
sob o bloco `<!-- maestro-config:slack -->`. Consulte-o de lá — não está
no `config.yaml`, no código nem neste arquivo. (CLAUDE.md descreve a regra
geral.)

## Entrada

`$ARGUMENTS` é um JSON opcional com a forma:

```json
{ "channel_id": "<override>", "limit": 20 }
```

Se `channel_id` ausente, use o valor de `MEMORY.md` (bloco `slack`). Se
`limit` ausente, use `20`.

## Comportamento (cada tick do /loop)

1. **Resolver o canal:** se `$ARGUMENTS.channel_id` veio, use-o; senão, leia
   `MEMORY.md` e pegue `slack.channel_id`. Se nenhum dos dois existir,
   responda com `"ok": false, "error": "missing channel_id"` e encerre.

2. **Ler o canal:**
   `mcp__plugin_slack_slack__slack_read_channel` com o `channel_id` e
   `limit` acima. Considere "novas" as mensagens cujo `ts` é maior que o
   último processado nesta sessão do `/loop` (no primeiro tick, considere
   apenas a mensagem mais recente para não responder histórico antigo).

3. **Filtrar comandos (sempre via script):**

   ```bash
   python -m scripts.parse_command --text "<message.text>" --ts "<message.ts>"
   ```

   O script (em `.claude/skills/slack-listener/scripts/parse_command.py`)
   retorna JSON `{ "kind": "command"|"ignored", ... }`. Nada de regex no
   prompt.

4. **Despachar o comando:**

   | Comando             | Ação                                                                                                                                  |
   | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
   | `:ping`             | Roda `python -m scripts.backend_ping` e responde com o status do backend.                                                              |
   | `:help`             | Lista os comandos disponíveis.                                                                                                         |
   | `:people [tipo]`    | Despacha para a skill `people-list` com `{ "relationship": "<tipo|null>" }` e posta a lista no thread.                                  |
   | `:add-person <kv>`  | Despacha para `people-add`. Args no formato `key=value` (ex.: `name="Alice" email=a@x.com relationship=peer`). Parse via `shlex`/`dict`.|
   | `:show-person <ref>`| Despacha para `people-show` com `{ "id": "<ref>" }` se `<ref>` é UUID, senão `{ "email": "<ref>" }`.                                    |
   | `:update-person …`  | Despacha para `people-update`. Formato: `id=<uuid> field=value field=value`.                                                            |
   | `:discover-person <nome|email>` | Aciona o agent `people` em modo `discover`. O agent posta a proposta com `draft_id` no canal.                              |
   | `:confirm-person <draft_id>`    | Despacha para `people-confirm` e posta confirmação no thread.                                                              |
   | `:cancel-person <draft_id>`     | Despacha para `people-cancel` e posta confirmação no thread.                                                               |
   | `:oneonone <ref>`               | Despacha para a skill `oneonone-show` com `{ "ref": "<id|email>" }`.                                                       |
   | `:collect-topics <ref> [--force]` | Despacha para `oneonone-collect-topics` com `{ "ref": "<...>", "force": true|false }`.                                   |
   | `:close-collection <ref>`       | Despacha para `oneonone-close-collection` com `{ "ref": "<...>" }`.                                                        |
   | `:add-topic <ref> <texto…>`     | Despacha para `oneonone-add-topic` com `{ "ref": "<...>", "title": "<texto>" }` (texto concatena tokens restantes).         |
   | `:prepare <ref>`                | Despacha para `oneonone-prepare` com `{ "ref": "<...>" }`. A skill aciona o agent `oneonone` em modo `enrich`.              |
   | `:new-session <ref> [data]`     | Despacha para `oneonone-new-session` com `{ "ref": "<...>", "scheduled_at": "<data|null>" }`. Data aceita `YYYY-MM-DD HH:MM`. |
   | (desconhecido)      | Responde no canal: `❓ comando não reconhecido: \`<cmd>\``. Sugira `:help`.                                                              |

   Em todos os casos, responder no **mesmo thread** da mensagem original
   via `mcp__plugin_slack_slack__slack_send_message` (use `thread_ts = message.ts`).

5. **Cálculo / IO sempre no script.** Backend ping nunca é feito inline —
   sempre via:

   ```bash
   python -m scripts.backend_ping
   ```

   (vive em `.claude/skills/slack-listener/scripts/backend_ping.py`; retorna
   JSON no stdout: `{ "ok": true|false, "data": {...} | "error": "..." }`).

6. **Responder no canal:** texto curto, sem nomes reais, sem dados sensíveis.

   - `:ping` ok → `🎼 Maestro online — \`<service>\` em \`<env>\` (ts=\`<timestamp>\`)`
   - `:ping` falha → `⚠️ Maestro indisponível: <error>`
   - `:help` → lista plana dos comandos registrados.
   - `:people …` / `:add-person …` / `:show-person …` / `:update-person …` →
     repassa para a skill `people-*` correspondente (via `skill_runner`); a
     resposta do bloco `data.formatted` (quando existir) entra como reply.
   - `:discover-person …` → aciona o agent `people` (modo `discover`); o agent
     mesmo posta a proposta com `draft_id` no thread.
   - `:confirm-person …` / `:cancel-person …` → repassa para `people-confirm` /
     `people-cancel` e posta confirmação curta.

7. **Encerrar** com bloco JSON delimitado:

   ```json
   {
     "ok": true,
     "data": {
       "channel_id": "<resolved>",
       "tick_ts": "<iso8601>",
       "handled": [ { "ts": "<msg.ts>", "command": ":ping", "ok": true } ],
       "ignored": [ { "ts": "<msg.ts>", "reason": "no-colon-prefix" } ]
     }
   }
   ```

   Em erro fatal (ex.: leitura do canal falhou), use `"ok": false` e
   `"error": "<msg>"` — o `/loop` decide se segue ou para.

   **Importante:** ao serializar o `channel_id` no JSON final, está OK —
   o JSON fica em memória local. Não escreva o `channel_id` em logs
   públicos, prints prolixos no canal, ou outros canais Slack.

## Regras (herdadas de `.claude/skills/README.md`)

1. **Nada de cálculo no prompt.** Ping, parsing, qualquer regra de negócio
   futura → `scripts/*.py` puro + CLI + teste pytest.
2. **Slack só via MCP.** Proibido `requests`/`httpx` apontando para
   `slack.com`. Backend Maestro sempre via REST local.
3. **Privacidade.** Sem nomes reais, sem PII no log ou no `data.handled`
   (use só `ts` da mensagem).
4. **`/loop` é local.** Esta skill **não** roda em produção; o EM dispara
   manualmente quando quer ouvir o canal.
5. **IDs sensíveis vêm de MEMORY.md.** Nunca hardcode `channel_id` aqui
   ou em `config.yaml`.

## Limites

- `max_turns`: 4 (read → parse → ping/help → reply).
- `timeout_s`: 60.
- Em qualquer erro de MCP: responder com `"ok": false` e seguir vivo.
