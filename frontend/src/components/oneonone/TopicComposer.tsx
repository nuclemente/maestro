import { useState } from 'react';
import { Plus } from 'lucide-react';

interface Props {
  disabled?: boolean;
  onAdd: (title: string, body?: string) => Promise<void>;
}

export default function TopicComposer({ disabled, onAdd }: Props) {
  const [title, setTitle] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      await onAdd(trimmed);
      setTitle('');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Novo tema (ex: carreira)"
        disabled={disabled || submitting}
        className="flex-1 rounded-md border border-neutral-200 bg-neutral-0 px-3 py-2 text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={disabled || submitting || !title.trim()}
        className="inline-flex items-center gap-1 rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-neutral-0 transition hover:bg-primary-700 disabled:opacity-50"
      >
        <Plus size={14} /> Adicionar
      </button>
    </form>
  );
}
