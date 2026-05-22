import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Plus, Search, X } from 'lucide-react';
import Button from '../components/ui/Button';
import Modal from '../components/ui/Modal';
import EmptyState from '../components/people/EmptyState';
import PersonDrawer from '../components/people/PersonDrawer';
import type { DrawerMode } from '../components/people/PersonDrawer';
import PersonGrid from '../components/people/PersonGrid';
import { usePeople } from '../hooks/usePeople';
import { useUndoableDelete } from '../hooks/useUndoableDelete';
import { notifyDraftsChanged } from '../hooks/useDraftsCount';
import { RELATIONSHIPS } from '../types/person';
import type { Person, PersonInput, RelationshipType } from '../types/person';

type DrawerState =
  | { mode: 'closed' }
  | { mode: 'edit'; person: Person }
  | { mode: 'create' };

export default function People() {
  const [filter, setFilter] = useState<RelationshipType | null>(null);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [drawer, setDrawer] = useState<DrawerState>({ mode: 'closed' });
  const [removeTarget, setRemoveTarget] = useState<Person | null>(null);
  const [removing, setRemoving] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const opts = useMemo(() => ({ relationship: filter, query: debouncedQuery }), [filter, debouncedQuery]);
  const { people, drafts, loading, create, update, remove, recreate } = usePeople(opts);
  const undoableDelete = useUndoableDelete({ remove, recreate });

  // Debounce da busca.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  // Atalhos globais (não interferem em inputs).
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const el = document.activeElement as HTMLElement | null;
      const inField = el && (
        el.tagName === 'INPUT' ||
        el.tagName === 'TEXTAREA' ||
        el.tagName === 'SELECT' ||
        el.isContentEditable
      );
      if (e.key === '/' && !inField) {
        e.preventDefault();
        searchRef.current?.focus();
      } else if (e.key.toLowerCase() === 'n' && !inField && drawer.mode === 'closed') {
        e.preventDefault();
        setDrawer({ mode: 'create' });
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawer.mode]);

  const selectedId = drawer.mode === 'edit' ? drawer.person.id : null;

  function openCreate() {
    setDrawer({ mode: 'create' });
  }

  function openEdit(person: Person) {
    setDrawer({ mode: 'edit', person });
  }

  async function handleSubmit(input: PersonInput) {
    try {
      if (drawer.mode === 'create') {
        const created = await create(input);
        toast.success(`${created.name} cadastrada`);
        notifyDraftsChanged();
        setDrawer({ mode: 'edit', person: created });
      } else if (drawer.mode === 'edit') {
        const updated = await update(drawer.person.id, input);
        toast.success('Cadastro atualizado');
        setDrawer({ mode: 'edit', person: updated });
      }
    } catch (err) {
      toast.error((err as Error).message);
      throw err;
    }
  }

  function requestRemove() {
    if (drawer.mode === 'edit') setRemoveTarget(drawer.person);
  }

  async function confirmRemove() {
    if (!removeTarget) return;
    setRemoving(true);
    try {
      await undoableDelete(removeTarget);
      setRemoveTarget(null);
      setDrawer({ mode: 'closed' });
      notifyDraftsChanged();
    } finally {
      setRemoving(false);
    }
  }

  const hasDrawer = drawer.mode !== 'closed';
  const visiblePeopleCount = people.length;
  const filterIsActive = filter !== null || debouncedQuery.trim() !== '';

  return (
    <section className="mx-auto flex max-w-7xl flex-col px-8 pb-20 pt-10">
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-800">Pessoas</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Liderados, pares, chefes e demais pessoas-chave do EM.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {drafts.length > 0 && (
            <Link
              to="/people/drafts"
              className="inline-flex h-10 items-center gap-2 rounded-lg border border-warning-500/30 bg-warning-100/60 px-3 text-sm font-medium text-warning-700 transition hover:bg-warning-100"
            >
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-warning-500 text-[10px] font-bold text-neutral-0">
                {drafts.length}
              </span>
              Propostas pendentes
            </Link>
          )}
          <Button onClick={openCreate}>
            <Plus size={16} />
            Adicionar
          </Button>
        </div>
      </header>

      <div className="mb-6 flex flex-col gap-3">
        <div className="relative max-w-xl">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            ref={searchRef}
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar por nome ou e-mail…"
            className="h-11 w-full rounded-xl border border-neutral-200 bg-neutral-0 pl-9 pr-10 text-sm text-neutral-800 transition-colors placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              aria-label="Limpar busca"
              className="absolute right-2.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-neutral-400 transition hover:bg-neutral-100 hover:text-neutral-600"
            >
              <X size={14} />
            </button>
          )}
        </div>

        <div className="-mx-1 flex items-center gap-1.5 overflow-x-auto px-1 pb-1">
          <FilterChip active={filter === null} onClick={() => setFilter(null)}>Todas</FilterChip>
          {RELATIONSHIPS.map((r) => (
            <FilterChip
              key={r.value}
              active={filter === r.value}
              onClick={() => setFilter(r.value)}
            >
              {r.short}
            </FilterChip>
          ))}
        </div>
      </div>

      {!loading && visiblePeopleCount === 0 ? (
        filterIsActive ? (
          <EmptyState
            title="Nada encontrado"
            description={
              debouncedQuery
                ? `Nenhuma pessoa corresponde a "${debouncedQuery}". Tente outro termo ou use :discover-person no Slack.`
                : 'Nenhuma pessoa nesta relação. Limpe o filtro para ver todas.'
            }
            action={
              <Button variant="secondary" onClick={() => { setFilter(null); setQuery(''); }}>
                Limpar filtros
              </Button>
            }
          />
        ) : (
          <EmptyState
            title="Nenhuma pessoa cadastrada ainda"
            description="Comece adicionando seus liderados diretos. Você também pode usar :discover-person no Slack para o agente enriquecer um cadastro automaticamente."
            action={<Button onClick={openCreate}><Plus size={16} />Adicionar primeira pessoa</Button>}
          />
        )
      ) : (
        <PersonGrid
          people={people}
          selectedId={selectedId}
          loading={loading}
          onSelect={openEdit}
        />
      )}

      <PersonDrawer
        open={hasDrawer}
        mode={drawer.mode === 'closed' ? 'edit' : (drawer.mode as DrawerMode)}
        person={drawer.mode === 'edit' ? drawer.person : null}
        onClose={() => setDrawer({ mode: 'closed' })}
        onRequestRemove={requestRemove}
        onSubmit={handleSubmit}
      />

      <Modal
        open={removeTarget !== null}
        onClose={() => !removing && setRemoveTarget(null)}
        title={removeTarget ? `Remover ${removeTarget.name}?` : 'Remover pessoa?'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setRemoveTarget(null)} disabled={removing}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={confirmRemove} loading={removing}>
              {removing ? 'Removendo…' : 'Remover'}
            </Button>
          </div>
        }
      >
        <p className="text-sm text-neutral-600">
          A pessoa será apagada do cadastro. Você terá ~5 segundos para desfazer.
        </p>
      </Modal>
    </section>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        'h-8 shrink-0 rounded-full px-3 text-xs font-medium transition-colors duration-150',
        active
          ? 'bg-primary-500 text-neutral-0 shadow-sm'
          : 'bg-neutral-50 text-neutral-700 hover:bg-neutral-100',
      ].join(' ')}
    >
      {children}
    </button>
  );
}
