import React from 'react';
import Header from './Header';
import ChatWindow from './ChatWindow';
import RightPanel from './RightPanel';
import { useChat } from '../hooks/useChat';

/**
 * PolicyNavigator - Main app wrapper component
 * Orchestrates the entire application layout and state
 */
const PolicyNavigator = () => {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    handleFileUpload,
  } = useChat();
  
  // Get workflow details from the latest assistant message
  const getLatestWorkflowDetails = () => {
    // Find the last assistant message
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant' && messages[i].metadata?.workflow_details) {
        return messages[i].metadata.workflow_details;
      }
    }
    return null;
  };
  
  const workflowDetails = getLatestWorkflowDetails();
  
  const appStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    width: '100%',
    backgroundColor: 'var(--color-background-light)',
  };
  
  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    position: 'relative',
    overflow: 'hidden',
    gap: '4px',
  };
  
  return (
    <div style={appStyle}>
      <Header />
      <div style={mainContentStyle}>
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSendMessage={sendMessage}
          onFileUpload={handleFileUpload}
        />
        <RightPanel workflowDetails={workflowDetails} />
      </div>
    </div>
  );
};

export default PolicyNavigator;

