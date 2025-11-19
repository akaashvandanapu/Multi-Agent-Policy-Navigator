import React from 'react';
import FloatingContainer from './FloatingContainer';
import WorkflowMindMap from './WorkflowMindMap';

/**
 * RightPanel - Displays workflow mind map for the current query
 * Takes up 30% of the width
 */
const RightPanel = ({ workflowDetails }) => {
  const panelStyle = {
    width: '30%',
    display: 'flex',
    flexDirection: 'column',
    padding: 'var(--spacing-sm)',
    gap: 'var(--spacing-xs)',
    overflow: 'hidden',
  };

  return (
    <div style={panelStyle}>
      <FloatingContainer 
        padding="sm" 
        borderRadius="lg" 
        shadow="medium"
        style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          overflow: 'hidden',
          minHeight: 0,
          backgroundColor: 'var(--color-surface)',
        }}
      >
        <WorkflowMindMap workflowDetails={workflowDetails} />
      </FloatingContainer>
    </div>
  );
};

export default RightPanel;

