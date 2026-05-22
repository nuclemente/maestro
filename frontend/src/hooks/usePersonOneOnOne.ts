import { useCallback, useEffect, useState } from 'react';
import { api } from '../lib/api';
import type {
  ActionItemStatus,
  OneOnOneSession,
  OneOnOneSessionDetail,
  OneOnOneTopic,
  OneOnOneTrack,
  OneOnOneTranscript,
} from '../types/oneonone';

interface UseOneOnOneResult {
  track: OneOnOneTrack | null;
  sessions: OneOnOneSession[];
  selectedSession: OneOnOneSessionDetail | null;
  selectedSessionId: string | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  selectSession: (id: string | null) => Promise<void>;
  createSession: (input: { scheduled_at?: string | null }) => Promise<OneOnOneSession>;
  addTopic: (sessionId: string, title: string, body?: string) => Promise<OneOnOneTopic>;
  updateTopic: (topicId: string, fields: Partial<OneOnOneTopic>) => Promise<OneOnOneTopic>;
  removeTopic: (topicId: string) => Promise<void>;
  putTranscript: (sessionId: string, rawText: string) => Promise<OneOnOneTranscript>;
  triggerAnalysis: (sessionId: string) => Promise<void>;
  toggleActionItem: (itemId: string, status: ActionItemStatus) => Promise<void>;
  triggerPrepare: (ref: string) => Promise<void>;
}

export function usePersonOneOnOne(personId: string | null): UseOneOnOneResult {
  const [track, setTrack] = useState<OneOnOneTrack | null>(null);
  const [sessions, setSessions] = useState<OneOnOneSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<OneOnOneSessionDetail | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!personId) {
      setTrack(null);
      setSessions([]);
      setSelectedSession(null);
      setSelectedSessionId(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [trackData, sessionsData] = await Promise.all([
        api.get<OneOnOneTrack>(`/people/${personId}/oneonone-track`),
        api.get<OneOnOneSession[]>(`/people/${personId}/oneonone-track/sessions`),
      ]);
      setTrack(trackData);
      setSessions(sessionsData);
      // Mantém seleção; se não houver, escolhe a próxima planned ou a mais recente.
      if (!selectedSessionId) {
        const planned = sessionsData
          .filter((s) => s.status === 'planned')
          .sort((a, b) => {
            const av = a.scheduled_at ?? '';
            const bv = b.scheduled_at ?? '';
            return av.localeCompare(bv);
          })[0];
        const next = planned ?? sessionsData[0] ?? null;
        if (next) {
          setSelectedSessionId(next.id);
        }
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [personId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Carrega detalhe da session selecionada (com polling se análise stale).
  useEffect(() => {
    if (!selectedSessionId) {
      setSelectedSession(null);
      return;
    }
    let cancelled = false;
    let timer: number | null = null;
    const tick = async () => {
      try {
        const detail = await api.get<OneOnOneSessionDetail>(
          `/oneonones/sessions/${selectedSessionId}`,
        );
        if (!cancelled) setSelectedSession(detail);
      } catch (err) {
        if (!cancelled) setError((err as Error).message);
      }
    };
    void tick();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [selectedSessionId]);

  const selectSession = useCallback(async (id: string | null) => {
    setSelectedSessionId(id);
  }, []);

  const createSession = useCallback(
    async (input: { scheduled_at?: string | null }) => {
      if (!personId) throw new Error('person not selected');
      const created = await api.post<OneOnOneSession>(
        `/people/${personId}/oneonone-track/sessions`,
        { scheduled_at: input.scheduled_at ?? null },
      );
      const sessionsData = await api.get<OneOnOneSession[]>(
        `/people/${personId}/oneonone-track/sessions`,
      );
      setSessions(sessionsData);
      setSelectedSessionId(created.id);
      return created;
    },
    [personId],
  );

  const addTopic = useCallback(
    async (sessionId: string, title: string, body?: string) => {
      const topic = await api.post<OneOnOneTopic>(
        `/oneonones/sessions/${sessionId}/topics`,
        { title, body },
      );
      const detail = await api.get<OneOnOneSessionDetail>(
        `/oneonones/sessions/${sessionId}`,
      );
      setSelectedSession(detail);
      return topic;
    },
    [],
  );

  const updateTopic = useCallback(
    async (topicId: string, fields: Partial<OneOnOneTopic>) => {
      const updated = await api.patch<OneOnOneTopic>(`/oneonones/topics/${topicId}`, fields);
      if (selectedSessionId) {
        const detail = await api.get<OneOnOneSessionDetail>(
          `/oneonones/sessions/${selectedSessionId}`,
        );
        setSelectedSession(detail);
      }
      return updated;
    },
    [selectedSessionId],
  );

  const removeTopic = useCallback(
    async (topicId: string) => {
      await api.delete(`/oneonones/topics/${topicId}`);
      if (selectedSessionId) {
        const detail = await api.get<OneOnOneSessionDetail>(
          `/oneonones/sessions/${selectedSessionId}`,
        );
        setSelectedSession(detail);
      }
    },
    [selectedSessionId],
  );

  const putTranscript = useCallback(
    async (sessionId: string, rawText: string) => {
      const out = await api.put<OneOnOneTranscript>(
        `/oneonones/sessions/${sessionId}/transcript`,
        { raw_text: rawText },
      );
      const detail = await api.get<OneOnOneSessionDetail>(
        `/oneonones/sessions/${sessionId}`,
      );
      setSelectedSession(detail);
      return out;
    },
    [],
  );

  const triggerAnalysis = useCallback(async (sessionId: string) => {
    await api.post(`/oneonones/sessions/${sessionId}/transcript/analyze`);
    // Poll: refresh detail por até ~60s ou enquanto analysis_stale.
    const start = Date.now();
    while (Date.now() - start < 60_000) {
      const detail = await api.get<OneOnOneSessionDetail>(
        `/oneonones/sessions/${sessionId}`,
      );
      setSelectedSession(detail);
      if (detail.transcript && detail.transcript.analyzed_at && !detail.transcript.analysis_stale) {
        return;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
  }, []);

  const toggleActionItem = useCallback(
    async (itemId: string, status: ActionItemStatus) => {
      await api.patch(`/oneonones/action-items/${itemId}`, { status });
      if (selectedSessionId) {
        const detail = await api.get<OneOnOneSessionDetail>(
          `/oneonones/sessions/${selectedSessionId}`,
        );
        setSelectedSession(detail);
      }
    },
    [selectedSessionId],
  );

  const triggerPrepare = useCallback(async (ref: string) => {
    // Cada execução da skill enriquece 1 topic. Iteramos até `topics_remaining == 0`
    // (com cap pra evitar loop infinito em caso de bug).
    const MAX_ITERATIONS = 20;
    for (let i = 0; i < MAX_ITERATIONS; i++) {
      const resp = await api.post<{ ok: boolean; data?: { topics_remaining?: number; topic_id?: string | null }; error?: string }>(
        `/skills/oneonone-prepare/run`,
        {
          params: { ref },
          max_turns: 8,
          timeout_s: 90,
        },
      );
      // Refresh da UI a cada iteração.
      if (selectedSessionId) {
        const detail = await api.get<OneOnOneSessionDetail>(
          `/oneonones/sessions/${selectedSessionId}`,
        );
        setSelectedSession(detail);
      }
      if (!resp.ok) {
        throw new Error(resp.error || 'prepare failed');
      }
      const remaining = resp.data?.topics_remaining ?? 0;
      if (remaining === 0 || resp.data?.topic_id == null) return;
    }
  }, [selectedSessionId]);

  return {
    track,
    sessions,
    selectedSession,
    selectedSessionId,
    loading,
    error,
    refresh,
    selectSession,
    createSession,
    addTopic,
    updateTopic,
    removeTopic,
    putTranscript,
    triggerAnalysis,
    toggleActionItem,
    triggerPrepare,
  };
}
