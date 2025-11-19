# Test Query Suite for Policy Navigator

This document provides comprehensive test queries to validate the execution flow, agent routing, tool usage, and workflow display functionality.

## Test Query Categories

### 1. Policy Query (AP Region)
**Query**: `What is PM-KISAN scheme in Andhra Pradesh?`

**Expected Execution**:
- **Agents**: Query Analyzer → Policy Researcher → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Policy Researcher)
- **Framework**: CrewAI (all agents)
- **Requirements**: 
  - Context Sharing: ✓
  - Tool Integration: ✓ (2 tools)
  - Structured Output: ✓
  - Task Monitoring: ✓
  - A2A Communication: ✗ (no ADK tools)
  - Framework Usage: ✗ (only CrewAI)

**Validation Points**:
- Region detection identifies AP
- Policy researcher uses RAG tool to search local database
- Response includes scheme details from local documents

---

### 2. Crop Cultivation Query (AP Region)
**Query**: `How to grow paddy rice in Guntur district?`

**Expected Execution**:
- **Agents**: Query Analyzer → Crop Specialist → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Crop Specialist)
- **Framework**: CrewAI (all agents)
- **Requirements**: Same as Policy Query

**Validation Points**:
- Region detection identifies AP (Guntur is AP district)
- Crop specialist uses RAG tool for cultivation guides
- Response includes sowing, fertilizer, irrigation schedules

---

### 3. Pest Management Query
**Query**: `Control measures for fall armyworm in maize`

**Expected Execution**:
- **Agents**: Query Analyzer → Pest Advisor → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Pest Advisor)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Pest advisor identifies pest and provides IPM strategies
- Response includes cultural, biological, and chemical control measures
- Safe periods and yield loss estimates included

---

### 4. Market Query (AP Region)
**Query**: `What is the MSP for paddy in Andhra Pradesh 2024?`

**Expected Execution**:
- **Agents**: Query Analyzer → Market Analyst → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - Ollama Web Search MCP (Market Analyst)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Market analyst uses Ollama Web Search MCP for real-time MSP data
- Response includes current MSP with sources and timestamps
- Web-searched data clearly indicated

---

### 5. Calculator Query (ADK Tool)
**Query**: `Calculate the cost of cultivation for 2 hectares of paddy in Andhra Pradesh`

**Expected Execution**:
- **Agents**: Query Analyzer → Crop Specialist → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Crop Specialist)
  - Calculator Tool (ADK) (Crop Specialist)
- **Framework**: CrewAI (agents), ADK (calculator tool)
- **Requirements**: 
  - A2A Communication: ✓ (ADK tool used)
  - Framework Usage: ✓ (both CrewAI and ADK)

**Validation Points**:
- Crop specialist uses calculator ADK tool for cost calculations
- ADK tool properly tracked and displayed in right panel
- A2A communication requirement met
- Framework usage requirement met

---

### 6. PDF Upload Query
**Query**: Upload a PDF document and ask `Analyze this document about PM-KISAN`

**Expected Execution**:
- **Agents**: Query Analyzer (with PDF processing) → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - PDF Tool (ADK) (Query Analyzer)
- **Framework**: CrewAI (agents), ADK (PDF tool)
- **Requirements**: 
  - A2A Communication: ✓ (ADK tool used)
  - Framework Usage: ✓ (both CrewAI and ADK)

**Validation Points**:
- PDF processing task conditionally executes
- PDF ADK tool extracts text and structured data
- Response includes PDF analysis with confidence score
- ADK tool usage displayed in workflow

---

### 7. Non-AP Region Query
**Query**: `What are agricultural schemes available in Karnataka?`

**Expected Execution**:
- **Agents**: Query Analyzer → Non-AP Researcher → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - Ollama Web Search MCP (Non-AP Researcher)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Region detection identifies non-AP region (Karnataka)
- Non-AP researcher uses Ollama Web Search MCP instead of RAG
- Response includes disclaimer about web-searched data
- No local database data used

---

### 8. Multi-Agent Query
**Query**: `What is PM-KISAN scheme and how to grow paddy with pest management?`

**Expected Execution**:
- **Agents**: Query Analyzer → Policy Researcher → Crop Specialist → Pest Advisor → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Policy Researcher, Crop Specialist, Pest Advisor - multiple times)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Multiple agents execute in sequence
- Each agent uses appropriate tools
- Response synthesizes information from all agents
- All agents and tools displayed in workflow

---

### 9. Non-AP Market Query (with Market Analyst Recommendation)
**Query**: `What is the MSP for rice in Tamil Nadu?`

**Expected Execution**:
- **Agents**: Query Analyzer → Non-AP Researcher → Market Analyst → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - Ollama Web Search MCP (Non-AP Researcher, Market Analyst)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Non-AP researcher detects market-related query
- Sets `recommend_market_analyst=True`
- Market analyst conditionally executes
- Response includes both Ollama Web Search MCP and market analysis

---

### 10. Out-of-Scope Query
**Query**: `What is the weather today?`

**Expected Execution**:
- **Agents**: Query Analyzer → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Query analyzer detects out-of-scope query
- Only response synthesizer executes (no specialized agents)
- Response is simple plain text (no markdown)
- No sources or follow-up questions

---

### 11. Calculator with Multiple Operations
**Query**: `Calculate subsidy for 1 hectare paddy under PM-KISAN and expected profit`

**Expected Execution**:
- **Agents**: Query Analyzer → Policy Researcher → Crop Specialist → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Policy Researcher, Crop Specialist)
  - Calculator Tool (ADK) (Crop Specialist - multiple calculations)
- **Framework**: CrewAI (agents), ADK (calculator tool)

**Validation Points**:
- Multiple calculator operations performed
- ADK tool properly tracks all calculations
- A2A communication working for multiple tool calls

---

### 12. Mixed Region Query
**Query**: `Compare PM-KISAN benefits in Andhra Pradesh and Maharashtra`

**Expected Execution**:
- **Agents**: Query Analyzer → Policy Researcher → Non-AP Researcher → Response Synthesizer
- **Tools**: 
  - Region Detector Tool (Query Analyzer)
  - RAG Tool (Policy Researcher - for AP)
  - Ollama Web Search MCP (Non-AP Researcher - for Maharashtra)
- **Framework**: CrewAI (all agents)

**Validation Points**:
- Region detection identifies mixed regions
- Both RAG (AP) and Ollama Web Search MCP (non-AP) used
- Response distinguishes between local and web-searched data

---

## Verification Checklist

For each test query, verify:

### Backend Verification
- [ ] Correct agents executed (check execution_tracker)
- [ ] Correct tools used per agent (check tool tracking)
- [ ] Workflow details correctly built
- [ ] ADK tools properly detected when used
- [ ] A2A communication requirement correctly calculated
- [ ] Framework usage requirement correctly calculated

### Frontend Verification
- [ ] All executed agents appear in right panel
- [ ] All used tools appear under correct agents
- [ ] Tool framework badges display correctly (CrewAI/ADK)
- [ ] Execution order indicators show (1, 2, 3...)
- [ ] Summary section shows correct counts
- [ ] Requirements compliance shows accurate status
- [ ] ADK tool indicators visible when applicable

### Log Verification
- [ ] Tool usage logged in step_callback
- [ ] Agent execution logged in task_callback
- [ ] ADK tool detection logged when used
- [ ] A2A message creation logged when ADK tools used

### Response Quality
- [ ] Response directly answers the query
- [ ] Sources properly cited
- [ ] Follow-up questions relevant
- [ ] Markdown formatting correct
- [ ] Out-of-scope queries handled appropriately

## Expected Workflow Display Features

1. **Execution Summary Section**:
   - Total agents executed
   - Total tools used
   - CrewAI tools count
   - ADK tools count
   - Frameworks used

2. **Agent Workflow Section**:
   - Sequential agent display with execution order (1, 2, 3...)
   - Framework badges (CrewAI/ADK)
   - ADK Tools indicator when agent uses ADK tools
   - Tools listed with framework badges (CrewAI/ADK)

3. **Requirements Compliance Section**:
   - Context Sharing: Always ✓
   - Tool Integration: ✓ if ≥2 tools used
   - Structured Output: Always ✓
   - Task Monitoring: Always ✓
   - A2A Communication: ✓ if ADK tools/agents used
   - Framework Usage: ✓ if both CrewAI and ADK used

## Notes

- All queries should be tested in the React frontend
- Check browser console for any errors
- Verify workflow details update after each query
- Test with both AP and non-AP regions
- Test with and without ADK tools to verify requirement tracking
- Verify conditional task execution (some agents should not run for certain queries)

