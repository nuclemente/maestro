/**
 * Fetch wrapper — usa o proxy `/api` configurado no Vite (vide vite.config.ts).
 * Em produção (sem proxy), `VITE_API_BASE_URL` pode sobrescrever a base.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
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
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get:    <T>(p: string)                  => request<T>(p, { method: 'GET' }),
  post:   <T>(p: string, body?: unknown)  => request<T>(p, { method: 'POST',   body }),
  put:    <T>(p: string, body?: unknown)  => request<T>(p, { method: 'PUT',    body }),
  patch:  <T>(p: string, body?: unknown)  => request<T>(p, { method: 'PATCH',  body }),
  delete: <T>(p: string)                  => request<T>(p, { method: 'DELETE' }),
};
