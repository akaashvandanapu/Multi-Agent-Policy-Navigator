import React from 'react';

/**
 * WorkflowMindMap - Visualizes agent workflow as a mind map
 * Shows agents, frameworks, tools, and fallbacks
 */
const WorkflowMindMap = ({ workflowDetails }) => {
  if (!workflowDetails || !workflowDetails.agents || workflowDetails.agents.length === 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: 'var(--color-text-secondary)',
        fontSize: '14px',
        textAlign: 'center',
        padding: 'var(--spacing-md)',
      }}>
        No workflow data available. Process a query to see the agent flow.
      </div>
    );
  }

  const { agents, fallbacks = [] } = workflowDetails;

  // Color scheme
  const frameworkColors = {
    'CrewAI': '#4A6CF7',
    'ADK': '#10B981',
  };

  const toolColor = '#F59E0B';
  const fallbackColor = '#EF4444';
  const adkToolColor = '#10B981'; // Green for ADK tools
  const crewaiToolColor = '#4A6CF7'; // Blue for CrewAI tools


  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    overflow: 'auto',
    padding: 'var(--spacing-sm)',
    gap: 'var(--spacing-sm)',
  };

  const sectionStyle = {
    marginBottom: 'var(--spacing-md)',
  };

  const sectionTitleStyle = {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--color-text-primary)',
    marginBottom: 'var(--spacing-xs)',
    paddingBottom: '4px',
    borderBottom: '1px solid var(--color-border)',
  };

  // Mind map visualization
  const mindMapStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: 'var(--spacing-sm)',
  };

  const agentNodeStyle = (agent, index) => ({
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    padding: '10px 12px',
    borderRadius: 'var(--radius-md)',
    backgroundColor: agent.executed === false ? 'var(--color-surface-secondary)' : 'var(--color-surface)',
    border: `2px solid ${frameworkColors[agent.framework] || '#6B7280'}`,
    fontSize: '13px',
    position: 'relative',
    opacity: agent.executed === false ? 0.6 : 1.0,
  });

  const agentHeaderStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
  };

  const agentNumberStyle = {
    fontWeight: 700,
    color: 'var(--color-text-primary)',
    minWidth: '50px',
    fontSize: '12px',
  };

  const agentNameStyle = {
    flex: 1,
    color: 'var(--color-text-primary)',
    fontWeight: 500,
    fontSize: '13px',
  };

  const frameworkBadgeStyle = (framework) => ({
    padding: '2px 8px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '10px',
    fontWeight: 600,
    backgroundColor: frameworkColors[framework] || '#6B7280',
    color: '#FFFFFF',
    whiteSpace: 'nowrap',
  });

  const toolsContainerStyle = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    marginTop: '4px',
    paddingTop: '6px',
    borderTop: '1px solid var(--color-border)',
  };

  // Helper function to check if tool is ADK-based
  const isADKTool = (toolName) => {
    return toolName && (toolName.includes('ADK') || toolName.includes('(ADK)'));
  };

  const toolBadgeStyle = (toolName) => ({
    padding: '2px 6px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '9px',
    fontWeight: 500,
    backgroundColor: isADKTool(toolName) ? adkToolColor : crewaiToolColor,
    color: '#FFFFFF',
    whiteSpace: 'nowrap',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
  });

  const toolFrameworkBadgeStyle = (isADK) => ({
    fontSize: '7px',
    fontWeight: 600,
    opacity: 0.9,
    padding: '1px 3px',
    borderRadius: '2px',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  });

  const noToolsStyle = {
    fontSize: '10px',
    color: 'var(--color-text-secondary)',
    fontStyle: 'italic',
  };

  const fallbackIndicatorStyle = {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: fallbackColor,
    border: '1px solid #FFFFFF',
  };

  const arrowStyle = {
    marginLeft: '30px',
    color: 'var(--color-text-secondary)',
    fontSize: '12px',
  };

  return (
    <div style={containerStyle}>
      {/* Mind Map Section */}
      <div style={sectionStyle}>
        <div style={sectionTitleStyle}>Agent Workflow</div>
        <div style={mindMapStyle}>
          {agents.map((agent, index) => (
            <React.Fragment key={agent.id || index}>
              {index > 0 && <div style={arrowStyle}>↓</div>}
              <div style={agentNodeStyle(agent, index)}>
                <div style={agentHeaderStyle}>
                  <div style={agentNumberStyle}>
                    {index + 1}
                  </div>
                  <div style={agentNameStyle}>{agent.name}</div>
                  <div style={frameworkBadgeStyle(agent.framework)}>
                    {agent.framework}
                  </div>
                  {agent.executed === false && (
                    <div
                      style={{
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '9px',
                        fontWeight: 600,
                        backgroundColor: '#6B7280',
                        color: '#FFFFFF',
                        whiteSpace: 'nowrap',
                      }}
                      title="Agent was skipped (condition not met)"
                    >
                      Skipped
                    </div>
                  )}
                  {agent.executed === true && (
                    <div
                      style={{
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '9px',
                        fontWeight: 600,
                        backgroundColor: '#10B981',
                        color: '#FFFFFF',
                        whiteSpace: 'nowrap',
                      }}
                      title="Agent executed successfully"
                    >
                      Executed
                    </div>
                  )}
                  {agent.uses_adk_tools && (
                    <div
                      style={{
                        ...frameworkBadgeStyle('ADK'),
                        backgroundColor: adkToolColor,
                        fontSize: '9px',
                        padding: '2px 6px',
                      }}
                      title="Uses ADK tools"
                    >
                      ADK Tools
                    </div>
                  )}
                  {agent.fallback_used && (
                    <div
                      style={fallbackIndicatorStyle}
                      title={`Fallback used: ${agent.fallback_type || 'unknown'}`}
                    />
                  )}
                </div>
                <div style={toolsContainerStyle}>
                  {agent.tools && agent.tools.length > 0 ? (
                    agent.tools.map((tool, toolIndex) => {
                      const isADK = isADKTool(tool);
                      return (
                        <div key={toolIndex} style={toolBadgeStyle(tool)} title={tool}>
                          <span>{tool}</span>
                          <span style={toolFrameworkBadgeStyle(isADK)}>
                            {isADK ? 'ADK' : 'CrewAI'}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <div style={noToolsStyle}>No tools used</div>
                  )}
                  {agent.executed === false && agent.tools && agent.tools.length > 0 && (
                    <div style={{
                      fontSize: '9px',
                      color: 'var(--color-text-secondary)',
                      fontStyle: 'italic',
                      marginTop: '4px',
                    }}>
                      (Expected tools - agent was skipped)
                    </div>
                  )}
                </div>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Fallbacks Section */}
      {fallbacks && fallbacks.length > 0 && (
        <div style={sectionStyle}>
          <div style={sectionTitleStyle}>Fallbacks ({fallbacks.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {fallbacks.map((fallback, index) => (
              <div
                key={index}
                style={{
                  padding: '6px 8px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: '#FEF2F2',
                  border: '1px solid #FECACA',
                  fontSize: '11px',
                  color: '#991B1B',
                }}
              >
                <div style={{ fontWeight: 600 }}>
                  {fallback.agent_id?.replace('agent_', 'Agent ').replace('_', ' ') || 'Unknown Agent'}
                </div>
                <div style={{ fontSize: '10px', marginTop: '2px' }}>
                  {fallback.type === 'llm' ? 'LLM' : 'Tool'} Fallback: {fallback.from} → {fallback.to}
                  {fallback.reason && ` (${fallback.reason})`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowMindMap;

