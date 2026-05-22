import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../App';

describe('Home page', () => {
  it('renders the Maestro title and main CTAs', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /maestro/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /testar backend/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sobre/i })).toBeInTheDocument();
  });

  it('opens the About modal when clicking "Sobre"', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /sobre/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/sobre o maestro/i)).toBeInTheDocument();
  });

  it('renders the fixed sidebar with Início link and feature placeholders', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    const sidebar = screen.getByRole('complementary', { name: /navegação principal/i });
    expect(sidebar).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /início/i })).toBeInTheDocument();
    expect(screen.getByText(/features \(em breve\)/i)).toBeInTheDocument();
  });

  it('calls the API and shows JSON on successful health ping', async () => {
    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/health')) {
        return new Response(
          JSON.stringify({
            status: 'ok',
            service: 'maestro-backend',
            env: 'test',
            timestamp: '2026-05-21T00:00:00Z',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }
      // Outras chamadas (drafts pelo sidebar etc.) — devolvem array vazio.
      return new Response('[]', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });

    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: /testar backend/i }));
    expect(await screen.findByText(/"maestro-backend"/)).toBeInTheDocument();
    fetchSpy.mockRestore();
  });
});
