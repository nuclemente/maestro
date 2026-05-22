import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Home as HomeIcon, Users as UsersIcon } from 'lucide-react';
import { useDraftsCount } from '../../hooks/useDraftsCount';

const PLACEHOLDER_ITEMS = [
  'Agenda',
  '1:1s',
  'Transcrições',
  'Performance',
  'Radar de temas',
  'Plano da semana',
  'To do',
];

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  [
    'flex items-center gap-2 rounded-md px-3 py-2 font-medium transition',
    isActive
      ? 'bg-primary-50 text-primary-600'
      : 'text-neutral-700 hover:bg-neutral-100',
  ].join(' ');

function DraftsBadge() {
  const { count } = useDraftsCount();
  const [pop, setPop] = useState(false);
  const [previous, setPrevious] = useState(count);

  useEffect(() => {
    if (count > previous) {
      setPop(true);
      const t = setTimeout(() => setPop(false), 360);
      return () => clearTimeout(t);
    }
    setPrevious(count);
  }, [count, previous]);

  if (count === 0) return null;

  return (
    <NavLink
      to="/people/drafts"
      title={`${count} proposta${count > 1 ? 's' : ''} pendente${count > 1 ? 's' : ''}`}
      onClick={(e) => e.stopPropagation()}
      className={`ml-auto inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-primary-500 px-1.5 text-[10px] font-bold text-neutral-0 ${pop ? 'maestro-badge-pop' : ''}`}
    >
      {count}
    </NavLink>
  );
}

export default function Sidebar() {
  return (
    <aside
      aria-label="Navegação principal"
      className="flex h-screen w-60 flex-shrink-0 flex-col border-r border-neutral-200 bg-neutral-0"
    >
      <div className="flex h-14 items-center gap-2 border-b border-neutral-200 px-5">
        <span className="text-base font-bold tracking-tight text-primary-500">Maestro</span>
        <span className="ml-auto text-xs text-neutral-400">v0.1.0</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1 text-sm">
          <li>
            <NavLink to="/" end className={NAV_LINK_CLASS}>
              <HomeIcon size={16} />
              Início
            </NavLink>
          </li>
          <li>
            <NavLink to="/people" className={NAV_LINK_CLASS}>
              <UsersIcon size={16} />
              <span>Pessoas</span>
              <DraftsBadge />
            </NavLink>
          </li>
        </ul>

        <div className="mt-6 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
          Features (em breve)
        </div>
        <ul className="space-y-0.5 text-sm">
          {PLACEHOLDER_ITEMS.map((label) => (
            <li key={label}>
              <span
                aria-disabled="true"
                className="block cursor-not-allowed rounded-md px-3 py-2 text-neutral-400"
              >
                {label}
              </span>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
