import { useState } from 'react';
import { CalendarPlus, X } from 'lucide-react';

interface Props {
  onCreate: (scheduledAt: string | null) => Promise<void>;
}

/**
 * Mini-composer inline: clicar abre um input datetime-local + ação.
 * Permite criar session "ad-hoc" (sem data) ou agendada.
 */
export default function NewSessionComposer({ onCreate }: Props) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(adhoc: boolean) {
    setSubmitting(true);
    try {
      const scheduled = adhoc
        ? null
        : value
          ? new Date(value).toISOString()
          : null;
      await onCreate(scheduled);
      setOpen(false);
      setValue('');
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        title="Criar nova sessão"
        className="inline-flex shrink-0 items-center gap-1 rounded-full border border-dashed border-neutral-300 px-3 py-1.5 text-xs text-neutral-600 transition hover:border-primary-400 hover:text-primary-700"
      >
        <CalendarPlus size={12} /> Nova sessão
      </button>
    );
  }

  return (
    <div className="flex shrink-0 items-center gap-1 rounded-full border border-primary-200 bg-primary-50 px-2 py-1">
      <input
        type="datetime-local"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={submitting}
        className="rounded bg-neutral-0 px-2 py-1 text-xs text-neutral-900 focus:outline-none"
      />
      <button
        type="button"
        onClick={() => void submit(false)}
        disabled={submitting || !value}
        className="rounded bg-primary-600 px-2 py-1 text-xs font-medium text-neutral-0 transition hover:bg-primary-700 disabled:opacity-50"
      >
        Criar
      </button>
      <button
        type="button"
        onClick={() => void submit(true)}
        disabled={submitting}
        title="Sem data específica"
        className="rounded px-2 py-1 text-xs text-neutral-700 transition hover:bg-neutral-100"
      >
        Sem data
      </button>
      <button
        type="button"
        onClick={() => {
          setOpen(false);
          setValue('');
        }}
        aria-label="Cancelar"
        className="rounded p-1 text-neutral-500 hover:text-neutral-900"
      >
        <X size={12} />
      </button>
    </div>
  );
}
