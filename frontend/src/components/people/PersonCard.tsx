import { forwardRef } from 'react';
import { Github, Slack, Hash } from 'lucide-react';
import InitialsAvatar from './InitialsAvatar';
import RelationshipChip from './RelationshipChip';
import type { Person } from '../../types/person';

interface Props {
  person: Person;
  selected?: boolean;
  onClick: (person: Person) => void;
}

const ICON_SIZE = 13;

const PersonCard = forwardRef<HTMLButtonElement, Props>(function PersonCard(
  { person, selected, onClick },
  ref,
) {
  const externalIds: Array<{ key: string; label: string; icon: JSX.Element }> = [];
  if (person.slack_id) externalIds.push({ key: 'slack', label: 'Slack', icon: <Slack size={ICON_SIZE} /> });
  if (person.jira_account_id) externalIds.push({ key: 'jira', label: 'Jira', icon: <Hash size={ICON_SIZE} /> });
  if (person.github_handle) externalIds.push({ key: 'github', label: 'GitHub', icon: <Github size={ICON_SIZE} /> });

  return (
    <button
      ref={ref}
      type="button"
      onClick={() => onClick(person)}
      aria-pressed={selected}
      className={[
        'group relative flex w-full flex-col gap-3 rounded-lg border bg-neutral-0 p-4 text-left shadow-sm',
        'transition-[transform,box-shadow,border-color] duration-200 ease-out',
        'hover:-translate-y-0.5 hover:shadow-md',
        'active:scale-[0.99] active:duration-100',
        selected
          ? 'border-primary-500 ring-2 ring-primary-100 shadow-md'
          : 'border-neutral-200 hover:border-primary-300',
      ].join(' ')}
    >
      <div className="flex items-start gap-3">
        <InitialsAvatar name={person.name} relationship={person.relationship} size={40} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-semibold text-neutral-800">{person.name}</div>
          {person.role && (
            <div className="truncate text-xs text-neutral-500">{person.role}</div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <RelationshipChip relationship={person.relationship} />
        {externalIds.length > 0 && (
          <div className="flex items-center gap-1.5 text-neutral-400">
            {externalIds.map((id) => (
              <span
                key={id.key}
                title={id.label}
                aria-label={id.label}
                className="transition-colors group-hover:text-neutral-600"
              >
                {id.icon}
              </span>
            ))}
          </div>
        )}
      </div>
    </button>
  );
});

export default PersonCard;
