import { Calendar, CircleDot, CheckCircle2, XCircle } from 'lucide-react';
import type { OneOnOneSession, SessionStatus } from '../../types/oneonone';

interface Props {
  sessions: OneOnOneSession[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  trailing?: React.ReactNode;
}

const STATUS_ICON: Record<SessionStatus, JSX.Element> = {
  planned: <CircleDot size={14} className="text-primary-600" />,
  done: <CheckCircle2 size={14} className="text-success-600" />,
  cancelled: <XCircle size={14} className="text-danger-600" />,
};

function fmtDate(iso: string | null): string {
  if (!iso) return 'sem data';
  const d = new Date(iso);
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
}

export default function SessionTimeline({ sessions, selectedId, onSelect, trailing }: Props) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <p className="text-sm text-neutral-500">
          Nenhuma 1:1 registrada ainda.
        </p>
        {trailing}
      </div>
    );
  }
  const ordered = [...sessions].sort((a, b) => {
    const av = a.scheduled_at ?? '';
    const bv = b.scheduled_at ?? '';
    return bv.localeCompare(av);
  });
  return (
    <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Sessões de 1:1">
      {ordered.map((s) => {
        const active = s.id === selectedId;
        return (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onSelect(s.id)}
            className={[
              'flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition',
              active
                ? 'border-primary-500 bg-primary-50 text-primary-900'
                : 'border-neutral-200 bg-neutral-0 text-neutral-700 hover:bg-neutral-50',
            ].join(' ')}
          >
            {STATUS_ICON[s.status]}
            <span className="font-medium">{fmtDate(s.scheduled_at)}</span>
            {s.external_event_id && (
              <Calendar size={12} className="text-neutral-400" aria-label="Vindo do Google Calendar" />
            )}
          </button>
        );
      })}
      {trailing}
    </div>
  );
}
