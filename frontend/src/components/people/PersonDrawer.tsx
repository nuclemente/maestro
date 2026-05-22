import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, MoreHorizontal, Trash2, X } from 'lucide-react';
import Button from '../ui/Button';
import PersonForm from './PersonForm';
import OneOnOneTab from '../oneonone/OneOnOneTab';
import type { Person, PersonInput } from '../../types/person';

type DrawerTab = 'profile' | 'oneonone';

export type DrawerMode = 'edit' | 'create' | 'edit-draft';

interface Props {
  open: boolean;
  mode: DrawerMode;
  person?: Person | null;
  /** Pré-preenche o form em modo `edit-draft` ou outro fluxo iniciado com payload. */
  initialForm?: Partial<Person> | null;
  hasHistory?: boolean;
  onClose: () => void;
  onBack?: () => void;
  onRequestRemove?: () => void;
  onSubmit: (input: PersonInput) => Promise<void>;
}

const TITLE_BY_MODE: Record<DrawerMode, (name?: string) => string> = {
  edit:         (name) => name ?? '',
  create:       () => 'Nova pessoa',
  'edit-draft': () => 'Editar proposta',
};

export default function PersonDrawer({
  open,
  mode,
  person,
  initialForm,
  hasHistory,
  onClose,
  onBack,
  onRequestRemove,
  onSubmit,
}: Props) {
  const [, setAnimating] = useState(false);
  const [closing, setClosing] = useState(false);
  const [paneClass, setPaneClass] = useState('maestro-pane-in');
  const [menuOpen, setMenuOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [tab, setTab] = useState<DrawerTab>('profile');
  const submitFnRef = useRef<(() => Promise<boolean>) | null>(null);
  const previousModeRef = useRef<DrawerMode>(mode);
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open && !closing) {
      const t = setTimeout(() => closeBtnRef.current?.focus(), 60);
      return () => clearTimeout(t);
    }
  }, [open, closing]);

  useEffect(() => {
    if (!open) return;
    if (previousModeRef.current === mode) return;
    setPaneClass('maestro-pane-out');
    const t = setTimeout(() => {
      previousModeRef.current = mode;
      setPaneClass('maestro-pane-in');
    }, 140);
    return () => clearTimeout(t);
  }, [mode, open]);

  // Reset tab quando troca de pessoa/modo.
  useEffect(() => {
    setTab('profile');
  }, [person?.id, mode]);

  const closeWithAnim = useCallback(() => {
    if (closing) return;
    if (dirty) {
      const ok = window.confirm('Descartar alterações não salvas?');
      if (!ok) return;
    }
    setClosing(true);
    setTimeout(() => {
      setClosing(false);
      onClose();
    }, 240);
  }, [closing, dirty, onClose]);

  const handleSubmit = useCallback(async () => {
    if (!submitFnRef.current) return;
    setSubmitting(true);
    try {
      await submitFnRef.current();
    } finally {
      setSubmitting(false);
    }
  }, []);

  // Esc fecha; Cmd/Ctrl+S salva.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeWithAnim();
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        void handleSubmit();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, closeWithAnim, handleSubmit]);

  useEffect(() => {
    if (!menuOpen) return;
    function onClick(e: MouseEvent) {
      if (!drawerRef.current?.contains(e.target as Node)) return;
      const target = e.target as HTMLElement;
      if (!target.closest('[data-menu-anchor]')) setMenuOpen(false);
    }
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [menuOpen]);

  if (!open && !closing) return null;

  const title = TITLE_BY_MODE[mode](person?.name);
  const showBack = hasHistory;
  const submitLabel = mode === 'create' ? 'Cadastrar' : 'Salvar';
  const submittingLabel = mode === 'create' ? 'Cadastrando…' : 'Salvando…';
  const canRemove = mode === 'edit' && Boolean(person) && Boolean(onRequestRemove);
  const canShowOneOnOne = mode === 'edit' && !!person?.id;
  const onProfileTab = tab === 'profile';

  return (
    <>
      <div
        aria-hidden
        onClick={closeWithAnim}
        className={`fixed inset-0 z-40 bg-neutral-900/30 backdrop-blur-sm ${
          closing ? 'maestro-backdrop-out' : 'maestro-backdrop-in'
        }`}
      />
      <aside
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={title || 'Pessoa'}
        className={[
          'fixed right-0 top-0 z-50 flex h-screen w-full flex-col bg-neutral-0 shadow-2xl outline-none',
          'md:w-[640px]',
          closing ? 'maestro-drawer-out' : 'maestro-drawer-in',
        ].join(' ')}
        onAnimationEnd={() => setAnimating(false)}
        onAnimationStart={() => setAnimating(true)}
      >
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-3 border-b border-neutral-100 bg-neutral-0/95 px-4 backdrop-blur">
          <div className="flex min-w-0 items-center gap-2">
            <button
              ref={closeBtnRef}
              type="button"
              onClick={() => {
                if (showBack && onBack) onBack();
                else closeWithAnim();
              }}
              aria-label={showBack ? 'Voltar' : 'Fechar'}
              className="flex h-9 w-9 items-center justify-center rounded-md text-neutral-600 transition hover:bg-neutral-100 active:scale-95"
            >
              {showBack ? <ArrowLeft size={18} /> : <X size={18} />}
            </button>
            <span className="truncate text-sm font-medium text-neutral-700">{title}</span>
          </div>

          <div className="flex items-center gap-2">
            {onProfileTab && (
              <>
                <Button size="sm" variant="secondary" onClick={closeWithAnim} disabled={submitting}>
                  Cancelar
                </Button>
                <Button size="sm" variant="primary" loading={submitting} onClick={handleSubmit}>
                  {submitting ? submittingLabel : submitLabel}
                </Button>
              </>
            )}
            {canRemove && (
              <div className="relative" data-menu-anchor>
                <button
                  type="button"
                  aria-haspopup="menu"
                  aria-label="Mais opções"
                  aria-expanded={menuOpen}
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex h-9 w-9 items-center justify-center rounded-md text-neutral-600 transition hover:bg-neutral-100 active:scale-95"
                >
                  <MoreHorizontal size={18} />
                </button>
                {menuOpen && (
                  <div className="maestro-fade-in absolute right-0 top-11 z-20 w-44 overflow-hidden rounded-lg border border-neutral-200 bg-neutral-0 shadow-lg">
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false);
                        onRequestRemove?.();
                      }}
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-danger-700 transition hover:bg-danger-100/40"
                    >
                      <Trash2 size={14} />
                      Remover
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </header>

        {canShowOneOnOne && (
          <nav
            className="flex shrink-0 gap-1 border-b border-neutral-100 bg-neutral-0 px-6"
            role="tablist"
            aria-label="Seções da pessoa"
          >
            {([
              { id: 'profile' as const, label: 'Perfil' },
              { id: 'oneonone' as const, label: '1:1s' },
            ]).map((t) => {
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setTab(t.id)}
                  className={[
                    'border-b-2 px-3 py-2 text-sm font-medium transition',
                    active
                      ? 'border-primary-600 text-primary-800'
                      : 'border-transparent text-neutral-600 hover:text-neutral-900',
                  ].join(' ')}
                >
                  {t.label}
                </button>
              );
            })}
          </nav>
        )}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div key={`pane-${mode}-${person?.id ?? 'new'}-${tab}`} className={paneClass}>
            {onProfileTab ? (
              <PersonForm
                initial={mode === 'edit' ? person : initialForm}
                onSubmit={onSubmit}
                registerSubmit={(fn) => {
                  submitFnRef.current = fn;
                }}
                onDirtyChange={setDirty}
              />
            ) : person ? (
              <OneOnOneTab person={person} />
            ) : null}
          </div>
        </div>
      </aside>
    </>
  );
}
