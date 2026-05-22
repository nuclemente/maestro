import type { AnalysisPayload, Sentiment } from '../../types/oneonone';
import { SENTIMENT_LABEL } from '../../types/oneonone';

interface Props {
  analysis: AnalysisPayload;
}

const SENTIMENT_CLASS: Record<Sentiment, string> = {
  positive: 'bg-success-50 text-success-800',
  neutral: 'bg-neutral-100 text-neutral-700',
  concern: 'bg-warning-50 text-warning-800',
};

export default function AnalysisCard({ analysis }: Props) {
  return (
    <section className="space-y-3 rounded-lg border border-neutral-200 bg-neutral-0 p-4">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-900">Resumo da última 1:1</h3>
        <span className={`rounded-full px-2 py-0.5 text-[10px] ${SENTIMENT_CLASS[analysis.sentiment]}`}>
          {SENTIMENT_LABEL[analysis.sentiment]}
        </span>
      </header>
      <p className="whitespace-pre-line text-sm text-neutral-700">{analysis.summary}</p>
      {analysis.follow_ups.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
            Follow-ups
          </h4>
          <ul className="mt-1 list-disc pl-4 text-sm text-neutral-700">
            {analysis.follow_ups.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}
      {analysis.suggested_topics.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
            Sugestões para a próxima
          </h4>
          <ul className="mt-1 list-disc pl-4 text-sm text-neutral-700">
            {analysis.suggested_topics.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
