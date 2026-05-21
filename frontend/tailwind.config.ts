import type { Config } from 'tailwindcss';
import { colors, radius, shadow, spacing, typography } from './src/theme/tokens';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: colors.primary,
        neutral: colors.neutral,
        success: colors.success,
        warning: colors.warning,
        danger:  colors.danger,
        info:    colors.info,
      },
      fontFamily: typography.fontFamily,
      fontSize: typography.fontSize,
      spacing: spacing as Record<string, string>,
      borderRadius: radius,
      boxShadow: shadow,
    },
  },
  plugins: [],
};

export default config;
