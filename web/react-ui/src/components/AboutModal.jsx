import React, { useState, useEffect } from 'react';

/**
 * AboutModal - Comprehensive information about the Policy Navigator system
 * Shows agents, tools, workflow, and requirements compliance
 */
const AboutModal = ({ isOpen, onClose }) => {
  const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!isOpen) return null;

  // Hardcoded agent information
  const agents = [
    {
      id: 'query_analyzer',
      name: 'Query Understanding Specialist',
      framework: 'CrewAI',
      description: 'Analyzes user queries to understand intent, extract entities, and determine which agents should handle the request. Expert in natural language understanding with deep knowledge of agricultural terminology.',
      tool: 'Region Detector'
    },
    {
      id: 'policy_researcher',
      name: 'Agricultural Policy Expert',
      framework: 'CrewAI',
      description: 'Retrieves and explains agricultural schemes, policies, subsidies, and benefits from government documents. Comprehensive knowledge of PM-KISAN, PMFBY, crop insurance, and rural development programs.',
      tool: 'RAG Document Search'
    },
    {
      id: 'crop_specialist',
      name: 'Crop Cultivation Expert',
      framework: 'CrewAI',
      description: 'Provides comprehensive crop cultivation guidance including varieties, sowing, fertilization, irrigation, and best practices. Agronomist with extensive experience across different regions of India.',
      tool: 'RAG Document Search'
    },
    {
      id: 'pest_advisor',
      name: 'Pest Control Advisor',
      framework: 'CrewAI',
      description: 'Identifies pests and diseases, provides IPM strategies and control measures. Entomologist and plant pathologist with expertise in Integrated Pest Management (IPM).',
      tool: 'RAG Document Search'
    },
    {
      id: 'market_analyst',
      name: 'Market & Weather Analyst',
      framework: 'CrewAI',
      description: 'Provides current MSP, market prices, weather conditions, and agricultural announcements. Market analyst specializing in agricultural commodities with real-time information.',
      tool: 'Ollama Web Search MCP'
    },
    {
      id: 'non_ap_researcher',
      name: 'Non-AP Region Web Research Specialist',
      framework: 'CrewAI',
      description: 'Searches the web for agricultural information about non-AP regions. Specialized web research agent focused on finding current information for regions outside Andhra Pradesh.',
      tool: 'Ollama Web Search MCP'
    },
    {
      id: 'pdf_processor_agent',
      name: 'PDF Document Processor',
      framework: 'CrewAI',
      description: 'Extracts, analyzes, and answers questions about PDF documents. Uses PDF MCP tool to extract text, generate summaries, and provide comprehensive document analysis.',
      tool: 'PDF Processor (MCP)'
    },
    {
      id: 'calculator_agent',
      name: 'Agricultural Calculator',
      framework: 'ADK',
      description: 'Performs agricultural calculations including costs, yields, subsidies, and profits. ADK agent using Google Generative AI for accurate financial calculations.',
      tool: 'Calculator (ADK)'
    },
    {
      id: 'response_synthesizer',
      name: 'Response Synthesizer',
      framework: 'CrewAI',
      description: 'Synthesizes comprehensive, well-structured responses from multiple agent outputs. Expert technical writer specializing in agricultural information.',
      tool: 'None'
    }
  ];

  // Hardcoded tools information
  const tools = [
    {
      name: 'Region Detector',
      type: 'Normal',
      framework: 'CrewAI',
      description: 'Detects if queries mention Andhra Pradesh or other regions. Analyzes query text to identify AP districts, cities, and states.',
      usedBy: ['Query Understanding Specialist']
    },
    {
      name: 'RAG Document Search',
      type: 'Normal',
      framework: 'CrewAI',
      description: 'Searches agricultural policy and crop information documents using ChromaDB vector store. Provides semantic search through vectorized documents.',
      usedBy: ['Policy Expert', 'Crop Specialist', 'Pest Advisor']
    },
    {
      name: 'Ollama Web Search MCP',
      type: 'MCP',
      framework: 'CrewAI',
      description: 'External MCP server for real-time web search. Provides current market prices, MSP, weather information, and agricultural data from the web.',
      usedBy: ['Market Analyst', 'Non-AP Researcher']
    },
    {
      name: 'PDF Processor (MCP)',
      type: 'MCP',
      framework: 'CrewAI',
      description: 'MCP-compatible PDF reading tool. Extracts text content from PDF documents with page-by-page breakdown and comprehensive analysis.',
      usedBy: ['PDF Document Processor']
    },
    {
      name: 'Calculator (ADK)',
      type: 'ADK',
      framework: 'ADK',
      description: 'Agricultural calculator using Google ADK. Performs cost estimation, yield calculation, subsidy calculation, and profit analysis.',
      usedBy: ['Agricultural Calculator']
    }
  ];

  // Workflow examples
  const workflows = [
    {
      queryType: 'Policy Query',
      example: 'PM-KISAN scheme benefits',
      flow: ['Query Analyzer', 'Policy Researcher', 'Response Synthesizer'],
      description: 'For policy/scheme queries, the system routes to Policy Researcher who uses RAG to search government documents.'
    },
    {
      queryType: 'Cultivation Query',
      example: 'How to grow paddy in Andhra Pradesh',
      flow: ['Query Analyzer', 'Crop Specialist', 'Response Synthesizer'],
      description: 'Cultivation queries are handled by Crop Specialist using RAG to find crop cultivation guides and best practices.'
    },
    {
      queryType: 'Pest Management Query',
      example: 'Control measures for fall armyworm in maize',
      flow: ['Query Analyzer', 'Pest Advisor', 'Response Synthesizer'],
      description: 'Pest-related queries are routed to Pest Advisor who uses RAG to find IPM strategies and control measures.'
    },
    {
      queryType: 'Market Query',
      example: 'Current MSP for wheat',
      flow: ['Query Analyzer', 'Market Analyst', 'Response Synthesizer'],
      description: 'Market queries use Market Analyst with Ollama Web Search MCP for real-time web search of current prices and MSP.'
    },
    {
      queryType: 'Non-AP Query',
      example: 'How to grow paddy in Karnataka',
      flow: ['Query Analyzer', 'Non-AP Researcher', 'Response Synthesizer'],
      description: 'Queries about non-AP regions use Non-AP Researcher with Ollama Web Search MCP for web search instead of RAG.'
    },
    {
      queryType: 'Calculation Query',
      example: 'Calculate cost of cultivation for 2 hectares of paddy',
      flow: ['Query Analyzer', 'Calculator Agent (ADK)', 'Response Synthesizer'],
      description: 'Calculation queries are delegated to ADK Calculator Agent for financial calculations.'
    },
    {
      queryType: 'PDF Upload',
      example: 'Upload and analyze agricultural policy PDF',
      flow: ['Query Analyzer', 'PDF Processor', 'Response Synthesizer'],
      description: 'PDF uploads are processed by PDF Processor using PDF MCP tool for text extraction and analysis.'
    }
  ];

  // Requirements compliance
  const requirements = [
    {
      id: 'context_sharing',
      name: 'Context Sharing',
      description: 'Intermediate outputs from one agent feed into another using StateManager and task context.',
      implementation: 'Query analysis results are stored in ExecutionTracker and passed to conditional tasks. Task outputs are shared via context parameter.',
      status: '✓ Implemented'
    },
    {
      id: 'tool_integration',
      name: 'Tool Integration using MCP',
      description: 'At least two external tools (library or custom) must be used.',
      implementation: 'Ollama Web Search MCP (web search) and PDF MCP (document processing) are integrated as external MCP servers. RAG tool and Region Detector are custom CrewAI tools.',
      status: '✓ Implemented'
    },
    {
      id: 'structured_output',
      name: 'Structured Output using Pydantic',
      description: 'Final output must be generated in structured form (Markdown, Table, or JSON).',
      implementation: 'All tasks use Pydantic models (QueryAnalysis, PolicyResponse, CropGuidance, PestManagement, etc.). Final responses are formatted as Markdown.',
      status: '✓ Implemented'
    },
    {
      id: 'task_monitoring',
      name: 'Task Monitoring & Logging',
      description: 'Agents must include monitoring mechanism tracking intermediate outputs, execution flows, and errors.',
      implementation: 'step_callback and task_callback functions track agent execution, tool usage, and task outputs. ExecutionTracker maintains state across execution.',
      status: '✓ Implemented'
    },
    {
      id: 'a2a_communication',
      name: 'Agent-to-Agent Communication (A2A)',
      description: 'Use A2A protocol for interoperability between CrewAI and ADK agents.',
      implementation: 'ADKAgentAdapter enables A2A communication. StateManager handles message exchange. Calculator Agent (ADK) communicates with CrewAI agents via A2A messages.',
      status: '✓ Implemented'
    },
    {
      id: 'framework_usage',
      name: 'Framework Usage',
      description: 'Use CrewAI and/or ADK as agentic frameworks.',
      implementation: '8 CrewAI agents and 1 ADK agent (Calculator). ADKAgentAdapter bridges frameworks. Both frameworks work together seamlessly.',
      status: '✓ Implemented'
    }
  ];

  // Modal overlay style - responsive padding
  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: windowWidth >= 768 ? '0 15%' : '20px', // Leaves ~15% margin on each side on larger screens
    animation: 'fadeIn 0.2s ease',
  };

  // Modal container style - takes up ~70% width (leaving ~15% margin on each side = ~30% total)
  const modalStyle = {
    backgroundColor: 'var(--color-surface)',
    borderRadius: 'var(--radius-lg)',
    width: '100%',
    maxWidth: '1400px',
    maxHeight: '90vh',
    overflow: 'auto',
    boxShadow: 'var(--shadow-large)',
    display: 'flex',
    flexDirection: 'column',
    animation: 'modalSlideIn 0.3s ease',
    margin: '0 auto',
  };

  // Modal header style
  const headerStyle = {
    padding: 'var(--spacing-lg)',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky',
    top: 0,
    backgroundColor: 'var(--color-surface)',
    zIndex: 10,
  };

  // Close button style
  const closeButtonStyle = {
    background: 'none',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    color: 'var(--color-text-secondary)',
    padding: '4px 8px',
    borderRadius: 'var(--radius-sm)',
    transition: 'var(--transition-fast)',
  };

  // Content style
  const contentStyle = {
    padding: 'var(--spacing-lg)',
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xl)',
  };

  // Section style
  const sectionStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-md)',
  };

  // Section title style
  const sectionTitleStyle = {
    fontSize: '20px',
    fontWeight: 700,
    color: 'var(--color-text-primary)',
    paddingBottom: 'var(--spacing-sm)',
    borderBottom: '2px solid var(--color-primary)',
  };

  // Card style
  const cardStyle = {
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: 'var(--spacing-md)',
    boxShadow: 'var(--shadow-soft)',
    transition: 'var(--transition-normal)',
  };

  // Card hover effect (for interactive elements)
  const cardHoverStyle = {
    ...cardStyle,
    cursor: 'pointer',
  };

  // Agent card style
  const agentCardStyle = {
    ...cardStyle,
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-sm)',
  };

  // Framework badge style
  const frameworkBadgeStyle = (framework) => ({
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '11px',
    fontWeight: 600,
    backgroundColor: framework === 'CrewAI' ? '#4A6CF7' : '#10B981',
    color: '#FFFFFF',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  });

  // Tool type badge style
  const toolTypeBadgeStyle = (type) => ({
    display: 'inline-block',
    padding: '3px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '10px',
    fontWeight: 600,
    backgroundColor: type === 'MCP' ? '#A78BFA' : type === 'ADK' ? '#10B981' : '#4A6CF7',
    color: '#FFFFFF',
    textTransform: 'uppercase',
    marginLeft: 'var(--spacing-xs)',
  });

  // Grid layout for agents
  const agentsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: 'var(--spacing-md)',
  };

  // Workflow item style
  const workflowItemStyle = {
    ...cardStyle,
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-sm)',
  };

  // Flow visualization style
  const flowStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 'var(--spacing-xs)',
    flexWrap: 'wrap',
    marginTop: 'var(--spacing-xs)',
  };

  // Agent in flow style
  const agentInFlowStyle = {
    padding: '4px 10px',
    backgroundColor: 'var(--color-primary-light)',
    borderRadius: 'var(--radius-sm)',
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--color-primary-dark)',
  };

  // Arrow in flow style
  const arrowInFlowStyle = {
    color: 'var(--color-text-secondary)',
    fontSize: '14px',
  };

  // Requirement item style
  const requirementItemStyle = {
    ...cardStyle,
    display: 'flex',
    flexDirection: 'column',
    gap: 'var(--spacing-xs)',
  };

  // Status badge style
  const statusBadgeStyle = {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '11px',
    fontWeight: 600,
    backgroundColor: '#10B981',
    color: '#FFFFFF',
    marginTop: 'var(--spacing-xs)',
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={headerStyle}>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            About Policy Navigator
          </h2>
          <button
            style={closeButtonStyle}
            onClick={onClose}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = 'var(--color-background-light)';
              e.target.style.color = 'var(--color-text-primary)';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.color = 'var(--color-text-secondary)';
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={contentStyle}>
          {/* Agents Section */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>Agents Used</h3>
            <div style={agentsGridStyle}>
              {agents.map((agent) => (
                <div key={agent.id} style={agentCardStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {agent.name}
                      </h4>
                      <div style={{ display: 'flex', gap: 'var(--spacing-xs)', alignItems: 'center', marginBottom: 'var(--spacing-xs)' }}>
                        <span style={frameworkBadgeStyle(agent.framework)}>{agent.framework}</span>
                        {agent.tool !== 'None' && (
                          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Tool: {agent.tool}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                    {agent.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Tools Section */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>All Tools</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              {tools.map((tool, index) => (
                <div key={index} style={cardStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--spacing-xs)' }}>
                    <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {tool.name}
                      <span style={toolTypeBadgeStyle(tool.type)}>{tool.type}</span>
                    </h4>
                    <span style={frameworkBadgeStyle(tool.framework)}>{tool.framework}</span>
                  </div>
                  <p style={{ margin: '4px 0', fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                    {tool.description}
                  </p>
                  <div style={{ marginTop: 'var(--spacing-xs)', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    <strong>Used by:</strong> {tool.usedBy.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Workflow Section */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>Agent Workflow by Query Type</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              {workflows.map((workflow, index) => (
                <div key={index} style={workflowItemStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--spacing-xs)' }}>
                    <div>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {workflow.queryType}
                      </h4>
                      <p style={{ margin: 0, fontSize: '12px', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                        Example: "{workflow.example}"
                      </p>
                    </div>
                  </div>
                  <div style={flowStyle}>
                    {workflow.flow.map((agent, idx) => (
                      <React.Fragment key={idx}>
                        <span style={agentInFlowStyle}>{agent}</span>
                        {idx < workflow.flow.length - 1 && <span style={arrowInFlowStyle}>→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                  <p style={{ margin: 'var(--spacing-xs) 0 0 0', fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                    {workflow.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Requirements Section */}
          <div style={sectionStyle}>
            <h3 style={sectionTitleStyle}>Minimum Requirements Compliance</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              {requirements.map((req) => (
                <div key={req.id} style={requirementItemStyle}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {req.name}
                      </h4>
                      <p style={{ margin: '4px 0', fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                        <strong>Requirement:</strong> {req.description}
                      </p>
                      <p style={{ margin: '4px 0', fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                        <strong>Implementation:</strong> {req.implementation}
                      </p>
                      <span style={statusBadgeStyle}>{req.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutModal;

