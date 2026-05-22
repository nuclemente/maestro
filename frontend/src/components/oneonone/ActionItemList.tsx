import type { OneOnOneActionItem } from '../../types/oneonone';

interface Props {
  items: OneOnOneActionItem[];
  onToggle: (id: string, next: 'open' | 'done') => Promise<void>;
}

const OWNER_LABEL: Record<OneOnOneActionItem['owner'], string> = {
  em: 'EM',
  person: 'Pessoa',
  other: 'Outro',
};

const OWNER_CLASS: Record<OneOnOneActionItem['owner'], string> = {
  em: 'bg-primary-50 text-primary-800',
  person: 'bg-success-50 text-success-800',
  other: 'bg-neutral-100 text-neutral-700',
};

export default function ActionItemList({ items, onToggle }: Props) {
  if (items.length === 0) {
    return (
      <section className="rounded-lg border border-dashed border-neutral-200 bg-neutral-0 p-4 text-sm text-neutral-500">
        Sem action items registrados.
      </section>
    );
  }
  return (
    <section className="rounded-lg border border-neutral-200 bg-neutral-0 p-4">
      <h3 className="mb-2 text-sm font-semibold text-neutral-900">Action items</h3>
      <ul className="space-y-2">
        {items.map((item) => {
          const done = item.status === 'done';
          return (
            <li key={item.id} className="flex items-start gap-2">
              <input
                type="checkbox"
                checked={done}
                onChange={() => void onToggle(item.id, done ? 'open' : 'done')}
                className="mt-1 h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                aria-label={done ? 'Marcar como aberto' : 'Marcar como feito'}
              />
              <div className="flex-1">
                <p
                  className={`text-sm ${done ? 'text-neutral-400 line-through' : 'text-neutral-800'}`}
                >
                  {item.description}
                </p>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] ${OWNER_CLASS[item.owner]}`}>
                {OWNER_LABEL[item.owner]}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
