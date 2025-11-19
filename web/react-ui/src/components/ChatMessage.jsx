import React from 'react';

/**
 * ChatMessage - Individual message bubble component
 * Outgoing messages: primary light tint
 * Incoming messages: white with soft shadow
 */
const ChatMessage = ({ message, isUser }) => {
  const messageStyle = {
    display: 'flex',
    flexDirection: 'column',
    marginBottom: '4px',
    maxWidth: '85%',
    animation: 'fadeIn 0.3s ease',
    ...(isUser ? {
      marginLeft: 'auto',
      marginRight: 0,
      alignItems: 'flex-end',
    } : {
      marginLeft: 0,
      marginRight: 'auto',
      alignItems: 'flex-start',
    }),
  };
  
  const bubbleStyle = {
    padding: 'var(--spacing-sm) var(--spacing-md)',
    borderRadius: 'var(--radius-lg)',
    wordWrap: 'break-word',
    lineHeight: '1.6',
    width: '100%',
    ...(isUser ? {
      backgroundColor: 'var(--color-primary-light)',
      color: 'var(--color-text-primary)',
      border: '1px solid var(--color-primary)',
      borderColor: 'rgba(74, 108, 247, 0.2)',
    } : {
      backgroundColor: 'var(--color-surface)',
      color: 'var(--color-text-primary)',
      boxShadow: 'var(--shadow-soft)',
      border: '1px solid var(--color-border)',
    }),
  };
  
  const contentStyle = {
    fontSize: '16px',
    lineHeight: '1.4',
    fontWeight: '400',
  };
  
  // Add styles for paragraph elements to ensure they display on new lines
  const paragraphStyles = `
    /* All regular text: same size (16px), normal weight (400) */
    .chat-message {
      font-size: 16px !important;
    }
    .chat-message p {
      display: block !important;
      margin: 2px 0 !important;
      padding: 0 !important;
      font-size: 16px !important;
      font-weight: 400 !important;
      line-height: 1.4 !important;
      clear: both;
    }
    .chat-message p:first-child {
      margin-top: 0 !important;
    }
    .chat-message p:last-child {
      margin-bottom: 0 !important;
    }
    .chat-message li {
      display: list-item !important;
      margin: 2px 0 !important;
      font-size: 16px !important;
      font-weight: 400 !important;
      line-height: 1.4 !important;
    }
    /* Ensure all text elements use the same size */
    .chat-message span,
    .chat-message div:not(.workflow-info) {
      font-size: 16px !important;
    }
    .chat-message ul, .chat-message ol {
      display: block !important;
      margin: 2px 0 !important;
      padding-left: 1.5em !important;
      clear: both;
    }
    /* Remove bold from strong tags in regular text */
    .chat-message p strong,
    .chat-message li strong {
      font-weight: 400 !important;
    }
    /* Headings: bold, slightly larger sizes, always on own line */
    .chat-message h1 {
      display: block !important;
      margin: 0.25em 0 2px 0 !important;
      font-size: 1.3rem !important;
      font-weight: 700 !important;
      line-height: 1.3 !important;
      clear: both !important;
    }
    .chat-message h2 {
      display: block !important;
      margin: 0.25em 0 2px 0 !important;
      font-size: 1.2rem !important;
      font-weight: 600 !important;
      line-height: 1.3 !important;
      clear: both !important;
    }
    .chat-message h3 {
      display: block !important;
      margin: 0.25em 0 2px 0 !important;
      font-size: 1.15rem !important;
      font-weight: 600 !important;
      line-height: 1.3 !important;
      clear: both !important;
    }
    .chat-message h4 {
      display: block !important;
      margin: 0.25em 0 2px 0 !important;
      font-size: 1.1rem !important;
      font-weight: 600 !important;
      line-height: 1.3 !important;
      clear: both !important;
    }
    .chat-message h1:first-child, .chat-message h2:first-child, 
    .chat-message h3:first-child, .chat-message h4:first-child {
      margin-top: 0 !important;
    }
    /* Paragraphs after headings: same size (16px), normal weight (400), minimal spacing */
    .chat-message h1 + p, .chat-message h2 + p, 
    .chat-message h3 + p, .chat-message h4 + p {
      margin-top: 2px !important;
      font-weight: 400 !important;
      font-size: 16px !important;
    }
  `;
  
  // Format markdown-like content with comprehensive markdown support
  const formatContent = (text) => {
    if (!text) return '';
    
    // Split by lines to process line-by-line
    const lines = text.split('\n');
    const formattedLines = [];
    let inList = false;
    let listType = null; // 'ul' or 'ol'
    let lastWasHeader = false;
    let headerLevel = null;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      const nextLine = i < lines.length - 1 ? lines[i + 1].trim() : '';
      const isNextLineList = nextLine.match(/^[-*] /) || nextLine.match(/^\d+\. /);
      
      // Headers - extract only the header text, ensure it's on its own line
      if (line.startsWith('#### ')) {
        if (inList) {
          formattedLines.push(`</${listType}>`);
          inList = false;
        }
        lastWasHeader = true;
        headerLevel = 4;
        // Extract heading text (everything after ####, but handle colons properly)
        const headerText = line.substring(5).trim();
        // If heading ends with colon, remove it (content will be on next line)
        const cleanHeaderText = headerText.endsWith(':') ? headerText.slice(0, -1) : headerText;
        formattedLines.push(`<h4>${cleanHeaderText}</h4>`);
        continue;
      }
      if (line.startsWith('### ')) {
        if (inList) {
          formattedLines.push(`</${listType}>`);
          inList = false;
        }
        lastWasHeader = true;
        headerLevel = 3;
        // Extract heading text (everything after ###, but handle colons properly)
        const headerText = line.substring(4).trim();
        // If heading ends with colon, remove it (content will be on next line)
        const cleanHeaderText = headerText.endsWith(':') ? headerText.slice(0, -1) : headerText;
        formattedLines.push(`<h3>${cleanHeaderText}</h3>`);
        continue;
      }
      if (line.startsWith('## ')) {
        if (inList) {
          formattedLines.push(`</${listType}>`);
          inList = false;
        }
        lastWasHeader = true;
        headerLevel = 2;
        // Extract heading text (everything after ##, but handle colons properly)
        const headerText = line.substring(3).trim();
        // If heading ends with colon, remove it (content will be on next line)
        const cleanHeaderText = headerText.endsWith(':') ? headerText.slice(0, -1) : headerText;
        formattedLines.push(`<h2>${cleanHeaderText}</h2>`);
        continue;
      }
      if (line.startsWith('# ')) {
        if (inList) {
          formattedLines.push(`</${listType}>`);
          inList = false;
        }
        lastWasHeader = true;
        headerLevel = 1;
        const headerText = line.substring(2).trim();
        formattedLines.push(`<h1>${headerText}</h1>`);
        continue;
      }
      
      // Lists - always start on new line (not inline with header)
      if (line.match(/^[-*] /)) {
        if (lastWasHeader) {
          // Close the header properly (lists always start on new line)
          lastWasHeader = false;
        }
        if (!inList || listType !== 'ul') {
          if (inList) {
            formattedLines.push(`</${listType}>`);
          }
          formattedLines.push('<ul>');
          inList = true;
          listType = 'ul';
        }
        const content = line.substring(2);
        formattedLines.push(`<li>${formatInlineMarkdown(content)}</li>`);
        continue;
      }
      
      if (line.match(/^\d+\. /)) {
        if (lastWasHeader) {
          // Close the header properly (lists always start on new line)
          lastWasHeader = false;
        }
        if (!inList || listType !== 'ol') {
          if (inList) {
            formattedLines.push(`</${listType}>`);
          }
          formattedLines.push('<ol>');
          inList = true;
          listType = 'ol';
        }
        const content = line.replace(/^\d+\. /, '');
        formattedLines.push(`<li>${formatInlineMarkdown(content)}</li>`);
        continue;
      }
      
      // Empty line - close list if open
      if (line === '') {
        if (inList) {
          formattedLines.push(`</${listType}>`);
          inList = false;
        }
        lastWasHeader = false;
        formattedLines.push('<br>');
        continue;
      }
      
      // Regular paragraph line
      if (inList) {
        formattedLines.push(`</${listType}>`);
        inList = false;
      }
      
      // Always put paragraphs on a new line (never inline with headers)
      // Reset lastWasHeader to ensure proper spacing
      if (lastWasHeader) {
        lastWasHeader = false;
      }
      
      // Always display paragraphs on new line after headers
      formattedLines.push(`<p>${formatInlineMarkdown(line)}</p>`);
    }
    
    // Close any open list
    if (inList) {
      formattedLines.push(`</${listType}>`);
    }
    
    return formattedLines.join('');
  };
  
  // Format inline markdown (bold, italic, links, code)
  const formatInlineMarkdown = (text) => {
    let formatted = text;
    
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Links
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    return formatted;
  };
  
  // Extract workflow_info from message metadata
  const workflowInfo = message?.metadata?.workflow_info || '';
  
  // Debug logging
  if (!isUser) {
    console.log('ChatMessage - isUser:', isUser);
    console.log('ChatMessage - message:', message);
    console.log('ChatMessage - message.metadata:', message?.metadata);
    console.log('ChatMessage - workflowInfo:', workflowInfo);
  }
  
  return (
    <>
      <style>{paragraphStyles}</style>
      <div className="chat-message" style={messageStyle}>
        <div style={bubbleStyle}>
          <div
            style={contentStyle}
            dangerouslySetInnerHTML={{ __html: formatContent(message) }}
          />
          {!isUser && workflowInfo && (
            <div className="workflow-info" style={{
              marginTop: 'var(--spacing-sm)',
              paddingTop: 'var(--spacing-xs)',
              borderTop: '1px solid var(--color-border)',
              fontSize: '13px',
              color: 'var(--color-text-secondary)',
              fontStyle: 'italic',
              opacity: 0.85,
              letterSpacing: '0.3px',
            }}>
              Workflow: {workflowInfo}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default ChatMessage;

