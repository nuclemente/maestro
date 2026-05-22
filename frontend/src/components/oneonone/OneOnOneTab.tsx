import { useState } from 'react';
import { Sparkles } from 'lucide-react';
import type { Person } from '../../types/person';
import { usePersonOneOnOne } from '../../hooks/usePersonOneOnOne';
import SessionTimeline from './SessionTimeline';
import NewSessionComposer from './NewSessionComposer';
import TopicCard from './TopicCard';
import TopicComposer from './TopicComposer';
import TranscriptComposer from './TranscriptComposer';
import AnalysisCard from './AnalysisCard';
import ActionItemList from './ActionItemList';

interface Props {
  person: Person;
}

export default function OneOnOneTab({ person }: Props) {
  const {
    sessions,
    selectedSession,
    selectedSessionId,
    loading,
    error,
    selectSession,
    createSession,
    addTopic,
    removeTopic,
    putTranscript,
    triggerAnalysis,
    toggleActionItem,
    triggerPrepare,
  } = usePersonOneOnOne(person.id);

  const [preparing, setPreparing] = useState(false);

  async function handlePrepare() {
    setPreparing(true);
    try {
      await triggerPrepare(person.id);
    } finally {
      setPreparing(false);
    }
  }

  if (loading && !selectedSession) {
    return <p className="text-sm text-neutral-500">Carregando 1:1s…</p>;
  }
  if (error) {
    return <p className="text-sm text-danger-700">{error}</p>;
  }

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between gap-2">
        <SessionTimeline
          sessions={sessions}
          selectedId={selectedSessionId}
          onSelect={(id) => void selectSession(id)}
          trailing={
            <NewSessionComposer
              onCreate={async (scheduledAt) => {
                await createSession({ scheduled_at: scheduledAt });
              }}
            />
          }
        />
        <button
          type="button"
          onClick={handlePrepare}
          disabled={preparing}
          title="Enriquece topics pending via Glean/Slack/Atlassian"
          className="inline-flex shrink-0 items-center gap-1 rounded-md border border-primary-200 bg-primary-50 px-3 py-1.5 text-xs font-medium text-primary-800 transition hover:bg-primary-100 disabled:opacity-50"
        >
          <Sparkles size={12} />
          {preparing ? 'Preparando…' : 'Preparar sessão'}
        </button>
      </header>

      {selectedSession && (
        <>
          <section className="space-y-2">
            <h3 className="text-sm font-semibold text-neutral-900">Temas</h3>
            <TopicComposer
              disabled={!selectedSessionId}
              onAdd={async (title) => {
                await addTopic(selectedSession.id, title);
              }}
            />
            <div className="space-y-2">
              {selectedSession.topics.length === 0 ? (
                <p className="rounded-md border border-dashed border-neutral-200 p-3 text-sm text-neutral-500">
                  Sem temas ainda. Adicione manualmente ou rode <code>:collect-topics</code>.
                </p>
              ) : (
                selectedSession.topics.map((t) => (
                  <TopicCard
                    key={t.id}
                    topic={t}
                    onRemove={() => void removeTopic(t.id)}
                  />
                ))
              )}
            </div>
          </section>

          <TranscriptComposer
            transcript={selectedSession.transcript}
            onSave={(raw) => putTranscript(selectedSession.id, raw)}
            onAnalyze={() => triggerAnalysis(selectedSession.id)}
          />

          {selectedSession.transcript?.analysis && (
            <AnalysisCard analysis={selectedSession.transcript.analysis} />
          )}

          {selectedSession.transcript && (
            <ActionItemList
              items={selectedSession.transcript.action_items}
              onToggle={(id, next) => toggleActionItem(id, next)}
            />
          )}
        </>
      )}
    </div>
  );
}
