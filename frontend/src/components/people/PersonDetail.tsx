import RelationshipChip from './RelationshipChip';
import InitialsAvatar from './InitialsAvatar';
import type { Person } from '../../types/person';

interface Props {
  person: Person;
}

interface Section {
  title: string;
  rows: Array<{ label: string; value: string | null | undefined }>;
}

const LABEL_CLASS = 'text-[11px] font-semibold uppercase tracking-wider text-neutral-400';

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1">
      <span className="text-xs text-neutral-500">{label}</span>
      <span className="text-right text-sm text-neutral-800">{value}</span>
    </div>
  );
}

export default function PersonDetail({ person }: Props) {
  const sections: Section[] = [
    {
      title: 'Identidade',
      rows: [
        { label: 'E-mail', value: person.email },
        { label: 'Cargo', value: person.role },
        { label: 'Início', value: person.start_date },
      ],
    },
    {
      title: 'Identificações externas',
      rows: [
        { label: 'Slack', value: person.slack_id },
        { label: 'Jira', value: person.jira_account_id },
        { label: 'GitHub', value: person.github_handle },
      ],
    },
  ];

  return (
    <div className="flex flex-col gap-7">
      <header className="flex items-start gap-4">
        <InitialsAvatar name={person.name} relationship={person.relationship} size={64} />
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-tight text-neutral-800">{person.name}</h2>
          <div className="mt-2">
            <RelationshipChip relationship={person.relationship} size="md" />
          </div>
        </div>
      </header>

      {sections.map((section) => {
        const filled = section.rows.filter((r) => r.value);
        if (filled.length === 0) return null;
        return (
          <section key={section.title}>
            <h3 className={`${LABEL_CLASS} mb-2`}>{section.title}</h3>
            <div className="divide-y divide-neutral-100">
              {filled.map((r) => (
                <Row key={r.label} label={r.label} value={r.value as string} />
              ))}
            </div>
          </section>
        );
      })}

      {person.notes && (
        <section>
          <h3 className={`${LABEL_CLASS} mb-2`}>Notas</h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
            {person.notes}
          </p>
        </section>
      )}
    </div>
  );
}
