const API_URL = 'http://localhost:5000';

async function checkHealth() {
  try {
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    const el = document.getElementById('apiStatus');
    const ok = data.status === 'healthy';
    el.textContent = ok ? 'Ready' : 'Error';
    el.className = ok ? 'ok' : 'err';
  } catch {
    const el = document.getElementById('apiStatus');
    el.textContent = 'Offline';
    el.className = 'err';
  }
}

function addMessage(text, type) {
  const wrap = document.getElementById('messages');
  const m = document.createElement('div');
  m.className = `msg ${type}`;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = type === 'user' ? 'You' : 'Policy Navigator';
  const content = document.createElement('div');
  content.className = 'content';
  content.innerHTML = text
    .replace(/### (.*)/g, '<h3>$1</h3>')
    .replace(/## (.*)/g, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  m.appendChild(meta);
  m.appendChild(content);
  wrap.appendChild(m);
  wrap.scrollTop = wrap.scrollHeight;
}

async function sendQuery() {
  const input = document.getElementById('queryInput');
  const btn = document.getElementById('sendBtn');
  const query = input.value.trim();
  if (!query) return;

  input.disabled = true;
  btn.disabled = true;
  document.getElementById('loading').classList.add('active');
  addMessage(query, 'user');
  input.value = '';

  try {
    const response = await fetch(`${API_URL}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await response.json();
    if (data.success && data.result) {
      const responseText = data.result.response_markdown || data.result.response_text || JSON.stringify(data.result, null, 2);
      addMessage(responseText, 'assistant');
      renderMindmap(extractTrace(data));
    } else {
      throw new Error(data.error || 'Unknown error');
    }
  } catch (e) {
    addMessage(`❌ ${e.message}. Ensure API is running on port 5000.`, 'assistant');
  } finally {
    input.disabled = false;
    btn.disabled = false;
    document.getElementById('loading').classList.remove('active');
    input.focus();
  }
}

function sendExample(q) {
  document.getElementById('queryInput').value = q;
  sendQuery();
}

// Extract a generic trace for visualization
function extractTrace(apiData) {
  // Preferred: apiData.result.trace (ordered steps)
  if (apiData?.result?.trace && Array.isArray(apiData.result.trace) && apiData.result.trace.length > 0) {
    return apiData.result.trace.map((t, idx) => ({
      id: `s${idx + 1}`,
      label: `${idx + 1}. ${t.agentId || t.agent || 'Agent'}${t.tool ? ' → ' + t.tool : ''}`
    }));
  }
  // Fallback: synthesize minimal path from known flow
  const guess = [
    { id: 's1', label: '1. Agent 1: Query Understanding' },
    { id: 's2', label: '2. Agent X: Tool/Domain Agent' },
    { id: 's3', label: '3. Agent 7: Response Synthesis' },
  ];
  return guess;
}

// Render a simple left-to-right mindmap using Cytoscape
let cy;
function renderMindmap(trace) {
  const container = document.getElementById('mindmap');
  if (!container) return;
  const elements = [];
  trace.forEach((step, i) => {
    elements.push({ data: { id: step.id, label: step.label } });
    if (i > 0) elements.push({ data: { id: `e${i}`, source: trace[i - 1].id, target: step.id } });
  });
  if (!cy) {
    cy = cytoscape({
      container,
      elements,
      style: [
        { selector: 'node', style: {
          'background-color': '#A8092D',
          'label': 'data(label)',
          'color': '#EDEDED',
          'font-size': '12px',
          'text-wrap': 'wrap',
          'text-max-width': '160px',
          'text-halign': 'center',
          'text-valign': 'center',
          'border-color': '#D2042D',
          'border-width': 1,
          'width': '160px',
          'height': '54px',
          'shape': 'round-rectangle',
          'box-shadow': '0 6px 14px rgba(0,0,0,0.35)'
        }},
        { selector: 'edge', style: {
          'width': 2,
          'line-color': '#7D0D2C',
          'target-arrow-color': '#7D0D2C',
          'target-arrow-shape': 'triangle'
        }}
      ],
      layout: { name: 'breadthfirst', directed: true, spacingFactor: 1.2, animate: false }
    });
  } else {
    cy.elements().remove();
    cy.add(elements);
    cy.layout({ name: 'breadthfirst', directed: true, spacingFactor: 1.2, animate: false }).run();
  }
}

// init
checkHealth();
setInterval(checkHealth, 30000);
window.sendQuery = sendQuery;
window.sendExample = sendExample;

