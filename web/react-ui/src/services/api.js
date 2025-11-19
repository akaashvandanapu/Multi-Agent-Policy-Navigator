/**
 * API service layer for Policy Navigator
 * Connects React app to Flask backend endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Check backend health status
 */
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Failed to connect to backend',
    };
  }
};

/**
 * Process a user query through the agent pipeline
 */
export const processQuery = async (query) => {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Query processing failed');
    }
    
    // Extract response text from result - always use response_markdown
    let responseText = '';
    if (data.result) {
      if (data.result.response_markdown) {
        responseText = data.result.response_markdown;
      } else if (data.result.response_text) {
        responseText = data.result.response_text;
      } else if (typeof data.result === 'string') {
        responseText = data.result;
      } else {
        responseText = JSON.stringify(data.result, null, 2);
      }
    }
    
    // Extract workflow_info and workflow_details from metadata
    const workflowInfo = data.result?.workflow_info || '';
    const workflowDetails = data.result?.workflow_details || {};
    
    // Debug logging
    if (workflowInfo) {
      console.log('✅ Workflow info found in API response:', workflowInfo);
    } else {
      console.warn('⚠️ Workflow info not found in API response. Result keys:', Object.keys(data.result || {}));
    }
    
    if (workflowDetails && Object.keys(workflowDetails).length > 0) {
      console.log('✅ Workflow details found in API response:', workflowDetails);
    } else {
      console.warn('⚠️ Workflow details not found in API response.');
    }
    
    return {
      success: true,
      response: responseText,
      metadata: {
        ...data.result,
        workflow_info: workflowInfo,
        workflow_details: workflowDetails,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Failed to process query',
    };
  }
};

/**
 * Upload a document for verification
 */
export const uploadDocument = async (file, query = '') => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (query) {
      formData.append('query', query);
    }
    
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'Document upload failed');
    }
    
    let responseText = '';
    if (data.result) {
      if (data.result.response_markdown) {
        responseText = data.result.response_markdown;
      } else if (data.result.response_text) {
        responseText = data.result.response_text;
      } else if (typeof data.result === 'string') {
        responseText = data.result;
      } else {
        responseText = JSON.stringify(data.result, null, 2);
      }
    }
    
    // Extract workflow_info and workflow_details from metadata
    const workflowInfo = data.result?.workflow_info || '';
    const workflowDetails = data.result?.workflow_details || {};
    
    return {
      success: true,
      response: responseText,
      metadata: {
        ...data.result,
        workflow_info: workflowInfo,
        workflow_details: workflowDetails,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Failed to upload document',
    };
  }
};

/**
 * Get information about available agents
 */
export const getAgentsInfo = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/agents`);
    if (!response.ok) {
      throw new Error('Failed to fetch agents info');
    }
    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Failed to fetch agents info',
    };
  }
};

