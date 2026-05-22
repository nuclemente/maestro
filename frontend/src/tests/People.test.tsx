import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

function mockJson(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

const ALICE = {
  id: 'p1',
  name: 'Alice Lima',
  email: 'alice@example.com',
  relationship: 'direct_report',
  role: 'Senior SWE',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('People page', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the page header and cards from the API', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/people/drafts')) return mockJson([]);
      if (url.includes('/people')) return mockJson([ALICE]);
      return mockJson({}, 404);
    });

    render(
      <MemoryRouter initialEntries={['/people']}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole('heading', { level: 1, name: /pessoas/i }),
    ).toBeInTheDocument();
    expect(await screen.findByText('Alice Lima')).toBeInTheDocument();
    expect(screen.getByText('Senior SWE')).toBeInTheDocument();
  });

  it('opens the drawer on card click and shows the detail', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/people/drafts')) return mockJson([]);
      if (url.includes('/people')) return mockJson([ALICE]);
      return mockJson({}, 404);
    });

    render(
      <MemoryRouter initialEntries={['/people']}>
        <App />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText('Alice Lima'));
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /editar/i })).toBeInTheDocument();
  });

  it('shows empty state when there are no people', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async () => mockJson([]));

    render(
      <MemoryRouter initialEntries={['/people']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/nenhuma pessoa cadastrada ainda/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /adicionar primeira pessoa/i })).toBeInTheDocument();
  });

  it('shows the badge in the sidebar when there are drafts', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/people/drafts')) {
        return mockJson([
          {
            id: 'd1',
            name: 'Bob',
            email: 'bob@example.com',
            relationship: 'peer',
            source: 'agent:people',
            proposed_at: '2026-05-01T00:00:00Z',
          },
        ]);
      }
      return mockJson([]);
    });

    render(
      <MemoryRouter initialEntries={['/people']}>
        <App />
      </MemoryRouter>,
    );

    // Badge da sidebar exibe contagem.
    await waitFor(() => {
      const badges = screen.getAllByText('1');
      expect(badges.length).toBeGreaterThan(0);
    });
    // CTA destacando propostas pendentes na página.
    expect(await screen.findByText(/propostas pendentes/i)).toBeInTheDocument();
  });
});
