import React, { useRef, useEffect, useState } from 'react';

/**
 * ProjectMindMap - Complete visual flowchart of the Policy Navigator project
 * Shows system architecture with arrows and connections
 */
const ProjectMindMap = ({ isOpen, onClose }) => {
  const [dimensions, setDimensions] = useState({ width: 1200, height: 800 });
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current && isOpen) {
      const updateDimensions = () => {
        setDimensions({
          width: Math.max(1400, containerRef.current?.offsetWidth || 1400),
          height: Math.max(900, containerRef.current?.offsetHeight || 900)
        });
      };
      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Node positions (flowchart layout) - centered and balanced
  const centerX = dimensions.width / 2;
  const nodePositions = {
    // Top level
    userQuery: { x: centerX - 100, y: 30, width: 200, height: 50 },
    
    // Query Analyzer
    queryAnalyzer: { x: centerX - 110, y: 120, width: 220, height: 70 },
    
    // Specialized agents (arranged in two rows)
    policyResearcher: { x: centerX - 550, y: 250, width: 180, height: 90 },
    cropSpecialist: { x: centerX - 300, y: 250, width: 180, height: 90 },
    pestAdvisor: { x: centerX - 50, y: 250, width: 180, height: 90 },
    marketAnalyst: { x: centerX + 200, y: 250, width: 180, height: 90 },
    nonApResearcher: { x: centerX + 450, y: 250, width: 180, height: 90 },
    pdfProcessor: { x: centerX - 300, y: 380, width: 180, height: 90 },
    calculatorAgent: { x: centerX + 200, y: 380, width: 180, height: 90 },
    
    // Response Synthesizer
    responseSynthesizer: { x: centerX - 110, y: 520, width: 220, height: 70 },
    
    // User Response
    userResponse: { x: centerX - 100, y: 630, width: 200, height: 50 },
    
    // Tools (positioned on the left side)
    regionDetector: { x: 30, y: 120, width: 140, height: 50 },
    ragTool: { x: 30, y: 250, width: 140, height: 50 },
    ollamaMCP: { x: 30, y: 330, width: 140, height: 50 },
    pdfMCP: { x: 30, y: 410, width: 140, height: 50 },
    calculatorTool: { x: 30, y: 490, width: 140, height: 50 },
  };

  // Connections (arrows)
  const connections = [
    // Main flow
    { from: 'userQuery', to: 'queryAnalyzer', type: 'main' },
    { from: 'queryAnalyzer', to: 'policyResearcher', type: 'branch' },
    { from: 'queryAnalyzer', to: 'cropSpecialist', type: 'branch' },
    { from: 'queryAnalyzer', to: 'pestAdvisor', type: 'branch' },
    { from: 'queryAnalyzer', to: 'marketAnalyst', type: 'branch' },
    { from: 'queryAnalyzer', to: 'nonApResearcher', type: 'branch' },
    { from: 'queryAnalyzer', to: 'pdfProcessor', type: 'branch' },
    { from: 'queryAnalyzer', to: 'calculatorAgent', type: 'branch' },
    { from: 'policyResearcher', to: 'responseSynthesizer', type: 'converge' },
    { from: 'cropSpecialist', to: 'responseSynthesizer', type: 'converge' },
    { from: 'pestAdvisor', to: 'responseSynthesizer', type: 'converge' },
    { from: 'marketAnalyst', to: 'responseSynthesizer', type: 'converge' },
    { from: 'nonApResearcher', to: 'responseSynthesizer', type: 'converge' },
    { from: 'pdfProcessor', to: 'responseSynthesizer', type: 'converge' },
    { from: 'calculatorAgent', to: 'responseSynthesizer', type: 'converge' },
    { from: 'responseSynthesizer', to: 'userResponse', type: 'main' },
    
    // Tool connections
    { from: 'queryAnalyzer', to: 'regionDetector', type: 'tool', dashed: true },
    { from: 'policyResearcher', to: 'ragTool', type: 'tool', dashed: true },
    { from: 'cropSpecialist', to: 'ragTool', type: 'tool', dashed: true },
    { from: 'pestAdvisor', to: 'ragTool', type: 'tool', dashed: true },
    { from: 'marketAnalyst', to: 'ollamaMCP', type: 'tool', dashed: true },
    { from: 'nonApResearcher', to: 'ollamaMCP', type: 'tool', dashed: true },
    { from: 'pdfProcessor', to: 'pdfMCP', type: 'tool', dashed: true },
    { from: 'calculatorAgent', to: 'calculatorTool', type: 'tool', dashed: true },
  ];

  // Calculate arrow path with proper connection points
  const getArrowPath = (from, to, type) => {
    const fromNode = nodePositions[from];
    const toNode = nodePositions[to];
    
    if (!fromNode || !toNode) return '';
    
    // Calculate connection points based on node positions
    let startX, startY, endX, endY;
    const padding = 20; // Padding for content area
    
    if (type === 'main') {
      // Vertical connections (straight down)
      startX = fromNode.x + fromNode.width / 2;
      startY = fromNode.y + fromNode.height;
      endX = toNode.x + toNode.width / 2;
      endY = toNode.y;
    } else if (type === 'branch') {
      // Diagonal connections from query analyzer to specialized agents
      startX = fromNode.x + fromNode.width / 2;
      startY = fromNode.y + fromNode.height;
      endX = toNode.x + toNode.width / 2;
      endY = toNode.y;
    } else if (type === 'converge') {
      // Connections from agents to synthesizer
      startX = fromNode.x + fromNode.width / 2;
      startY = fromNode.y + fromNode.height;
      endX = toNode.x + toNode.width / 2;
      endY = toNode.y;
    } else if (type === 'tool') {
      // Horizontal connections to tools on the left
      startX = fromNode.x;
      startY = fromNode.y + fromNode.height / 2;
      endX = toNode.x + toNode.width;
      endY = toNode.y + toNode.height / 2;
    }
    
    // Add padding offset
    startX += padding;
    startY += padding;
    endX += padding;
    endY += padding;
    
    return `M ${startX} ${startY} L ${endX} ${endY}`;
  };


  // Styles
  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000,
    padding: '20px',
  };

  const modalStyle = {
    backgroundColor: 'var(--color-surface)',
    borderRadius: 'var(--radius-lg)',
    width: '100%',
    maxWidth: '95vw',
    maxHeight: '95vh',
    overflow: 'auto',
    boxShadow: 'var(--shadow-large)',
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyle = {
    padding: 'var(--spacing-lg)',
    borderBottom: '2px solid var(--color-border)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky',
    top: 0,
    backgroundColor: 'var(--color-surface)',
    zIndex: 10,
  };

  const closeButtonStyle = {
    background: 'none',
    border: 'none',
    fontSize: '28px',
    cursor: 'pointer',
    color: 'var(--color-text-secondary)',
    padding: '4px 12px',
    borderRadius: 'var(--radius-sm)',
    transition: 'var(--transition-fast)',
  };

  const contentStyle = {
    padding: 'var(--spacing-xl)',
    position: 'relative',
    minHeight: '750px',
    overflow: 'auto',
    backgroundColor: '#F9FAFB',
  };

  // Node styles
  const nodeStyle = (type) => {
    const styles = {
      'input': {
        backgroundColor: '#3B82F6',
        color: '#FFFFFF',
        border: '3px solid #2563EB',
      },
      'analysis': {
        backgroundColor: '#8B5CF6',
        color: '#FFFFFF',
        border: '3px solid #7C3AED',
      },
      'rag': {
        backgroundColor: '#6366F1',
        color: '#FFFFFF',
        border: '3px solid #4F46E5',
      },
      'mcp': {
        backgroundColor: '#A78BFA',
        color: '#FFFFFF',
        border: '3px solid #8B5CF6',
      },
      'synthesis': {
        backgroundColor: '#10B981',
        color: '#FFFFFF',
        border: '3px solid #059669',
      },
      'adk': {
        backgroundColor: '#10B981',
        color: '#FFFFFF',
        border: '3px solid #059669',
      },
      'output': {
        backgroundColor: '#3B82F6',
        color: '#FFFFFF',
        border: '3px solid #2563EB',
      },
      'tool': {
        backgroundColor: 'var(--color-surface)',
        color: 'var(--color-text-primary)',
        border: '2px solid #6B7280',
        fontSize: '12px',
      },
    };
    
    return {
      position: 'absolute',
      padding: '12px 16px',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-medium)',
      fontWeight: 600,
      fontSize: '14px',
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2,
      ...styles[type],
    };
  };

  const toolLabelStyle = {
    fontSize: '10px',
    marginTop: '4px',
    opacity: 0.9,
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={headerStyle}>
          <h2 style={{ margin: 0, fontSize: '28px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            🗺️ Project Architecture Flowchart
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

        {/* Flowchart Content */}
        <div style={contentStyle} ref={containerRef}>
          <svg
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: dimensions.width,
              height: dimensions.height,
              zIndex: 1,
              pointerEvents: 'none',
            }}
            viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
            preserveAspectRatio="none"
          >
            <defs>
              {/* Arrow markers for different connection types */}
              <marker
                id="arrowhead-main"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#3B82F6" />
              </marker>
              <marker
                id="arrowhead-branch"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#8B5CF6" />
              </marker>
              <marker
                id="arrowhead-converge"
                markerWidth="10"
                markerHeight="10"
                refX="9"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 10 3, 0 6" fill="#10B981" />
              </marker>
              <marker
                id="arrowhead-tool"
                markerWidth="8"
                markerHeight="8"
                refX="7"
                refY="2.5"
                orient="auto"
              >
                <polygon points="0 0, 8 2.5, 0 5" fill="#6B7280" />
              </marker>
            </defs>
            
            {/* Draw connections */}
            {connections.map((conn, idx) => {
              const path = getArrowPath(conn.from, conn.to, conn.type);
              const strokeColor = conn.type === 'tool' ? '#6B7280' : 
                                 conn.type === 'main' ? '#3B82F6' : 
                                 conn.type === 'converge' ? '#10B981' : '#8B5CF6';
              const markerId = `arrowhead-${conn.type}`;
              
              return (
                <path
                  key={idx}
                  d={path}
                  stroke={strokeColor}
                  strokeWidth={conn.type === 'main' ? 3 : conn.type === 'tool' ? 2 : 2.5}
                  fill="none"
                  strokeDasharray={conn.dashed ? '5,5' : '0'}
                  markerEnd={`url(#${markerId})`}
                  opacity={conn.type === 'tool' ? 0.6 : 0.8}
                />
              );
            })}
          </svg>

          {/* User Query Node */}
          <div style={{
            ...nodeStyle('input'),
            left: `${nodePositions.userQuery.x + 20}px`,
            top: `${nodePositions.userQuery.y + 20}px`,
            width: `${nodePositions.userQuery.width}px`,
            height: `${nodePositions.userQuery.height}px`,
          }}>
            User Query
          </div>

          {/* Query Analyzer Node */}
          <div style={{
            ...nodeStyle('analysis'),
            left: `${nodePositions.queryAnalyzer.x + 20}px`,
            top: `${nodePositions.queryAnalyzer.y + 20}px`,
            width: `${nodePositions.queryAnalyzer.width}px`,
            height: `${nodePositions.queryAnalyzer.height}px`,
          }}>
            Query Analyzer
            <div style={toolLabelStyle}>Region Detector</div>
          </div>

          {/* Specialized Agents */}
          <div style={{
            ...nodeStyle('rag'),
            left: `${nodePositions.policyResearcher.x + 20}px`,
            top: `${nodePositions.policyResearcher.y + 20}px`,
            width: `${nodePositions.policyResearcher.width}px`,
            height: `${nodePositions.policyResearcher.height}px`,
          }}>
            Policy Researcher
            <div style={toolLabelStyle}>RAG Document Search</div>
          </div>

          <div style={{
            ...nodeStyle('rag'),
            left: `${nodePositions.cropSpecialist.x + 20}px`,
            top: `${nodePositions.cropSpecialist.y + 20}px`,
            width: `${nodePositions.cropSpecialist.width}px`,
            height: `${nodePositions.cropSpecialist.height}px`,
          }}>
            Crop Specialist
            <div style={toolLabelStyle}>RAG Document Search</div>
          </div>

          <div style={{
            ...nodeStyle('rag'),
            left: `${nodePositions.pestAdvisor.x + 20}px`,
            top: `${nodePositions.pestAdvisor.y + 20}px`,
            width: `${nodePositions.pestAdvisor.width}px`,
            height: `${nodePositions.pestAdvisor.height}px`,
          }}>
            Pest Advisor
            <div style={toolLabelStyle}>RAG Document Search</div>
          </div>

          <div style={{
            ...nodeStyle('mcp'),
            left: `${nodePositions.marketAnalyst.x + 20}px`,
            top: `${nodePositions.marketAnalyst.y + 20}px`,
            width: `${nodePositions.marketAnalyst.width}px`,
            height: `${nodePositions.marketAnalyst.height}px`,
          }}>
            Market Analyst
            <div style={toolLabelStyle}>Ollama Web Search MCP</div>
          </div>

          <div style={{
            ...nodeStyle('mcp'),
            left: `${nodePositions.nonApResearcher.x + 20}px`,
            top: `${nodePositions.nonApResearcher.y + 20}px`,
            width: `${nodePositions.nonApResearcher.width}px`,
            height: `${nodePositions.nonApResearcher.height}px`,
          }}>
            Non-AP Researcher
            <div style={toolLabelStyle}>Ollama Web Search MCP</div>
          </div>

          <div style={{
            ...nodeStyle('mcp'),
            left: `${nodePositions.pdfProcessor.x + 20}px`,
            top: `${nodePositions.pdfProcessor.y + 20}px`,
            width: `${nodePositions.pdfProcessor.width}px`,
            height: `${nodePositions.pdfProcessor.height}px`,
          }}>
            PDF Processor
            <div style={toolLabelStyle}>PDF MCP</div>
          </div>

          <div style={{
            ...nodeStyle('adk'),
            left: `${nodePositions.calculatorAgent.x + 20}px`,
            top: `${nodePositions.calculatorAgent.y + 20}px`,
            width: `${nodePositions.calculatorAgent.width}px`,
            height: `${nodePositions.calculatorAgent.height}px`,
          }}>
            Calculator Agent
            <div style={toolLabelStyle}>Calculator (ADK)</div>
          </div>

          {/* Response Synthesizer */}
          <div style={{
            ...nodeStyle('synthesis'),
            left: `${nodePositions.responseSynthesizer.x + 20}px`,
            top: `${nodePositions.responseSynthesizer.y + 20}px`,
            width: `${nodePositions.responseSynthesizer.width}px`,
            height: `${nodePositions.responseSynthesizer.height}px`,
          }}>
            Response Synthesizer
          </div>

          {/* User Response */}
          <div style={{
            ...nodeStyle('output'),
            left: `${nodePositions.userResponse.x + 20}px`,
            top: `${nodePositions.userResponse.y + 20}px`,
            width: `${nodePositions.userResponse.width}px`,
            height: `${nodePositions.userResponse.height}px`,
          }}>
            User Response
          </div>

          {/* Tool Nodes (on the left side) */}
          <div style={{
            ...nodeStyle('tool'),
            left: `${nodePositions.regionDetector.x + 20}px`,
            top: `${nodePositions.regionDetector.y + 20}px`,
            width: `${nodePositions.regionDetector.width}px`,
            height: `${nodePositions.regionDetector.height}px`,
          }}>
            Region Detector
            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.7 }}>Custom Tool</div>
          </div>

          <div style={{
            ...nodeStyle('tool'),
            left: `${nodePositions.ragTool.x + 20}px`,
            top: `${nodePositions.ragTool.y + 20}px`,
            width: `${nodePositions.ragTool.width}px`,
            height: `${nodePositions.ragTool.height}px`,
          }}>
            RAG Document Search
            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.7 }}>Custom Tool</div>
          </div>

          <div style={{
            ...nodeStyle('tool'),
            left: `${nodePositions.ollamaMCP.x + 20}px`,
            top: `${nodePositions.ollamaMCP.y + 20}px`,
            width: `${nodePositions.ollamaMCP.width}px`,
            height: `${nodePositions.ollamaMCP.height}px`,
          }}>
            Ollama Web Search MCP
            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.7 }}>MCP Tool</div>
          </div>

          <div style={{
            ...nodeStyle('tool'),
            left: `${nodePositions.pdfMCP.x + 20}px`,
            top: `${nodePositions.pdfMCP.y + 20}px`,
            width: `${nodePositions.pdfMCP.width}px`,
            height: `${nodePositions.pdfMCP.height}px`,
          }}>
            PDF MCP
            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.7 }}>MCP Tool</div>
          </div>

          <div style={{
            ...nodeStyle('tool'),
            left: `${nodePositions.calculatorTool.x + 20}px`,
            top: `${nodePositions.calculatorTool.y + 20}px`,
            width: `${nodePositions.calculatorTool.width}px`,
            height: `${nodePositions.calculatorTool.height}px`,
          }}>
            Calculator (ADK)
            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.7 }}>ADK Tool</div>
          </div>
        </div>

        {/* Legend */}
        <div style={{
          padding: 'var(--spacing-md) var(--spacing-xl)',
          borderTop: '2px solid var(--color-border)',
          backgroundColor: 'var(--color-background-light)',
        }}>
          <div style={{
            display: 'flex',
            gap: 'var(--spacing-lg)',
            flexWrap: 'wrap',
            fontSize: '12px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '20px', height: '3px', backgroundColor: '#3B82F6' }}></div>
              <span>Main Flow</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '20px', height: '3px', backgroundColor: '#8B5CF6' }}></div>
              <span>Agent Branching</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '20px', height: '3px', backgroundColor: '#10B981', borderTop: '2px dashed' }}></div>
              <span>Convergence</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '20px', height: '2px', backgroundColor: '#6B7280', borderTop: '2px dashed' }}></div>
              <span>Tool Connection</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectMindMap;
