import { Users } from 'lucide-react';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export default function EmptyState({ title, description, action, icon }: Props) {
  return (
    <div className="maestro-fade-in flex flex-col items-center justify-center rounded-2xl border border-dashed border-neutral-200 bg-neutral-0 px-6 py-16 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary-50 text-primary-500">
        {icon ?? <Users size={26} strokeWidth={1.5} />}
      </div>
      <h3 className="text-base font-semibold text-neutral-800">{title}</h3>
      {description && (
        <p className="mt-1 max-w-md text-sm text-neutral-500">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
