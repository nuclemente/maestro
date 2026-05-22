/**
 * Fetch wrapper — usa o proxy `/api` configurado no Vite (vide vite.config.ts).
 * Em produção (sem proxy), `VITE_API_BASE_URL` pode sobrescrever a base.
 *
 * GETs retentam com backoff em erros de rede e 5xx (1s/2s/4s). Mutações
 * falham imediatamente. Erros 4xx **não** disparam retry (esperados pela
 * lógica de negócio).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const RETRY_DELAYS_MS = [1000, 2000, 4000];

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

function shouldRetry(err: unknown, status?: number): boolean {
  if (status !== undefined) return status >= 500;
  // Erro de rede (fetch jogou TypeError, AbortError, etc.).
  return err instanceof TypeError;
}

async function rawRequest<T>(path: string, options: RequestOptions): Promise<T> {
  const { body, headers, ...rest } = options;
  const init: RequestInit = {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers ?? {}),
    },
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, init);

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      /* corpo não-JSON */
    }
    const err = new Error(detail) as Error & { status: number };
    err.status = response.status;
    throw err;
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function requestWithRetry<T>(path: string, options: RequestOptions): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt <= RETRY_DELAYS_MS.length; attempt++) {
    try {
      return await rawRequest<T>(path, options);
    } catch (err) {
      lastErr = err;
      const status = (err as { status?: number }).status;
      if (attempt === RETRY_DELAYS_MS.length || !shouldRetry(err, status)) {
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAYS_MS[attempt]));
    }
  }
  throw lastErr;
}

export const api = {
  get:    <T>(p: string)                  => requestWithRetry<T>(p, { method: 'GET' }),
  post:   <T>(p: string, body?: unknown)  => rawRequest<T>(p, { method: 'POST',   body }),
  put:    <T>(p: string, body?: unknown)  => rawRequest<T>(p, { method: 'PUT',    body }),
  patch:  <T>(p: string, body?: unknown)  => rawRequest<T>(p, { method: 'PATCH',  body }),
  delete: <T>(p: string)                  => rawRequest<T>(p, { method: 'DELETE' }),
};
