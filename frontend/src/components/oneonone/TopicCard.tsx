import { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, AlertTriangle, Trash2 } from 'lucide-react';
import type { OneOnOneTopic } from '../../types/oneonone';

interface Props {
  topic: OneOnOneTopic;
  onRemove?: () => void;
}

const SOURCE_LABEL: Record<OneOnOneTopic['source'], string> = {
  manual: 'Manual',
  slack_collection: 'DM',
  from_transcript: 'Da transcrição',
};

export default function TopicCard({ topic, onRemove }: Props) {
  const [open, setOpen] = useState(false);
  const enriched = topic.enriched_at && topic.enrichment;
  const hits = topic.enrichment?.hits ?? [];
  const errors = topic.enrichment?.errors ?? [];

  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-0">
      <header className="flex items-start gap-3 p-3">
        <button
          type="button"
          aria-label={open ? 'Recolher' : 'Expandir'}
          onClick={() => setOpen((v) => !v)}
          className="mt-0.5 text-neutral-500 transition hover:text-neutral-900"
          disabled={!enriched}
        >
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="truncate text-sm font-medium text-neutral-900">{topic.title}</h4>
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-neutral-600">
              {SOURCE_LABEL[topic.source]}
            </span>
            {enriched && (
              <span className="rounded-full bg-primary-50 px-2 py-0.5 text-[10px] text-primary-800">
                {hits.length} hits
              </span>
            )}
            {errors.length > 0 && (
              <span
                title={`Fontes que falharam: ${errors.join(', ')}`}
                className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2 py-0.5 text-[10px] text-warning-800"
              >
                <AlertTriangle size={10} /> {errors.length}
              </span>
            )}
          </div>
          {topic.body && (
            <p className="mt-1 line-clamp-2 text-xs text-neutral-600">{topic.body}</p>
          )}
        </div>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            aria-label="Remover topic"
            className="text-neutral-400 transition hover:text-danger-700"
          >
            <Trash2 size={14} />
          </button>
        )}
      </header>
      {open && enriched && (
        <div className="space-y-2 border-t border-neutral-100 px-3 py-3">
          {topic.enrichment?.summary && (
            <p className="text-xs text-neutral-700">{topic.enrichment.summary}</p>
          )}
          <ul className="space-y-1.5">
            {hits.map((h, idx) => (
              <li key={idx} className="text-xs">
                <span className="mr-1 rounded bg-neutral-100 px-1.5 py-0.5 text-[10px] uppercase text-neutral-600">
                  {h.source}
                </span>
                {h.url ? (
                  <a
                    href={h.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary-700 hover:underline"
                  >
                    {h.title}
                    <ExternalLink size={10} className="ml-0.5 inline" />
                  </a>
                ) : (
                  <span className="text-neutral-900">{h.title}</span>
                )}
                {h.snippet && (
                  <p className="ml-1 mt-0.5 text-neutral-600">{h.snippet}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
