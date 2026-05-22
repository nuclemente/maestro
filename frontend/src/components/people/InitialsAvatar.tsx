import type { RelationshipType } from '../../types/person';

interface Props {
  name: string;
  relationship?: RelationshipType;
  size?: 40 | 48 | 64;
}

const BG: Record<RelationshipType, string> = {
  direct_report: 'bg-primary-100 text-primary-700',
  peer:          'bg-neutral-200 text-neutral-700',
  manager:       'bg-warning-100 text-warning-700',
  skip_level:    'bg-warning-100 text-warning-800',
  stakeholder:   'bg-info-100 text-info-700',
  other:         'bg-neutral-100 text-neutral-600',
};

const SIZE_CLASSES: Record<40 | 48 | 64, string> = {
  40: 'h-10 w-10 text-xs',
  48: 'h-12 w-12 text-sm',
  64: 'h-16 w-16 text-lg',
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function InitialsAvatar({ name, relationship = 'other', size = 40 }: Props) {
  return (
    <div
      aria-hidden
      className={`flex shrink-0 items-center justify-center rounded-full font-semibold ${SIZE_CLASSES[size]} ${BG[relationship]}`}
    >
      {initials(name)}
    </div>
  );
}
