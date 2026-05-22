import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Person, PersonDraft, PersonInput, PersonUpdate, RelationshipType } from '../types/person';

interface UsePeopleResult {
  people: Person[];
  drafts: PersonDraft[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  create: (input: PersonInput) => Promise<Person>;
  update: (id: string, fields: PersonUpdate) => Promise<Person>;
  remove: (id: string) => Promise<void>;
  recreate: (input: PersonInput) => Promise<Person>;
  confirmDraft: (draftId: string) => Promise<Person>;
  cancelDraft: (draftId: string) => Promise<void>;
}

interface UsePeopleOptions {
  relationship?: RelationshipType | null;
  query?: string | null;
}

function buildQS(opts: UsePeopleOptions): string {
  const params = new URLSearchParams();
  if (opts.relationship) params.set('relationship', opts.relationship);
  if (opts.query?.trim()) params.set('q', opts.query.trim());
  const s = params.toString();
  return s ? `?${s}` : '';
}

export function usePeople(opts: UsePeopleOptions = {}): UsePeopleResult {
  const [people, setPeople] = useState<Person[]>([]);
  const [drafts, setDrafts] = useState<PersonDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [peopleData, draftsData] = await Promise.all([
        api.get<Person[]>(`/people${buildQS(opts)}`),
        api.get<PersonDraft[]>('/people/drafts'),
      ]);
      setPeople(peopleData);
      setDrafts(draftsData);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.relationship, opts.query]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const create = useCallback(async (input: PersonInput) => {
    const created = await api.post<Person>('/people', input);
    await refresh();
    return created;
  }, [refresh]);

  const update = useCallback(async (id: string, fields: PersonUpdate) => {
    const updated = await api.patch<Person>(`/people/${id}`, fields);
    await refresh();
    return updated;
  }, [refresh]);

  const remove = useCallback(async (id: string) => {
    await api.delete(`/people/${id}`);
    await refresh();
  }, [refresh]);

  // Reinsere uma pessoa apagada (usado pelo undo).
  const recreate = useCallback(async (input: PersonInput) => {
    const recreated = await api.post<Person>('/people', input);
    await refresh();
    return recreated;
  }, [refresh]);

  const confirmDraft = useCallback(async (draftId: string) => {
    const person = await api.post<Person>(`/people/drafts/${draftId}/confirm`);
    await refresh();
    return person;
  }, [refresh]);

  const cancelDraft = useCallback(async (draftId: string) => {
    await api.delete(`/people/drafts/${draftId}`);
    await refresh();
  }, [refresh]);

  return { people, drafts, loading, error, refresh, create, update, remove, recreate, confirmDraft, cancelDraft };
}
