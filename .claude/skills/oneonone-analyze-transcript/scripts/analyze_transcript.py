"""Skill oneonone-analyze-transcript — chunking + prompt + validação + PUT.

Funções puras testáveis:
  - `chunk_transcript(text, max_tokens)` — split em pedaços com overlap pequeno.
  - `build_analysis_prompt(chunk_text, person_name, prior_summary)` — prompt
    estruturado para Claude.
  - `validate_analysis_payload(raw)` — valida schema retornado pelo LLM.
  - `merge_analyses(parts)` — consolida partes (concat + dedup leve por string).

A chamada Claude **não** está nas funções puras — é feita pelo prompt do AGENT.md
(que invoca este script com `--build-prompt`, recebe o JSON, e chama o LLM como
parte do próprio fluxo Claude). Isso mantém o cálculo isolado do I/O.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
DEFAULT_TIMEOUT_S = 10.0
_CHUNK_TOKENS = int(os.environ.get("MAESTRO_ONEONONE_TRANSCRIPT_CHUNK_TOKENS", "8000"))
# Aproximação grosseira: ~4 chars por token.
_CHARS_PER_TOKEN = 4
_VALID_SENTIMENTS = {"positive", "neutral", "concern"}
_VALID_OWNERS = {"em", "person", "other"}


def chunk_transcript(text: str, max_tokens: int = _CHUNK_TOKENS) -> list[str]:
    """Quebra `text` em pedaços de até `max_tokens` (aprox). Pura.

    Cada chunk preserva limites de parágrafo quando possível.
    """
    if not text:
        return []
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text)
    buf: list[str] = []
    size = 0
    for para in paragraphs:
        if size + len(para) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf = []
            size = 0
        if len(para) > max_chars:
            # Parágrafo gigante — corta em pedaços brutos.
            if buf:
                chunks.append("\n\n".join(buf))
                buf = []
                size = 0
            for i in range(0, len(para), max_chars):
                chunks.append(para[i : i + max_chars])
        else:
            buf.append(para)
            size += len(para) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def build_analysis_prompt(
    chunk_text: str,
    person_name: str,
    prior_summary: str | None = None,
) -> str:
    """Monta o prompt estruturado para análise. Pura."""
    prior_block = (
        f"\n## Contexto da última 1:1\n{prior_summary.strip()}\n"
        if prior_summary
        else ""
    )
    return f"""Você é um assistente para Engineering Managers. Analise a transcrição
abaixo de uma 1:1 entre o EM e {person_name}.
{prior_block}
Devolva **apenas** um bloco JSON delimitado por ```json ... ``` no formato:

```json
{{
  "summary": "resumo executivo curto (3-5 frases)",
  "follow_ups": ["ações que precisam acompanhamento mas não são tarefa imediata"],
  "sentiment": "positive | neutral | concern",
  "suggested_topics": ["temas sugeridos para a próxima 1:1"],
  "action_items": [
    {{"description": "ação concreta", "owner": "em | person | other"}}
  ]
}}
```

Diretrizes:
- Não invente informação que não está na transcrição.
- `sentiment` deve refletir o tom geral da conversa.
- `action_items` são compromissos concretos (com responsável).
- Sem PII desnecessária — use só o primeiro nome quando precisar.

## Transcrição
{chunk_text}
"""


def validate_analysis_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Valida e normaliza o JSON devolvido pelo LLM. Pura."""
    if not isinstance(raw, dict):
        raise ValueError("payload precisa ser objeto JSON")
    summary = (raw.get("summary") or "").strip()
    if not summary:
        raise ValueError("analysis.summary obrigatório")

    sentiment = (raw.get("sentiment") or "").strip().lower()
    if sentiment not in _VALID_SENTIMENTS:
        raise ValueError(
            f"sentiment inválido: {sentiment!r} (válidos: {sorted(_VALID_SENTIMENTS)})"
        )

    follow_ups = [str(x).strip() for x in (raw.get("follow_ups") or []) if str(x).strip()]
    suggested = [str(x).strip() for x in (raw.get("suggested_topics") or []) if str(x).strip()]

    items_out: list[dict[str, Any]] = []
    for item in raw.get("action_items") or []:
        if not isinstance(item, dict):
            continue
        desc = (item.get("description") or "").strip()
        if not desc:
            continue
        owner = (item.get("owner") or "em").strip().lower()
        if owner not in _VALID_OWNERS:
            owner = "em"
        items_out.append({"description": desc, "owner": owner})

    return {
        "summary": summary,
        "follow_ups": follow_ups,
        "sentiment": sentiment,
        "suggested_topics": suggested,
        "action_items": items_out,
    }


def merge_analyses(parts: list[dict[str, Any]]) -> dict[str, Any]:
    """Consolida múltiplas análises (uma por chunk). Pura.

    - `summary`: junta com "\\n---\\n" e marca como "(múltiplos trechos)" no início.
    - `sentiment`: pior tom vence (`concern` > `neutral` > `positive`).
    - `follow_ups`, `suggested_topics`, `action_items`: concatena e dedup por
      `description` (lowercase + strip).
    """
    if not parts:
        raise ValueError("nenhuma parte para consolidar")
    if len(parts) == 1:
        return validate_analysis_payload(parts[0])

    rank = {"positive": 0, "neutral": 1, "concern": 2}
    summaries = []
    follow_ups: list[str] = []
    suggested: list[str] = []
    items: list[dict[str, Any]] = []
    sentiment = "positive"
    for raw in parts:
        validated = validate_analysis_payload(raw)
        summaries.append(validated["summary"])
        follow_ups.extend(validated["follow_ups"])
        suggested.extend(validated["suggested_topics"])
        items.extend(validated["action_items"])
        if rank[validated["sentiment"]] > rank[sentiment]:
            sentiment = validated["sentiment"]

    def _dedup(seq: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for s in seq:
            key = s.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

    seen_items: set[str] = set()
    items_dedup: list[dict[str, Any]] = []
    for it in items:
        key = it["description"].lower().strip()
        if key in seen_items:
            continue
        seen_items.add(key)
        items_dedup.append(it)

    return {
        "summary": "(múltiplos trechos)\n" + "\n---\n".join(summaries),
        "follow_ups": _dedup(follow_ups),
        "sentiment": sentiment,
        "suggested_topics": _dedup(suggested),
        "action_items": items_dedup,
    }


# ---------- I/O wrappers ----------


def fetch_transcript(
    session_id: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    base = base_url.rstrip("/")
    try:
        detail = http.get(f"{base}/oneonones/sessions/{session_id}").json()
        transcript = detail.get("transcript") or {}
        return {
            "raw_text": transcript.get("raw_text") or "",
            "track_id": detail.get("track_id"),
        }
    finally:
        if owns:
            http.close()


def put_analysis(
    session_id: str,
    analysis: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    owns = client is None
    http = client or httpx.Client(timeout=timeout_s)
    try:
        resp = http.put(
            f"{base_url.rstrip('/')}/oneonones/sessions/{session_id}/transcript/analysis",
            json=analysis,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()
    finally:
        if owns:
            http.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Análise de transcrição de 1:1.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--build-prompt", action="store_true")
    g.add_argument("--merge", action="store_true")
    g.add_argument("--put", action="store_true")
    g.add_argument("--chunk", action="store_true")
    p.add_argument("--payload", required=True)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        raw = json.loads(args.payload)
        if args.fetch:
            session_id = raw.get("session_id")
            if not session_id:
                raise ValueError("--fetch requer session_id")
            t = fetch_transcript(session_id, args.base_url, timeout_s=args.timeout)
            chunks = chunk_transcript(t["raw_text"])
            data = {"raw_text_len": len(t["raw_text"]), "chunks": len(chunks)}
        elif args.chunk:
            text = raw.get("text") or ""
            data = {"chunks": chunk_transcript(text)}
        elif args.build_prompt:
            chunk_text = raw.get("chunk_text") or ""
            person_name = raw.get("person_name") or "a pessoa"
            prior_summary = raw.get("prior_summary")
            data = {
                "prompt": build_analysis_prompt(chunk_text, person_name, prior_summary)
            }
        elif args.merge:
            parts = raw.get("parts") or []
            data = merge_analyses(parts)
        else:  # --put
            session_id = raw.get("session_id")
            analysis = raw.get("analysis") or {}
            if not session_id or not analysis:
                raise ValueError("--put requer session_id e analysis")
            validated = validate_analysis_payload(analysis)
            data = put_analysis(
                session_id, validated, args.base_url, timeout_s=args.timeout
            )
    except (ValueError, RuntimeError, httpx.HTTPError, json.JSONDecodeError) as exc:
        sys.stdout.write(
            json.dumps({"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}, ensure_ascii=False)
            + "\n"
        )
        return 1
    sys.stdout.write(json.dumps({"ok": True, "data": data}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
