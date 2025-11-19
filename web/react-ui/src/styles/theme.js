/**
 * Theme configuration for Policy Navigator
 * Modern, minimal, elegant design system
 */

export const theme = {
  colors: {
    // Primary Palette
    primary: '#4A6CF7',
    primaryLight: '#E8EDFF',
    primaryDark: '#324DBF',
    
    // Neutrals
    backgroundLight: '#F7F8FA',
    surface: '#FFFFFF',
    border: '#E5E7EB',
    softShadow: 'rgba(0, 0, 0, 0.06)',
    textPrimary: '#1E1E1E',
    textSecondary: '#6B7280',
    
    // Accents
    accentGreen: '#4ADE80',
    accentPurple: '#A78BFA',
  },
  
  spacing: {
    xs: '8px',
    sm: '12px',
    md: '16px',
    lg: '20px',
    xl: '24px',
    xxl: '32px',
  },
  
  borderRadius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
  },
  
  shadows: {
    soft: '0 2px 8px rgba(0, 0, 0, 0.06)',
    medium: '0 4px 12px rgba(0, 0, 0, 0.08)',
    large: '0 8px 24px rgba(0, 0, 0, 0.1)',
  },
  
  transitions: {
    fast: '150ms ease',
    normal: '250ms ease',
    slow: '350ms ease',
  },
  
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
};

