import React from 'react';

/**
 * FloatingContainer - Reusable wrapper for elevated card-style components
 * Provides consistent floating appearance with soft shadows and rounded corners
 */
const FloatingContainer = ({ 
  children, 
  className = '', 
  padding = 'md',
  borderRadius = 'lg',
  shadow = 'medium',
  style = {}
}) => {
  const paddingMap = {
    xs: 'var(--spacing-xs)',
    sm: 'var(--spacing-sm)',
    md: 'var(--spacing-md)',
    lg: 'var(--spacing-lg)',
    xl: 'var(--spacing-xl)',
  };
  
  const borderRadiusMap = {
    sm: 'var(--radius-sm)',
    md: 'var(--radius-md)',
    lg: 'var(--radius-lg)',
    xl: 'var(--radius-xl)',
  };
  
  const shadowMap = {
    soft: 'var(--shadow-soft)',
    medium: 'var(--shadow-medium)',
    large: 'var(--shadow-large)',
  };
  
  const containerStyle = {
    backgroundColor: 'var(--color-surface)',
    borderRadius: borderRadiusMap[borderRadius] || borderRadiusMap.lg,
    boxShadow: shadowMap[shadow] || shadowMap.medium,
    padding: paddingMap[padding] || paddingMap.md,
    transition: 'var(--transition-normal)',
    ...style,
  };
  
  return (
    <div className={`floating-container ${className}`} style={containerStyle}>
      {children}
    </div>
  );
};

export default FloatingContainer;

