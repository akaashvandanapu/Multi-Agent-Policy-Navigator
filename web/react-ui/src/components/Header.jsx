import React, { useState } from 'react';
import AboutModal from './AboutModal';

/**
 * Header - Sticky header component with Policy Navigator branding
 * Minimal design with primary palette accents and bold typography
 */
const Header = () => {
  const [isAboutOpen, setIsAboutOpen] = useState(false);

  const headerStyle = {
    position: 'sticky',
    top: 0,
    zIndex: 100,
    backgroundColor: 'var(--color-surface)',
    borderBottom: '1px solid var(--color-border)',
    padding: 'var(--spacing-sm) var(--spacing-lg)',
    boxShadow: 'var(--shadow-soft)',
    backdropFilter: 'blur(10px)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };
  
  const brandStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-sm)',
  };
  
  const logoStyle = {
    fontSize: '24px',
    filter: 'drop-shadow(0 2px 4px rgba(74, 108, 247, 0.2))',
  };
  
  const titleStyle = {
    fontSize: '20px',
    fontWeight: 700,
    letterSpacing: '0.3px',
    color: 'var(--color-text-primary)',
    margin: 0,
  };

  const aboutButtonStyle = {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--color-text-primary)',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'var(--transition-fast)',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  };
  
  return (
    <>
      <header style={headerStyle}>
        <div style={brandStyle}>
          <span style={logoStyle}>🌾</span>
          <h1 style={titleStyle}>Policy Navigator</h1>
        </div>
        <button
          style={aboutButtonStyle}
          onClick={() => setIsAboutOpen(true)}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = 'var(--color-primary-light)';
            e.target.style.borderColor = 'var(--color-primary)';
            e.target.style.color = 'var(--color-primary-dark)';
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = 'transparent';
            e.target.style.borderColor = 'var(--color-border)';
            e.target.style.color = 'var(--color-text-primary)';
          }}
        >
          <span>ℹ️</span>
          <span>About</span>
        </button>
      </header>
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </>
  );
};

export default Header;

