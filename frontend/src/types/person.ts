export type RelationshipType =
  | 'direct_report'
  | 'peer'
  | 'manager'
  | 'skip_level'
  | 'stakeholder'
  | 'other';

export interface RelationshipMeta {
  value: RelationshipType;
  label: string;
  short: string;
}

export const RELATIONSHIPS: readonly RelationshipMeta[] = [
  { value: 'direct_report', label: 'Liderado direto', short: 'Liderados' },
  { value: 'peer',          label: 'Par',             short: 'Pares' },
  { value: 'manager',       label: 'Chefe',           short: 'Chefes' },
  { value: 'skip_level',    label: 'Skip-level',      short: 'Skip' },
  { value: 'stakeholder',   label: 'Stakeholder',     short: 'Stakeholders' },
  { value: 'other',         label: 'Outro',           short: 'Outros' },
] as const;

export const RELATIONSHIP_LABEL: Record<RelationshipType, string> = Object.fromEntries(
  RELATIONSHIPS.map((r) => [r.value, r.label]),
) as Record<RelationshipType, string>;

export interface Person {
  id: string;
  name: string;
  email: string;
  relationship: RelationshipType;
  role?: string | null;
  slack_id?: string | null;
  jira_account_id?: string | null;
  github_handle?: string | null;
  start_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonDraft {
  id: string;
  name: string;
  email: string;
  relationship: RelationshipType;
  role?: string | null;
  slack_id?: string | null;
  jira_account_id?: string | null;
  github_handle?: string | null;
  start_date?: string | null;
  notes?: string | null;
  source: string;
  proposed_at: string;
}

export type PersonInput = Omit<Person, 'id' | 'created_at' | 'updated_at'>;
export type PersonUpdate = Partial<PersonInput>;
