import { useState, useEffect, useCallback } from 'react';
import { processQuery, checkHealth, uploadDocument } from '../services/api';

/**
 * useChat - Custom hook for managing chat state and interactions
 * Handles messages, loading states, and errors (session-only, no persistence)
 */
export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  
  // Check backend health on mount and periodically
  useEffect(() => {
    const checkBackendHealth = async () => {
      const result = await checkHealth();
      setHealthStatus(result);
    };
    
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  // Initialize with welcome message
  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: 'Welcome! Ask about policies, cultivation, pests, or market pricing.',
      timestamp: new Date().toISOString(),
    }]);
  }, []);
  
  /**
   * Send a message and get response from the backend
   */
  const sendMessage = useCallback(async (content) => {
    if (!content.trim()) return;
    
    // Add user message immediately
    const userMessage = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await processQuery(content.trim());
      
      if (result.success) {
        // Add assistant response
        const assistantMessage = {
          role: 'assistant',
          content: result.response,
          timestamp: new Date().toISOString(),
          metadata: result.metadata,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        setError(result.error || 'Failed to get response');
        
        // Add error message
        const errorMessage = {
          role: 'assistant',
          content: `❌ Error: ${result.error || 'Failed to process your query. Please ensure the API is running on port 5000.'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      const errorMsg = err.message || 'An unexpected error occurred';
      setError(errorMsg);
      
      const errorMessage = {
        role: 'assistant',
        content: `❌ Error: ${errorMsg}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  /**
   * Handle PDF file upload and immediate processing
   */
  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    
    // Add user message showing file upload
    const uploadMessage = {
      role: 'user',
      content: `📎 Uploaded PDF: ${file.name}`,
      timestamp: new Date().toISOString(),
      isFileUpload: true,
      fileName: file.name,
    };
    
    setMessages(prev => [...prev, uploadMessage]);
    setIsLoading(true);
    setError(null);
    
    try {
      // Upload and process PDF immediately
      const result = await uploadDocument(file, '');
      
      if (result.success) {
        // Add assistant response with PDF processing result
        const assistantMessage = {
          role: 'assistant',
          content: result.response,
          timestamp: new Date().toISOString(),
          metadata: result.metadata,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        setError(result.error || 'Failed to process PDF');
        
        // Add error message
        const errorMessage = {
          role: 'assistant',
          content: `❌ ${result.error || 'Failed to process PDF file.'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      const errorMsg = err.message || 'An unexpected error occurred while processing PDF';
      setError(errorMsg);
      
      const errorMessage = {
        role: 'assistant',
        content: `❌ Error: ${errorMsg}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  return {
    messages,
    isLoading,
    error,
    healthStatus,
    sendMessage,
    handleFileUpload,
  };
};

