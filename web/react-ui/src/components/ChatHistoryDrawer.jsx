import React from 'react';
import FloatingContainer from './FloatingContainer';

/**
 * ChatHistoryDrawer - Slide-in drawer for chat history
 * Card-like entries for previous conversations with smooth transitions
 */
const ChatHistoryDrawer = ({ isOpen, onClose, chatHistory, onSelectChat }) => {
  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    zIndex: 200,
    opacity: isOpen ? 1 : 0,
    visibility: isOpen ? 'visible' : 'hidden',
    transition: 'var(--transition-normal)',
    backdropFilter: 'blur(4px)',
  };
  
  const drawerStyle = {
    position: 'fixed',
    top: 0,
    left: isOpen ? 0 : '-400px',
    width: '380px',
    height: '100%',
    backgroundColor: 'var(--color-surface)',
    boxShadow: 'var(--shadow-large)',
    zIndex: 201,
    transition: 'left var(--transition-slow)',
    display: 'flex',
    flexDirection: 'column',
    padding: 'var(--spacing-xl)',
    overflowY: 'auto',
  };
  
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 'var(--spacing-xl)',
    paddingBottom: 'var(--spacing-md)',
    borderBottom: '1px solid var(--color-border)',
  };
  
  const titleStyle = {
    fontSize: '20px',
    fontWeight: 700,
    color: 'var(--color-text-primary)',
    margin: 0,
  };
  
  const closeButtonStyle = {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    border: 'none',
    backgroundColor: 'var(--color-background-light)',
    color: 'var(--color-text-secondary)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    transition: 'var(--transition-fast)',
  };
  
  const historyListStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-md)',
  };
  
  const emptyStateStyle = {
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    padding: 'var(--spacing-xl)',
    fontSize: '14px',
  };
  
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };
  
  return (
    <>
      <div 
        style={overlayStyle}
        onClick={handleOverlayClick}
        aria-hidden={!isOpen}
      />
      <div className="chat-history-drawer" style={drawerStyle}>
        <div style={headerStyle}>
          <h2 style={titleStyle}>Chat History</h2>
          <button
            onClick={onClose}
            style={closeButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = 'var(--color-primary-light)';
              e.target.style.color = 'var(--color-primary)';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'var(--color-background-light)';
              e.target.style.color = 'var(--color-text-secondary)';
            }}
            aria-label="Close drawer"
          >
            ×
          </button>
        </div>
        
        <div style={historyListStyle}>
          {chatHistory.length === 0 ? (
            <div style={emptyStateStyle}>
              <p>No chat history yet.</p>
              <p style={{ marginTop: 'var(--spacing-sm)', fontSize: '13px', opacity: 0.7 }}>
                Start a conversation to see it here.
              </p>
            </div>
          ) : (
            chatHistory.map((chat, idx) => (
              <ChatHistoryCard
                key={idx}
                chat={chat}
                onClick={() => {
                  onSelectChat(chat);
                  onClose();
                }}
              />
            ))
          )}
        </div>
      </div>
    </>
  );
};

/**
 * ChatHistoryCard - Individual chat history entry card
 */
const ChatHistoryCard = ({ chat, onClick }) => {
  const cardStyle = {
    padding: 'var(--spacing-md)',
    borderRadius: 'var(--radius-md)',
    backgroundColor: 'var(--color-background-light)',
    border: '1px solid var(--color-border)',
    cursor: 'pointer',
    transition: 'var(--transition-fast)',
  };
  
  const cardHoverStyle = {
    ...cardStyle,
    backgroundColor: 'var(--color-primary-light)',
    borderColor: 'var(--color-primary)',
    transform: 'translateY(-2px)',
    boxShadow: 'var(--shadow-soft)',
  };
  
  const [isHovered, setIsHovered] = React.useState(false);
  
  const previewStyle = {
    fontSize: '14px',
    color: 'var(--color-text-primary)',
    marginBottom: 'var(--spacing-xs)',
    fontWeight: 500,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  };
  
  const metaStyle = {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };
  
  const getPreview = () => {
    if (chat.messages && chat.messages.length > 0) {
      const firstMessage = chat.messages[0];
      return firstMessage.content.substring(0, 60) + (firstMessage.content.length > 60 ? '...' : '');
    }
    return 'Empty chat';
  };
  
  const getDate = () => {
    if (chat.timestamp) {
      return new Date(chat.timestamp).toLocaleDateString();
    }
    return 'Recently';
  };
  
  return (
    <div
      style={isHovered ? cardHoverStyle : cardStyle}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      <div style={previewStyle}>{getPreview()}</div>
      <div style={metaStyle}>
        <span>{getDate()}</span>
        {chat.messageCount && (
          <span>{chat.messageCount} messages</span>
        )}
      </div>
    </div>
  );
};

export default ChatHistoryDrawer;

