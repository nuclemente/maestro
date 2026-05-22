import { useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import DraftCard from '../components/people/DraftCard';
import EmptyState from '../components/people/EmptyState';
import PersonDrawer from '../components/people/PersonDrawer';
import { usePeople } from '../hooks/usePeople';
import { notifyDraftsChanged } from '../hooks/useDraftsCount';
import type { Person, PersonDraft, PersonInput } from '../types/person';

export default function PeopleDrafts() {
  const { drafts, loading, confirmDraft, cancelDraft, refresh } = usePeople();
  const [editing, setEditing] = useState<PersonDraft | null>(null);
  const [busy, setBusy] = useState<{ id: string; op: 'confirm' | 'cancel' } | null>(null);

  async function handleConfirm(draft: PersonDraft) {
    setBusy({ id: draft.id, op: 'confirm' });
    try {
      const person: Person = await confirmDraft(draft.id);
      toast.success(`Proposta confirmada — ${person.name} cadastrada`);
      notifyDraftsChanged();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function handleCancel(draft: PersonDraft) {
    setBusy({ id: draft.id, op: 'cancel' });
    try {
      await cancelDraft(draft.id);
      toast.success('Proposta descartada');
      notifyDraftsChanged();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function handleEditSubmit(input: PersonInput) {
    if (!editing) return;
    try {
      await api.patch<PersonDraft>(`/people/drafts/${editing.id}`, input);
      toast.success('Proposta atualizada');
      await refresh();
      notifyDraftsChanged();
      setEditing(null);
    } catch (err) {
      toast.error((err as Error).message);
      throw err;
    }
  }

  return (
    <section className="mx-auto flex max-w-5xl flex-col px-8 pb-20 pt-10">
      <header className="mb-8">
        <Link
          to="/people"
          className="mb-3 inline-flex items-center gap-1.5 text-xs font-medium text-neutral-500 transition hover:text-neutral-700"
        >
          <ArrowLeft size={14} />
          Voltar para Pessoas
        </Link>
        <h1 className="text-3xl font-bold tracking-tight text-neutral-800">Propostas pendentes</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Cadastros sugeridos pelo agente <code className="rounded bg-neutral-100 px-1.5 py-0.5 text-[11px] font-mono text-neutral-700">people</code>{' '}
          ou criados manualmente. Revise antes de promover ao cadastro principal.
        </p>
      </header>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-lg border border-neutral-200 bg-neutral-0" />
          ))}
        </div>
      ) : drafts.length === 0 ? (
        <EmptyState
          title="Nenhuma proposta pendente"
          description="Quando o agente people criar uma proposta de cadastro, ela aparece aqui."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {drafts.map((d) => (
            <DraftCard
              key={d.id}
              draft={d}
              confirming={busy?.id === d.id && busy.op === 'confirm'}
              cancelling={busy?.id === d.id && busy.op === 'cancel'}
              onEdit={setEditing}
              onConfirm={handleConfirm}
              onCancel={handleCancel}
            />
          ))}
        </div>
      )}

      <PersonDrawer
        open={editing !== null}
        mode="edit-draft"
        initialForm={editing}
        onClose={() => setEditing(null)}
        onSubmit={handleEditSubmit}
      />
    </section>
  );
}
