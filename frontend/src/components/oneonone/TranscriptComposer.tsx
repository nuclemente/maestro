import { useEffect, useState } from 'react';
import { FileText, Loader2, RefreshCw } from 'lucide-react';
import type { OneOnOneTranscript } from '../../types/oneonone';

interface Props {
  transcript: OneOnOneTranscript | null;
  onSave: (rawText: string) => Promise<void>;
  onAnalyze: () => Promise<void>;
}

export default function TranscriptComposer({ transcript, onSave, onAnalyze }: Props) {
  const [text, setText] = useState(transcript?.raw_text ?? '');
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    setText(transcript?.raw_text ?? '');
  }, [transcript?.id, transcript?.raw_text]);

  async function save() {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await onSave(text.trim());
    } finally {
      setSaving(false);
    }
  }

  async function analyze() {
    if (!transcript || !text.trim()) {
      // Salva primeiro pra existir transcript.
      await save();
    }
    setAnalyzing(true);
    try {
      await onAnalyze();
    } finally {
      setAnalyzing(false);
    }
  }

  const hasAnalysis = !!transcript?.analyzed_at;
  const stale = !!transcript?.analysis_stale;

  return (
    <section className="space-y-3 rounded-lg border border-neutral-200 bg-neutral-0 p-4">
      <header className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-neutral-900">
          <FileText size={16} /> Transcrição
        </h3>
        {stale && (
          <span className="rounded-full bg-warning-50 px-2 py-0.5 text-[10px] text-warning-800">
            Análise desatualizada
          </span>
        )}
      </header>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Cole a transcrição da 1:1 aqui…"
        className="h-48 w-full resize-y rounded-md border border-neutral-200 bg-neutral-0 p-3 text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none"
      />
      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={save}
          disabled={saving || !text.trim() || text.trim() === transcript?.raw_text}
          className="rounded-md border border-neutral-200 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-50 disabled:opacity-50"
        >
          {saving ? 'Salvando…' : 'Salvar texto'}
        </button>
        <button
          type="button"
          onClick={analyze}
          disabled={analyzing || !text.trim()}
          className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-neutral-0 transition hover:bg-primary-700 disabled:opacity-50"
        >
          {analyzing ? <Loader2 size={14} className="animate-spin" /> : hasAnalysis ? <RefreshCw size={14} /> : null}
          {analyzing ? 'Analisando…' : hasAnalysis ? 'Re-analisar' : 'Analisar'}
        </button>
      </div>
    </section>
  );
}
