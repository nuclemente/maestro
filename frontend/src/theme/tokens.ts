/**
 * Tokens de design — inspirados em `nubank/nuds-web-core`.
 *
 * Estes valores são uma replicação inicial baseada na paleta pública da Nubank.
 * A pipeline definitiva (extrair tokens via `gh api` do repo `nuds-web-core`)
 * está documentada em ARCHITECTURE.md. Atualize este arquivo regenerando-o
 * a partir do repo oficial antes de cada release.
 */

export const colors = {
  // Brand — paleta `mauve` (tema "pj" / Nu Empresas do nuds-web-core).
  // Mapeamento NuDS → Tailwind:
  //   mauve-10..90 (light theme) → primary-50..900.
  primary: {
    50:  '#F5EEF9', // mauve-10
    100: '#EADBF1', // mauve-20
    200: '#C3B2CA', // mauve-30
    300: '#A087AE', // mauve-40
    400: '#886A9E', // mauve-50
    500: '#714F8F', // mauve-60  ← brand primary (surface-accent-primary)
    600: '#652590', // mauve-70  (content/border-accent-primary)
    700: '#490C74', // mauve-80
    800: '#320851', // mauve-90
    900: '#1F0432', // extrapolação mais escura para fundos enfáticos
  },
  // Neutrals (UI surfaces & text)
  neutral: {
    0:   '#FFFFFF',
    50:  '#F7F7FA',
    100: '#EFEFF3',
    200: '#DCDCE3',
    300: '#B9B9C4',
    400: '#9494A1',
    500: '#6F6F7E',
    600: '#50505C',
    700: '#36363F',
    800: '#22222A',
    900: '#111116',
  },
  // Semantic
  success: { 100: '#DFF5E5', 500: '#1F9D55', 700: '#137042' },
  warning: { 100: '#FFF1D6', 500: '#D98B0A', 700: '#9A5F03' },
  danger:  { 100: '#FCE0E0', 500: '#D7263D', 700: '#A11529' },
  info:    { 100: '#DCEBFF', 500: '#1F6FEB', 700: '#0B4FB1' },
} as const;

export const typography = {
  fontFamily: {
    sans: ['"Nu Sans"', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
    mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
  },
  fontSize: {
    xs:   ['0.75rem',  { lineHeight: '1rem' }],
    sm:   ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem',     { lineHeight: '1.5rem' }],
    lg:   ['1.125rem', { lineHeight: '1.75rem' }],
    xl:   ['1.25rem',  { lineHeight: '1.75rem' }],
    '2xl':['1.5rem',   { lineHeight: '2rem' }],
    '3xl':['1.875rem', { lineHeight: '2.25rem' }],
    '4xl':['2.25rem',  { lineHeight: '2.5rem' }],
  },
} as const;

export const spacing = {
  px:   '1px',
  0:    '0',
  1:    '0.25rem',
  2:    '0.5rem',
  3:    '0.75rem',
  4:    '1rem',
  5:    '1.25rem',
  6:    '1.5rem',
  8:    '2rem',
  10:   '2.5rem',
  12:   '3rem',
  16:   '4rem',
  20:   '5rem',
  24:   '6rem',
} as const;

export const radius = {
  none: '0',
  sm:   '0.25rem',
  md:   '0.5rem',
  lg:   '0.75rem',
  xl:   '1rem',
  '2xl':'1.5rem',
  full: '9999px',
} as const;

export const shadow = {
  sm: '0 1px 2px 0 rgba(17, 17, 22, 0.05)',
  md: '0 4px 12px -2px rgba(17, 17, 22, 0.08), 0 2px 4px -2px rgba(17, 17, 22, 0.04)',
  lg: '0 10px 30px -10px rgba(17, 17, 22, 0.15)',
} as const;

export const tokens = { colors, typography, spacing, radius, shadow };
