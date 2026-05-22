import PersonCard from './PersonCard';
import SkeletonCard from './SkeletonCard';
import type { Person } from '../../types/person';

interface Props {
  people: Person[];
  selectedId?: string | null;
  loading?: boolean;
  onSelect: (person: Person) => void;
}

const SKELETON_COUNT = 8;

export default function PersonGrid({ people, selectedId, loading, onSelect }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: SKELETON_COUNT }, (_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="maestro-fade-in grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {people.map((p) => (
        <PersonCard
          key={p.id}
          person={p}
          selected={p.id === selectedId}
          onClick={onSelect}
        />
      ))}
    </div>
  );
}
