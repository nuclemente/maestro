import type { RelationshipType } from '../../types/person';
import { RELATIONSHIP_LABEL } from '../../types/person';

interface Props {
  relationship: RelationshipType;
  size?: 'sm' | 'md';
}

const STYLES: Record<RelationshipType, string> = {
  direct_report: 'bg-primary-50 text-primary-700',
  peer:          'bg-neutral-100 text-neutral-700',
  manager:       'bg-warning-100 text-warning-700',
  skip_level:    'bg-warning-100 text-warning-700 ring-1 ring-warning-500/30',
  stakeholder:   'bg-info-100 text-info-700',
  other:         'bg-neutral-50 text-neutral-600',
};

const SIZES = {
  sm: 'h-5 px-2 text-[10px]',
  md: 'h-6 px-2.5 text-xs',
} as const;

export default function RelationshipChip({ relationship, size = 'sm' }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium uppercase tracking-wide ${SIZES[size]} ${STYLES[relationship]}`}
    >
      {RELATIONSHIP_LABEL[relationship]}
    </span>
  );
}
