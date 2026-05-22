import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { PersonDraft } from '../types/person';

/**
 * Hook leve para o badge da sidebar. Sem polling: atualiza ao montar (em cada
 * navegação) e expõe `refresh` para mutações que precisem invalidar o cache.
 *
 * Eventos `maestro:drafts-changed` no `window` também disparam refresh —
 * permite que páginas que mutam drafts notifiquem o badge sem prop-drilling.
 */
export function useDraftsCount(): { count: number; refresh: () => Promise<void> } {
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    try {
      const drafts = await api.get<PersonDraft[]>('/people/drafts');
      setCount(drafts.length);
    } catch {
      // silencioso — badge não é crítico
    }
  }, []);

  useEffect(() => {
    void refresh();
    const onChanged = () => void refresh();
    window.addEventListener('maestro:drafts-changed', onChanged);
    return () => window.removeEventListener('maestro:drafts-changed', onChanged);
  }, [refresh]);

  return { count, refresh };
}

export function notifyDraftsChanged(): void {
  window.dispatchEvent(new CustomEvent('maestro:drafts-changed'));
}
