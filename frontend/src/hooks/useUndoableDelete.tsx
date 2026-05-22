import { useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import type { Person, PersonInput } from '../types/person';

interface Options {
  remove: (id: string) => Promise<void>;
  recreate: (input: PersonInput) => Promise<Person>;
  windowMs?: number;
}

/**
 * Remoção com janela de "Desfazer". A pessoa é apagada imediatamente no
 * backend; o toast permanece visível por `windowMs` (default 5000) e oferece
 * o botão **Desfazer** que recria a pessoa com o mesmo payload.
 *
 * Bem mais simples do que soft-delete no backend e suficiente para EM solo.
 */
export function useUndoableDelete({ remove, recreate, windowMs = 5000 }: Options) {
  const inflightToast = useRef<string | null>(null);

  return useCallback(
    async (person: Person) => {
      const snapshot: PersonInput = {
        name: person.name,
        email: person.email,
        relationship: person.relationship,
        role: person.role ?? null,
        slack_id: person.slack_id ?? null,
        jira_account_id: person.jira_account_id ?? null,
        github_handle: person.github_handle ?? null,
        start_date: person.start_date ?? null,
        notes: person.notes ?? null,
      };

      try {
        await remove(person.id);
      } catch (err) {
        toast.error((err as Error).message);
        return;
      }

      if (inflightToast.current) toast.dismiss(inflightToast.current);

      inflightToast.current = toast(
        (t) => (
          <div className="flex items-center gap-3 text-sm">
            <span>
              <strong>{person.name}</strong> removida
            </span>
            <button
              type="button"
              onClick={async () => {
                toast.dismiss(t.id);
                try {
                  await recreate(snapshot);
                  toast.success('Restaurada');
                } catch (err) {
                  toast.error((err as Error).message);
                }
              }}
              className="rounded-md bg-neutral-800 px-2.5 py-1 text-xs font-medium text-neutral-0 transition hover:bg-neutral-900"
            >
              Desfazer
            </button>
          </div>
        ),
        { duration: windowMs, position: 'top-right' },
      );
    },
    [remove, recreate, windowMs],
  );
}
