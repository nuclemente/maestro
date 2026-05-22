import { useEffect, useRef, useState } from 'react';
import type { Person, PersonInput, RelationshipType } from '../../types/person';
import { RELATIONSHIPS } from '../../types/person';

interface Props {
  initial?: Partial<Person> | null;
  /** Quando dispara, validação interna já passou e payload normalizado é enviado. */
  onSubmit: (input: PersonInput) => Promise<void> | void;
  /** Recebido pelo drawer para registrar um submitter externo (botão Salvar do header). */
  registerSubmit?: (fn: () => Promise<boolean>) => void;
  /** Avisa o drawer quando o form é "dirty" para o Esc pedir confirmação. */
  onDirtyChange?: (dirty: boolean) => void;
}

const FIELD =
  'h-10 w-full rounded-lg border border-neutral-200 bg-neutral-0 px-3 text-sm text-neutral-800 transition-colors placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100';
const LABEL = 'mb-1.5 block text-xs font-medium uppercase tracking-wide text-neutral-500';

const _EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function empty(): PersonInput {
  return {
    name: '',
    email: '',
    relationship: 'direct_report',
    role: '',
    slack_id: '',
    jira_account_id: '',
    github_handle: '',
    start_date: '',
    notes: '',
  };
}

function fromPerson(p?: Partial<Person> | null): PersonInput {
  if (!p) return empty();
  return {
    name: p.name ?? '',
    email: p.email ?? '',
    relationship: (p.relationship as RelationshipType) ?? 'direct_report',
    role: p.role ?? '',
    slack_id: p.slack_id ?? '',
    jira_account_id: p.jira_account_id ?? '',
    github_handle: p.github_handle ?? '',
    start_date: p.start_date ?? '',
    notes: p.notes ?? '',
  };
}

function nullify(v: string | null | undefined): string | null {
  if (v === null || v === undefined) return null;
  const t = v.trim();
  return t === '' ? null : t;
}

export default function PersonForm({ initial, onSubmit, registerSubmit, onDirtyChange }: Props) {
  const [form, setForm] = useState<PersonInput>(() => fromPerson(initial));
  const [errors, setErrors] = useState<Partial<Record<keyof PersonInput, string>>>({});
  const [shake, setShake] = useState<Set<keyof PersonInput>>(new Set());
  const firstFieldRef = useRef<HTMLInputElement>(null);

  // Re-sincroniza se o `initial` muda (e.g. drawer trocou de pessoa).
  useEffect(() => {
    setForm(fromPerson(initial));
    setErrors({});
    setShake(new Set());
  }, [initial?.id]);

  useEffect(() => {
    firstFieldRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    if (!onDirtyChange) return;
    const baseline = fromPerson(initial);
    const dirty = (Object.keys(baseline) as Array<keyof PersonInput>).some((k) => form[k] !== baseline[k]);
    onDirtyChange(dirty);
  }, [form, initial, onDirtyChange]);

  function set<K extends keyof PersonInput>(key: K, value: PersonInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }));
  }

  function validate(): null | PersonInput {
    const next: Partial<Record<keyof PersonInput, string>> = {};
    if (!form.name.trim()) next.name = 'Obrigatório';
    const emailTrimmed = form.email.trim().toLowerCase();
    if (!emailTrimmed) next.email = 'Obrigatório';
    else if (!_EMAIL_RE.test(emailTrimmed)) next.email = 'E-mail inválido';

    if (Object.keys(next).length > 0) {
      setErrors(next);
      const toShake = new Set(Object.keys(next) as Array<keyof PersonInput>);
      setShake(toShake);
      setTimeout(() => setShake(new Set()), 280);
      return null;
    }

    return {
      name: form.name.trim(),
      email: emailTrimmed,
      relationship: form.relationship,
      role: nullify(form.role),
      slack_id: nullify(form.slack_id),
      jira_account_id: nullify(form.jira_account_id),
      github_handle: nullify(form.github_handle),
      start_date: nullify(form.start_date),
      notes: nullify(form.notes),
    };
  }

  async function submit(): Promise<boolean> {
    const payload = validate();
    if (!payload) return false;
    try {
      await onSubmit(payload);
      return true;
    } catch {
      // erro já tratado pelo caller (toast); mantém form aberto
      return false;
    }
  }

  // Expõe submit ao drawer (que tem o botão Salvar/Cadastrar no header).
  useEffect(() => {
    registerSubmit?.(submit);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form]);

  function fieldClass(key: keyof PersonInput): string {
    const has = !!errors[key];
    const wig = shake.has(key) ? 'maestro-wiggle' : '';
    const tone = has ? 'border-danger-500 focus:border-danger-500 focus:ring-danger-100' : '';
    return `${FIELD} ${tone} ${wig}`.trim();
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
      className="flex flex-col gap-5"
    >
      <div>
        <label className={LABEL} htmlFor="pf-name">Nome</label>
        <input
          id="pf-name"
          ref={firstFieldRef}
          className={fieldClass('name')}
          value={form.name}
          onChange={(e) => set('name', e.target.value)}
          autoComplete="off"
        />
        {errors.name && <p className="mt-1 text-xs text-danger-700">{errors.name}</p>}
      </div>

      <div>
        <label className={LABEL} htmlFor="pf-email">E-mail</label>
        <input
          id="pf-email"
          type="email"
          className={fieldClass('email')}
          value={form.email}
          onChange={(e) => set('email', e.target.value)}
          autoComplete="off"
        />
        {errors.email && <p className="mt-1 text-xs text-danger-700">{errors.email}</p>}
      </div>

      <div>
        <label className={LABEL} htmlFor="pf-relationship">Relação</label>
        <select
          id="pf-relationship"
          className={FIELD}
          value={form.relationship}
          onChange={(e) => set('relationship', e.target.value as RelationshipType)}
        >
          {RELATIONSHIPS.map((r) => (
            <option key={r.value} value={r.value}>{r.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className={LABEL} htmlFor="pf-role">Cargo</label>
        <input
          id="pf-role"
          className={FIELD}
          value={form.role ?? ''}
          onChange={(e) => set('role', e.target.value)}
          placeholder="ex.: Senior SWE, Tech Lead, PM"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className={LABEL} htmlFor="pf-slack">Slack ID</label>
          <input
            id="pf-slack"
            className={FIELD}
            value={form.slack_id ?? ''}
            onChange={(e) => set('slack_id', e.target.value)}
            placeholder="U01ABC..."
          />
        </div>
        <div>
          <label className={LABEL} htmlFor="pf-github">GitHub</label>
          <input
            id="pf-github"
            className={FIELD}
            value={form.github_handle ?? ''}
            onChange={(e) => set('github_handle', e.target.value)}
            placeholder="usuário-gh"
          />
        </div>
        <div>
          <label className={LABEL} htmlFor="pf-jira">Jira account</label>
          <input
            id="pf-jira"
            className={FIELD}
            value={form.jira_account_id ?? ''}
            onChange={(e) => set('jira_account_id', e.target.value)}
            placeholder="557058:..."
          />
        </div>
        <div>
          <label className={LABEL} htmlFor="pf-start">Início no vínculo</label>
          <input
            id="pf-start"
            type="date"
            className={FIELD}
            value={form.start_date ?? ''}
            onChange={(e) => set('start_date', e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className={LABEL} htmlFor="pf-notes">Notas</label>
        <textarea
          id="pf-notes"
          rows={4}
          className="w-full resize-none rounded-lg border border-neutral-200 bg-neutral-0 px-3 py-2.5 text-sm text-neutral-800 transition-colors placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
          value={form.notes ?? ''}
          onChange={(e) => set('notes', e.target.value)}
          placeholder="contexto livre, squad, decisões…"
        />
      </div>

      {/* Submit oculto para que Enter no input dispare submit nativo (sem botão no rodapé). */}
      <button type="submit" className="sr-only" tabIndex={-1}>Salvar</button>
    </form>
  );
}
