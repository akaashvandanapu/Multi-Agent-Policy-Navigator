import React, { useState, useRef, useEffect } from 'react';
import FloatingContainer from './FloatingContainer';

/**
 * ChatInputBar - Modern input component with rounded corners and soft shadow
 * Includes a past/history icon with dropdown for example queries
 */
const ChatInputBar = ({ onSendMessage, isLoading, onFileUpload }) => {
  const [input, setInput] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const exampleQueries = [
    'What is PM-KISAN and how do I apply?',
    'How to grow paddy rice in Andhra Pradesh?',
    'Control measures for fall armyworm in maize',
    'Current MSP for wheat',
  ];
  
  useEffect(() => {
    // Auto-focus input on mount
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('[data-dropdown-container]')) {
        setShowDropdown(false);
      }
    };
    
    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showDropdown]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };
  
  const handleExampleClick = (query) => {
    setInput(query);
    setShowDropdown(false);
    inputRef.current?.focus();
  };
  
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        setSelectedFile(file);
        // Immediately trigger upload
        if (onFileUpload) {
          onFileUpload(file);
        }
      } else {
        alert('Please select a PDF file.');
      }
    }
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };
  
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: 0,
    padding: 'var(--spacing-xs)',
  };
  
  const formStyle = {
    display: 'flex',
    gap: 'var(--spacing-xs)',
    alignItems: 'center',
    position: 'relative',
    width: '100%',
  };
  
  const inputStyle = {
    height: '40px',
    borderRadius: 'var(--radius-md)',
    padding: '0 var(--spacing-sm)',
    border: '1px solid var(--color-border)',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text-primary)',
    fontSize: '14px',
    outline: 'none',
    transition: 'var(--transition-fast)',
    boxShadow: 'var(--shadow-soft)',
    boxSizing: 'border-box',
  };
  
  const inputFocusStyle = {
    borderColor: 'var(--color-primary)',
    boxShadow: '0 0 0 3px rgba(74, 108, 247, 0.1)',
  };
  
  const iconButtonStyle = {
    height: '40px',
    width: '40px',
    borderRadius: '50%',
    border: '1px solid var(--color-border)',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text-secondary)',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'var(--transition-fast)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: 'var(--shadow-soft)',
    flexShrink: 0,
  };
  
  const buttonStyle = {
    height: '40px',
    padding: '0 var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    border: 'none',
    backgroundColor: 'var(--color-primary)',
    color: 'white',
    fontSize: '14px',
    fontWeight: 600,
    cursor: isLoading ? 'not-allowed' : 'pointer',
    transition: 'var(--transition-fast)',
    boxShadow: 'var(--shadow-soft)',
    opacity: isLoading ? 0.6 : 1,
    flexShrink: 0,
  };
  
  const dropdownStyle = {
    backgroundColor: 'var(--color-surface)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-medium)',
    border: '1px solid var(--color-border)',
    minWidth: '280px',
    maxWidth: '400px',
    zIndex: 1000,
    overflow: 'hidden',
    opacity: showDropdown ? 1 : 0,
    visibility: showDropdown ? 'visible' : 'hidden',
    transform: showDropdown ? 'translateY(0)' : 'translateY(8px)',
    transition: 'var(--transition-normal)',
  };
  
  const dropdownItemStyle = {
    padding: 'var(--spacing-sm) var(--spacing-md)',
    cursor: 'pointer',
    fontSize: '14px',
    color: 'var(--color-text-primary)',
    borderBottom: '1px solid var(--color-border)',
    transition: 'var(--transition-fast)',
  };
  
  const dropdownItemHoverStyle = {
    backgroundColor: 'var(--color-primary-light)',
    color: 'var(--color-primary)',
  };
  
  const [inputFocused, setInputFocused] = useState(false);
  const [hoveredItem, setHoveredItem] = useState(null);
  
  return (
    <FloatingContainer padding="xs" borderRadius="lg" shadow="medium">
      <div style={containerStyle}>
        <form 
          className="chat-input-form" 
          onSubmit={handleSubmit} 
          style={formStyle}
        >
          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          
          <div 
            style={{ position: 'relative', flexShrink: 0 }}
            data-dropdown-container
          >
            <button
              type="button"
              style={iconButtonStyle}
              onClick={() => setShowDropdown(!showDropdown)}
              title="Example questions"
            >
              {'<'}
            </button>
            {showDropdown && (
              <div 
                data-dropdown-container
                style={{
                  ...dropdownStyle,
                  position: 'absolute',
                  bottom: '100%',
                  left: 0,
                  marginBottom: 'var(--spacing-xs)',
                }}
              >
                {exampleQueries.map((query, idx) => (
                  <div
                    key={idx}
                    style={{
                      ...dropdownItemStyle,
                      ...(hoveredItem === idx ? dropdownItemHoverStyle : {}),
                      ...(idx === exampleQueries.length - 1 ? { borderBottom: 'none' } : {}),
                    }}
                    onMouseEnter={() => setHoveredItem(idx)}
                    onMouseLeave={() => setHoveredItem(null)}
                    onClick={() => handleExampleClick(query)}
                  >
                    {query}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* PDF Attach Button */}
          <button
            type="button"
            style={iconButtonStyle}
            onClick={handleAttachClick}
            title="Attach PDF document"
            disabled={isLoading}
          >
            📎
          </button>
          
          {selectedFile && (
            <div style={{
              position: 'absolute',
              bottom: '100%',
              left: '50px',
              marginBottom: '4px',
              padding: '4px 8px',
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: 'var(--color-text-secondary)',
              border: '1px solid var(--color-border)',
              whiteSpace: 'nowrap',
              maxWidth: '200px',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {selectedFile.name}
            </div>
          )}
          
          <div style={{ position: 'relative', flex: 1, width: '100%', minWidth: 0 }}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              placeholder="Ask about agricultural policies, cultivation, pests, or markets…"
              disabled={isLoading}
              style={{
                ...inputStyle,
                width: '100%',
                ...(inputFocused ? inputFocusStyle : {}),
              }}
            />
          </div>
          
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            style={buttonStyle}
            onMouseEnter={(e) => {
              if (!isLoading && input.trim()) {
                e.target.style.transform = 'translateY(-1px)';
                e.target.style.boxShadow = 'var(--shadow-medium)';
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'none';
              e.target.style.boxShadow = 'var(--shadow-soft)';
            }}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </FloatingContainer>
  );
};

export default ChatInputBar;

