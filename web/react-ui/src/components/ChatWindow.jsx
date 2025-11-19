import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInputBar from './ChatInputBar';
import FloatingContainer from './FloatingContainer';

/**
 * ChatWindow - Main chat container with scrollable message area
 * Open and airy design with floating message bubbles
 */
const ChatWindow = ({ 
  messages, 
  isLoading, 
  error, 
  onSendMessage,
  onFileUpload,
}) => {
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  
  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const windowStyle = {
    width: '70%',
    display: 'flex',
    flexDirection: 'column',
    padding: 'var(--spacing-sm)',
    gap: '4px',
    overflow: 'hidden',
  };
  
  const messagesAreaStyle = {
    flex: 1,
    overflowY: 'auto',
    overflowX: 'hidden',
    padding: 'var(--spacing-xs)',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  };
  
  const loadingStyle = {
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    padding: 'var(--spacing-md)',
    fontSize: '14px',
    fontStyle: 'italic',
  };
  
  const errorStyle = {
    textAlign: 'center',
    color: '#ef4444',
    padding: 'var(--spacing-md)',
    fontSize: '14px',
    backgroundColor: '#fef2f2',
    borderRadius: 'var(--radius-md)',
    border: '1px solid #fecaca',
  };
  
  return (
    <div className="chat-window" style={windowStyle}>
      <FloatingContainer 
        padding="sm" 
        borderRadius="lg" 
        shadow="medium"
        style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}
      >
        <div ref={messagesContainerRef} style={messagesAreaStyle}>
          {messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              message={msg.content}
              isUser={msg.role === 'user'}
            />
          ))}
          
          {isLoading && (
            <div style={loadingStyle}>
              Processing your query through multi‑agent pipeline…
            </div>
          )}
          
          {error && (
            <div style={errorStyle}>
              ❌ {error}
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </FloatingContainer>
      
      <ChatInputBar 
        onSendMessage={onSendMessage} 
        isLoading={isLoading}
        onFileUpload={onFileUpload}
      />
    </div>
  );
};

export default ChatWindow;

