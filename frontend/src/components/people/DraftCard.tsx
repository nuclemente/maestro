import { Check, Pencil, Trash2 } from 'lucide-react';
import Button from '../ui/Button';
import InitialsAvatar from './InitialsAvatar';
import RelationshipChip from './RelationshipChip';
import type { PersonDraft } from '../../types/person';

interface Props {
  draft: PersonDraft;
  confirming?: boolean;
  cancelling?: boolean;
  onEdit: (draft: PersonDraft) => void;
  onConfirm: (draft: PersonDraft) => void;
  onCancel: (draft: PersonDraft) => void;
}

export default function DraftCard({ draft, confirming, cancelling, onEdit, onConfirm, onCancel }: Props) {
  return (
    <article className="maestro-fade-in flex flex-col gap-4 rounded-lg border border-neutral-200 bg-neutral-0 p-5 shadow-sm">
      <header className="flex items-start gap-4">
        <InitialsAvatar name={draft.name} relationship={draft.relationship} size={48} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-neutral-800">{draft.name}</h3>
            <span className="rounded-full bg-warning-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warning-700">
              proposta
            </span>
            <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-[10px] font-medium text-neutral-600">
              {draft.source}
            </span>
          </div>
          <div className="mt-1 truncate text-sm text-neutral-500">{draft.email}</div>
          {draft.role && (
            <div className="text-xs text-neutral-500">{draft.role}</div>
          )}
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <RelationshipChip relationship={draft.relationship} size="md" />
        {draft.slack_id && (
          <span className="rounded-md bg-neutral-50 px-2 py-1 text-[11px] text-neutral-600">
            slack <code className="font-mono text-neutral-800">{draft.slack_id}</code>
          </span>
        )}
        {draft.jira_account_id && (
          <span className="rounded-md bg-neutral-50 px-2 py-1 text-[11px] text-neutral-600">
            jira <code className="font-mono text-neutral-800">{draft.jira_account_id}</code>
          </span>
        )}
        {draft.github_handle && (
          <span className="rounded-md bg-neutral-50 px-2 py-1 text-[11px] text-neutral-600">
            gh <code className="font-mono text-neutral-800">{draft.github_handle}</code>
          </span>
        )}
      </div>

      {draft.notes && (
        <p className="whitespace-pre-wrap text-xs text-neutral-500">{draft.notes}</p>
      )}

      <footer className="flex items-center justify-end gap-2 border-t border-neutral-100 pt-3">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onCancel(draft)}
          loading={cancelling}
          disabled={confirming}
        >
          <Trash2 size={14} />
          {cancelling ? 'Descartando…' : 'Descartar'}
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onEdit(draft)}
          disabled={confirming || cancelling}
        >
          <Pencil size={14} />
          Editar
        </Button>
        <Button
          size="sm"
          variant="primary"
          onClick={() => onConfirm(draft)}
          loading={confirming}
          disabled={cancelling}
        >
          <Check size={14} />
          {confirming ? 'Confirmando…' : 'Confirmar'}
        </Button>
      </footer>
    </article>
  );
}
