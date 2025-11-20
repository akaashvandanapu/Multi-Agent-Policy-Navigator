# Policy Navigator - Multi-Agent System

📹 **[Watch Project Demo & Description](https://www.loom.com/share/c96b01df32de4ec281d9a174ec43578a)**

A comprehensive multi-agent system built with CrewAI for navigating agricultural policies, crop cultivation guidance, pest management, and real-time market information for farmers in Andhra Pradesh.

## Features

- **9 Specialized AI Agents** working collaboratively (8 CrewAI + 1 ADK)
- **MCP Integration**: Ollama Web Search MCP (web search) and PDF MCP (document processing)
- **Custom Tools**: RAG (ChromaDB), Region Detector
- **Structured Outputs**: Pydantic models for all agent responses
- **Context Sharing**: Agents share intermediate outputs via CrewAI memory
- **A2A Communication**: ADK integration for calculator agent
- **Monitoring & Logging**: Comprehensive callbacks for tracking execution

## System Architecture

The following diagram shows the complete project architecture and agent flow:

![Project Mind Map](images/project-mindmap.png)

## Complete System Workflow Diagram

The following diagram illustrates the complete workflow from user input to final response:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER QUERY INPUT                                   │
│                    (Text Query + Optional PDF File)                         │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATOR                                     │
│  - Initializes CrewAI Crew                                                  │
│  - Manages Workflow Execution                                               │
│  - Handles PDF Upload Processing                                            │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POLICY NAVIGATOR CREW                                     │
│                    (CrewAI Framework)                                        │
│  - Agent Coordination                                                        │
│  - Task Orchestration                                                        │
│  - Memory Management                                                         │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUERY ANALYZER AGENT                                     │
│                    (Always Executes First)                                   │
│                                                                               │
│  STEP 1: Scope Validation                                                    │
│    ├─ Agricultural? → Continue                                               │
│    └─ Out of Scope? → Route to Synthesizer Only                             │
│                                                                               │
│  STEP 2: Region Detection (Region Detector Tool)                             │
│    ├─ AP Region → Use RAG                                                   │
│    ├─ Non-AP Region → Use Web Search                                         │
│    └─ Mixed → Use Web Search                                                  │
│                                                                               │
│  STEP 3: Query Classification                                               │
│    ├─ Policy / Cultivation / Pest / Market / General                         │
│    └─ Document Upload (if PDF provided)                                       │
│                                                                               │
│  STEP 4: Entity Extraction                                                    │
│    └─ Crops, Schemes, Locations, Pests                                      │
│                                                                               │
│  STEP 5: Agent Assignment                                                    │
│    └─ Generates required_agents list                                         │
│                                                                               │
│  OUTPUT: QueryAnalysis (Pydantic Model)                                      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Execution Tracker    │
                    │  (Stores Query Analysis)│
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────────────┐                  ┌───────────────────────┐
│  CONDITIONAL TASK     │                  │  CONDITIONAL TASK     │
│  EXECUTION            │                  │  EXECUTION            │
│  (Based on            │                  │  (Based on            │
│   required_agents)    │                  │   required_agents)    │
└───────┬───────────────┘                  └───────┬───────────────┘
        │                                           │
        │                                           │
┌───────┴───────┐                      ┌──────────┴──────────┐
│               │                      │                      │
▼               ▼                      ▼                      ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   POLICY      │ │    CROP       │ │    PEST       │ │    MARKET     │
│  RESEARCHER   │ │  SPECIALIST   │ │   ADVISOR     │ │   ANALYST     │
│               │ │               │ │               │ │               │
│  Tool: RAG    │ │  Tool: RAG    │ │  Tool: RAG    │ │  Tool: Ollama │
│  (ChromaDB)   │ │  (ChromaDB)   │ │  (ChromaDB)   │ │  Web Search   │
│               │ │               │ │               │ │  MCP          │
│  Output:      │ │  Output:      │ │  Output:      │ │  Output:      │
│  PolicyResp   │ │  CropGuidance │ │  PestMgmt     │ │  MarketInfo   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────┐                          ┌───────────────┐
│   NON-AP     │                          │     PDF       │
│  RESEARCHER  │                          │   PROCESSOR   │
│              │                          │               │
│  Tool: Ollama│                          │  Tool: PDF    │
│  Web Search  │                          │  MCP Server   │
│  MCP         │                          │               │
│              │                          │  Output:      │
│  Output:     │                          │  PDFAnalysis  │
│  WebSearchResp│                         │               │
└───────┬───────┘                          └───────┬───────┘
        │                                           │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   CALCULATOR AGENT    │
                │      (ADK)            │
                │                       │
                │  Tool: Google         │
                │  Generative AI        │
                │                       │
                │  A2A Communication:   │
                │  StateManager        │
                │                       │
                │  Output: Calculation  │
                │  Results              │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Execution Tracker    │
                │  (Aggregates All)     │
                │                       │
                │  - Executed Agents    │
                │  - Used Tools         │
                │  - Agent-Tool Mapping │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  RESPONSE SYNTHESIZER │
                │                       │
                │  - Combines outputs   │
                │  - Formats markdown   │
                │  - Adds citations     │
                │  - Validates content  │
                │                       │
                │  Output: FinalResponse│
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   FINAL RESPONSE      │
                │                       │
                │  - response_text      │
                │  - response_markdown  │
                │  - sources            │
                │  - confidence_score   │
                │  - workflow_details   │
                └───────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUCTURE LAYER                                   │
├──────────────────────┬──────────────────────┬─────────────────────────────────┤
│                      │                      │                                 │
│   CHROMADB           │    MCP SERVERS       │    MONITORING                   │
│   VECTOR STORE       │                      │    CALLBACKS                    │
│                      │                      │                                 │
│  - Document Storage  │  - Ollama Web Search │  - step_callback                │
│  - Embedding Search  │  - PDF Extraction    │  - task_callback                │
│  - Metadata Filter   │  - FastMCP Protocol  │  - Execution Tracking           │
│                      │                      │  - Tool Usage Logging           │
│                      │                      │                                 │
│  Used by:            │  Used by:            │  Tracks:                        │
│  - Policy Researcher │  - Market Analyst    │  - All Agents                   │
│  - Crop Specialist   │  - Non-AP Researcher │  - All Tools                    │
│  - Pest Advisor      │  - PDF Processor     │  - Execution Flow              │
│                      │                      │                                 │
└──────────────────────┴──────────────────────┴─────────────────────────────────┘
         │                      │                      │
         │                      │                      │
         └──────────────────────┴──────────────────────┘
                                │
                    (Connected to agents above)
```

## Detailed Workflow Steps

1. **User Input**: User submits query (text + optional PDF)
2. **Orchestration**: MainOrchestrator initializes CrewAI crew
3. **Query Analysis**: Query Analyzer performs scope validation, region detection, classification, entity extraction, and agent assignment
4. **Conditional Execution**: Specialized agents execute only if in required_agents list
5. **Tool Usage**: Agents use appropriate tools (RAG, MCP, ADK) based on query type
6. **A2A Communication**: ADK agents communicate via StateManager
7. **Execution Tracking**: All agents and tools tracked by ExecutionTracker
8. **Response Synthesis**: Synthesizer combines all outputs into final response
9. **Output**: Structured response with markdown, sources, and workflow details

## Project Structure

Complete project structure with file descriptions:

```
policy-navigator-project/
│
├── README.md                          # Project documentation and setup guide
├── pyproject.toml                     # Python project configuration and dependencies
├── TEST_QUERIES.md                    # Test queries for system validation
│
├── src/policy_navigator/              # Main source code package
│   ├── __init__.py                    # Package initialization
│   ├── main.py                        # CLI entry point - handles user queries and PDF uploads
│   ├── crew.py                        # Main crew orchestration using CrewAI @CrewBase pattern
│   │
│   ├── config/                        # Configuration files
│   │   ├── agents.yaml                # Agent definitions (roles, goals, backstories)
│   │   ├── tasks.yaml                 # Task definitions and descriptions
│   │   ├── llm_config.py              # LLM provider configuration (OpenAI, Groq)
│   │   └── tool_mappings.py           # Maps agents to their tools
│   │
│   ├── tools/                         # Custom CrewAI tools
│   │   ├── __init__.py                # Package initialization
│   │   ├── rag_tool.py                # RAG tool for ChromaDB document search
│   │   ├── region_detector.py         # Detects AP vs non-AP regions in queries
│   │   ├── ollama_websearch_tool.py   # Wrapper for Ollama Web Search MCP
│   │   ├── pdf_mcp_tool.py            # Wrapper for PDF MCP server
│   │   └── pdf_domain_validator.py    # Validates PDF content is agricultural
│   │
│   ├── models/                        # Pydantic data models
│   │   ├── __init__.py                # Package initialization
│   │   └── schemas.py                 # All Pydantic schemas (QueryAnalysis, PolicyResponse, etc.)
│   │
│   ├── callbacks/                     # Monitoring and tracking callbacks
│   │   ├── __init__.py                # Package initialization
│   │   ├── execution_tracker.py       # Tracks executed agents and used tools
│   │   └── monitoring.py              # Comprehensive monitoring callbacks for CrewAI
│   │
│   ├── retrieval/                     # RAG infrastructure
│   │   ├── __init__.py                # Package initialization
│   │   ├── vector_store.py            # ChromaDB vector store wrapper
│   │   └── document_processor.py      # Processes PDFs and text files for RAG
│   │
│   ├── adk/                           # ADK (Agent Development Kit) integration
│   │   ├── __init__.py                # Package initialization
│   │   ├── adk_agent.py               # Google ADK calculator agent implementation
│   │   └── adk_agent_adapter.py       # Adapter to integrate ADK agents with CrewAI
│   │
│   ├── core/                          # Core orchestration logic
│   │   ├── __init__.py                # Package initialization
│   │   └── orchestrator.py            # MainOrchestrator class for workflow management
│   │
│   └── guardrails/                    # Hallucination guardrails and validation
│       ├── __init__.py                # Package initialization
│       ├── guardrail_config.py        # Guardrail configuration settings
│       └── guardrail_factory.py       # Factory for creating guardrail instances
│
├── mcp_servers/                       # MCP (Model Context Protocol) server implementations
│   ├── __init__.py                    # Package initialization
│   ├── ollama_websearch_mcp_server.py # Ollama Web Search MCP server (FastMCP)
│   ├── pdf_extractor_mcp_server.py   # FastMCP PDF extractor using pypdf
│   └── pdf_mcp_server.py              # Legacy PDF MCP server using PyPDF2
│
├── data/                              # Document repository
│   ├── DATA_INVENTORY.json            # Inventory of all documents in the repository
│   ├── 00_Archive/                    # Archived documents
│   ├── 01_Financial_Schemes/           # Financial assistance schemes (PM-KISAN, etc.)
│   ├── 02_Credit_Loans/               # Credit and loan schemes (KCC, etc.)
│   ├── 03_Crop_Insurance/             # Crop insurance schemes (PMFBY, RWBCIS)
│   ├── 04_Seeds_Inputs/               # Seed distribution and input subsidies
│   ├── 05_Irrigation_Water/           # Irrigation and water management schemes
│   ├── 06_Soil_Health/                # Soil health and fertilizer management
│   ├── 07_Farm_Mechanization/         # Farm mechanization schemes
│   ├── 08_Market_Pricing/             # Market pricing and MSP information
│   ├── 09_Horticulture_Allied/       # Horticulture and allied activities
│   ├── 10_Extension_Training/         # Extension services and training programs
│   ├── 11_Digital_Initiatives/        # Digital agriculture initiatives
│   ├── 12_Calamity_Relief/            # Natural calamity relief schemes
│   ├── 13_Crop_Cultivation_Guides/    # Crop-specific cultivation guides
│   ├── 14_Pest_Disease_Management/    # Pest and disease management guides
│   ├── 15_Fertilizer_Schedules/      # Fertilizer application schedules
│   ├── 16_Crop_Calendar/              # Crop sowing calendar for AP
│   └── 17_Crop_Varieties/             # Recommended crop varieties
│
├── web/                               # Web interface
│   ├── api/                           # Flask REST API backend
│   │   ├── __init__.py                # Package initialization
│   │   └── app.py                     # Flask application with REST endpoints
│   │
│   ├── react-ui/                      # React frontend application
│   │   ├── package.json               # Node.js dependencies
│   │   ├── vite.config.js             # Vite build configuration
│   │   ├── index.html                 # HTML entry point
│   │   └── src/                        # React source code
│   │       ├── main.jsx               # React application entry point
│   │       ├── App.jsx                # Main App component
│   │       ├── services/              # API service layer
│   │       │   └── api.js             # API client for backend communication
│   │       ├── hooks/                 # React custom hooks
│   │       │   └── useChat.js         # Chat functionality hook
│   │       ├── components/            # React components
│   │       │   ├── PolicyNavigator.jsx        # Main Policy Navigator component
│   │       │   ├── ChatWindow.jsx             # Chat interface component
│   │       │   ├── ChatMessage.jsx            # Individual chat message component
│   │       │   ├── ChatInputBar.jsx           # Chat input component
│   │       │   ├── ChatHistoryDrawer.jsx      # Chat history sidebar
│   │       │   ├── Header.jsx                 # Application header
│   │       │   ├── RightPanel.jsx             # Right sidebar panel
│   │       │   ├── FloatingContainer.jsx      # Floating UI container
│   │       │   ├── ProjectMindMap.jsx         # Project mind map visualization
│   │       │   ├── WorkflowMindMap.jsx        # Workflow diagram visualization
│   │       │   └── AboutModal.jsx             # About modal dialog
│   │       └── styles/                # Styling files
│   │           ├── global.css         # Global CSS styles
│   │           └── theme.js           # Theme configuration
│   │
│   └── static/                        # Static files for simple HTML interface
│       ├── index.html                 # Simple HTML interface
│       ├── app.js                     # JavaScript for static interface
│       └── styles.css                 # CSS for static interface
│
├── scripts/                           # Utility scripts
│   ├── __init__.py                    # Package initialization
│   ├── initialize_rag.py              # Initializes ChromaDB with documents from data/
│   └── run_pdf_mcp_server.py          # Standalone script to run PDF MCP server
│
├── images/                            # Project images and diagrams
│   ├── project-mindmap.png            # Project architecture mind map
│   └── frontend-ui.png                # Frontend UI screenshot
│
├── project_requirements/              # Project requirements and documentation
│   ├── minimum-requirements.txt      # Minimum project requirements checklist
│   └── Policy Navigator - Multi-Agent System Project Plan.pdf  # Project plan PDF
│
├── chroma_db/                         # ChromaDB vector database (auto-generated)
│   ├── chroma.sqlite3                 # SQLite database file
│   └── [uuid]/                        # Vector data directories
│
└── [other files]                      # Additional project files
    ├── policy-navigator-report.docx   # Project report (Word)
    └── policy-navigator-report.pdf    # Project report (PDF)
```

### Key File Descriptions

#### Core Application Files

- **`src/policy_navigator/main.py`**: Command-line interface entry point. Handles user queries, PDF uploads, RAG initialization, and displays execution summaries.

- **`src/policy_navigator/crew.py`**: Main crew orchestration file using CrewAI's `@CrewBase` pattern. Defines all 9 agents, their tasks, conditional routing logic, and crew workflow.

- **`src/policy_navigator/core/orchestrator.py`**: `MainOrchestrator` class that manages the overall workflow execution and coordinates between different components.

#### Configuration Files

- **`src/policy_navigator/config/agents.yaml`**: YAML configuration defining all agent roles, goals, backstories, and capabilities.

- **`src/policy_navigator/config/tasks.yaml`**: YAML configuration defining all task descriptions, expected outputs, and agent assignments.

- **`src/policy_navigator/config/llm_config.py`**: LLM provider configuration (OpenAI, Groq) with fallback logic and model selection.

- **`src/policy_navigator/config/tool_mappings.py`**: Maps agents to their respective tools for dynamic tool assignment.

#### Tools

- **`src/policy_navigator/tools/rag_tool.py`**: CrewAI tool wrapper for ChromaDB semantic search. Used by Policy Researcher, Crop Specialist, and Pest Advisor.

- **`src/policy_navigator/tools/region_detector.py`**: Rule-based tool that detects if queries mention Andhra Pradesh or other regions. Used by Query Analyzer.

- **`src/policy_navigator/tools/ollama_websearch_tool.py`**: Wrapper for Ollama Web Search MCP. Used by Market Analyst and Non-AP Researcher.

- **`src/policy_navigator/tools/pdf_mcp_tool.py`**: Wrapper for PDF MCP server. Used by PDF Processor Agent.

- **`src/policy_navigator/tools/pdf_domain_validator.py`**: Validates that uploaded PDFs contain agricultural content.

#### Data Models

- **`src/policy_navigator/models/schemas.py`**: Contains all Pydantic models for structured outputs:
  - `QueryAnalysis` - Query analyzer output
  - `PolicyResponse` - Policy researcher output
  - `CropGuidance` - Crop specialist output
  - `PestManagement` - Pest advisor output
  - `MarketInfo` - Market analyst output
  - `WebSearchResponse` - Non-AP researcher output
  - `PDFAnalysis` - PDF processor output
  - `FinalResponse` - Response synthesizer output

#### Monitoring & Tracking

- **`src/policy_navigator/callbacks/execution_tracker.py`**: Tracks which agents executed, which tools were used, and maintains agent-tool mappings.

- **`src/policy_navigator/callbacks/monitoring.py`**: Comprehensive monitoring callbacks for CrewAI that log step execution, task completion, and agent activities.

#### RAG Infrastructure

- **`src/policy_navigator/retrieval/vector_store.py`**: ChromaDB wrapper for vector storage and semantic search operations.

- **`src/policy_navigator/retrieval/document_processor.py`**: Processes PDF and text files from the `data/` directory, chunks them, and prepares them for vector storage.

#### ADK Integration

- **`src/policy_navigator/adk/adk_agent.py`**: Google ADK calculator agent implementation using Google Generative AI (Gemini).

- **`src/policy_navigator/adk/adk_agent_adapter.py`**: Adapter pattern implementation that wraps ADK agents to work seamlessly with CrewAI agents, enabling A2A communication.

#### Guardrails

- **`src/policy_navigator/guardrails/guardrail_config.py`**: Configuration for hallucination guardrails and content validation.

- **`src/policy_navigator/guardrails/guardrail_factory.py`**: Factory for creating and configuring guardrail instances.

#### MCP Servers

- **`mcp_servers/ollama_websearch_mcp_server.py`**: FastMCP server implementation for Ollama web search API integration.

- **`mcp_servers/pdf_extractor_mcp_server.py`**: FastMCP server for PDF text extraction using pypdf library.

- **`mcp_servers/pdf_mcp_server.py`**: Legacy PDF MCP server implementation using PyPDF2.

#### Web Interface

- **`web/api/app.py`**: Flask REST API backend providing endpoints for query processing, PDF uploads, and system status.

- **`web/react-ui/src/App.jsx`**: Main React application component.

- **`web/react-ui/src/components/PolicyNavigator.jsx`**: Main Policy Navigator React component orchestrating the UI.

- **`web/react-ui/src/components/ChatWindow.jsx`**: Chat interface component for user interactions.

- **`web/react-ui/src/services/api.js`**: API client service for communicating with Flask backend.

#### Scripts

- **`scripts/initialize_rag.py`**: One-time script to process all documents from `data/` directory and populate ChromaDB vector store.

- **`scripts/run_pdf_mcp_server.py`**: Standalone script to run PDF MCP server for testing or external use.

## Installation

### Prerequisites

- Python 3.10 or higher (tested with Python 3.12.4)
- Virtual environment (recommended)

### Setup Steps

1. **Create virtual environment:**
   - Create a new virtual environment using `python -m venv venv`
   - Activate the virtual environment:
     - On Windows: `venv\Scripts\activate`
     - On macOS/Linux: `source venv/bin/activate`

2. **Install dependencies:**
   - Install all dependencies from `pyproject.toml` using: `pip install -e .`
   - This will install all required packages including CrewAI, ChromaDB, and MCP libraries

3. **Configure environment variables:**
   - Create a `.env` file in the project root directory
   - Add your API keys and configuration (see Environment Variables section below)

4. **Initialize RAG database:**
   - Run the initialization script: `python scripts/initialize_rag.py`
   - This processes documents from the `data/` directory and creates the vector database

## Environment Variables

### Required Environment Variables

At least one LLM provider API key is required:
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `GROQ_API_KEY` - Groq API key for Llama models

ADK agent API key (required for calculator agent):
- `GOOGLE_API_KEY` - Google Generative AI API key
- `GEMINI_API_KEY` - Alternative to GOOGLE_API_KEY (both work)

Ollama Web Search MCP (required for market and non-AP research agents):
- `OLLAMA_API_KEY` - Ollama API key for web search capabilities

### Optional but Recommended Environment Variables

LLM Configuration:
- `PRIMARY_LLM_PROVIDER` - Primary LLM provider: "openai" or "groq"
- `PRIMARY_LLM_MODEL` - Primary model name (e.g., "groq/llama-3.3-70b-versatile", "gpt-4o-mini")
- `FALLBACK_LLM_PROVIDER` - Fallback provider if primary fails
- `FALLBACK_LLM_MODEL` - Fallback model name

Embedding and Model Configuration:
- `EMBEDDING_MODEL` - Embedding model for RAG (default: "sentence-transformers/all-MiniLM-L6-v2")
- `ADK_MODEL` - Google Generative AI model for ADK agent (default: "gemini-pro")

PDF Processing:
- `USE_FASTMCP_PDF` - Enable FastMCP PDF extractor: "1" or "0" (default: "0" uses PyPDF2)

### Unused/Reserved Variables

These variables are not currently used but may be reserved for future features:
- `BRAVE_API_KEY` - Reserved for future Brave search integration
- `GOOGLE_CLOUD_PROJECT_ID` - Not needed (only for Vertex AI, not used)
- `GOOGLE_API_KEY_UNAUTHORIZED` - Typo, use `GOOGLE_API_KEY` instead
- `LANGCHAIN_*` - Reserved for future LangChain integration

## Usage

### Command Line Interface

Run the main script from the project root:
- `python src/policy_navigator/main.py`

This starts an interactive command-line interface where you can:
- Enter queries about agricultural policies, crop cultivation, pest management, or market information
- Upload PDF documents for analysis
- Get structured responses from the multi-agent system

### Web Interface

![Frontend UI](images/frontend-ui.png)

Start the Flask API server:
- Navigate to `web/api/` directory
- Run `python app.py` or use Flask's development server
- Access the React frontend at the configured port (typically http://localhost:5000)

The web interface provides:
- Interactive chat interface
- PDF upload functionality
- Real-time agent execution tracking
- System status monitoring
- Project mind map visualization

## MCP Integration

This project uses **Model Context Protocol (MCP)** servers for external tool integration:

### MCP Servers Configured

1. **Ollama Web Search MCP Server**
   - **Purpose**: Web search for real-time information
   - **Used by**: Market Analyst and Non-AP Researcher agents
   - **Tools**: `web_search` (for searching) and `web_fetch` (for fetching specific URLs)
   - **Configuration**: Requires `OLLAMA_API_KEY` environment variable
   - **Setup**: Sign up at https://ollama.com/ and add your API key to `.env`
   - **Note**: Ollama offers a free tier for web searches

2. **PDF MCP Server**
   - **Purpose**: PDF text extraction and document processing
   - **Used by**: PDF Processor Agent
   - **Implementation**: Two implementations available:
     - FastMCP PDF Extractor (pypdf) - Set `USE_FASTMCP_PDF=1`
     - Legacy PDF MCP Server (PyPDF2) - Default when `USE_FASTMCP_PDF=0`
   - **Features**: Page-by-page text extraction, markdown formatting, error handling

### MCP Benefits

- **Standardized Protocol**: MCP provides a standardized way to integrate external services
- **Automatic Discovery**: Tools are automatically discovered and integrated
- **Error Resilience**: Graceful handling of unavailable servers
- **Performance**: On-demand connections with schema caching

## System Workflow

The system follows a multi-stage workflow:

1. **User Query Input** - User submits a query through CLI or web interface

2. **Query Analyzer Agent** - First agent analyzes the query:
   - Uses Region Detector Tool to identify AP vs non-AP regions
   - Classifies query type (policy, cultivation, pest, market, document_upload)
   - Extracts entities (crops, schemes, locations, pests)
   - Determines which specialized agents should handle the request

3. **Conditional Task Routing** - System routes to appropriate agents based on analysis:
   - **RAG-Based Agents** (for AP queries): Policy Researcher, Crop Specialist, Pest Advisor
   - **MCP-Based Agents** (for real-time data): Market Analyst, Non-AP Researcher, PDF Processor
   - **ADK-Based Agent** (for calculations): Calculator Agent

4. **Specialized Agent Execution** - Selected agents execute their tasks:
   - RAG agents search local document database
   - MCP agents use web search or PDF processing
   - ADK agent performs calculations

5. **Response Synthesizer Agent** - Final agent synthesizes all outputs:
   - Aggregates context from all executed agents
   - Generates comprehensive markdown response
   - Distinguishes between local database data and web-searched data
   - Compiles sources and generates follow-up questions

6. **Structured Output** - Returns Pydantic model with:
   - Response text and markdown formatting
   - Sources and citations
   - Follow-up questions

## Agents

The system consists of **9 specialized agents**, each with distinct roles and capabilities:

### 1. Query Analyzer (CrewAI)
- **Role**: Query Understanding Specialist
- **Tools**: Region Detector Tool
- **Responsibilities**: Analyzes user queries, detects regions, classifies query type, extracts entities, determines agent routing
- **Output**: QueryAnalysis (Pydantic model) with required_agents list

### 2. Policy Researcher (CrewAI)
- **Role**: Agricultural Policy Expert
- **Tools**: RAG Document Search Tool
- **Responsibilities**: Retrieves agricultural schemes and policies, explains eligibility and benefits, provides PM-KISAN and PMFBY information
- **Output**: PolicyResponse (Pydantic model)

### 3. Crop Specialist (CrewAI)
- **Role**: Crop Cultivation Expert
- **Tools**: RAG Document Search Tool
- **Responsibilities**: Provides crop cultivation guidance, recommends varieties, provides sowing details, fertilizer schedules, irrigation schedules, economics
- **Output**: CropGuidance (Pydantic model)

### 4. Pest Advisor (CrewAI)
- **Role**: Pest Control Advisor
- **Tools**: RAG Document Search Tool
- **Responsibilities**: Identifies pests and diseases, provides IPM strategies, recommends control measures, advises on ETL and safe periods
- **Output**: PestManagement (Pydantic model)

### 5. Market Analyst (CrewAI)
- **Role**: Market & Weather Analyst
- **Tools**: Ollama Web Search MCP
- **Responsibilities**: Provides current MSP, fetches real-time market prices, provides weather conditions and forecasts, shares government announcements
- **Output**: MarketInfo (Pydantic model)

### 6. Non-AP Researcher (CrewAI)
- **Role**: Non-AP Region Web Research Specialist
- **Tools**: Ollama Web Search MCP
- **Responsibilities**: Searches web for agricultural information about non-AP regions, handles queries for other states, provides well-sourced information
- **Output**: WebSearchResponse (Pydantic model)

### 7. PDF Processor Agent (CrewAI)
- **Role**: PDF Document Processor
- **Tools**: PDF MCP Tool
- **Responsibilities**: Extracts text from uploaded PDFs, analyzes document content, generates summaries, validates domain, integrates with RAG system
- **Output**: PDFAnalysis (Pydantic model)

### 8. Response Synthesizer (CrewAI)
- **Role**: Response Synthesizer
- **Tools**: None (synthesizes from other agents)
- **Responsibilities**: Synthesizes comprehensive responses, creates markdown formatting, distinguishes data sources, compiles sources, handles out-of-scope queries
- **Output**: FinalResponse (Pydantic model)

### 9. Calculator Agent (ADK)
- **Role**: Agricultural Calculator
- **Framework**: Google ADK (Agent Development Kit)
- **Responsibilities**: Performs agricultural calculations using Google Generative AI, calculates cost of cultivation, yield, subsidy amounts, profit
- **Communication**: A2A Protocol via ADKAgentAdapter

## Tools

The system uses a combination of custom CrewAI tools, MCP tools, and ADK capabilities:

### CrewAI Custom Tools

#### RAG Document Search Tool
- **Purpose**: Semantic search through agricultural policy and crop information documents
- **Technology**: ChromaDB vector store with SentenceTransformer embeddings
- **Features**: Searches through documents across multiple categories, returns top relevant chunks with scores, supports category filtering
- **Used by**: Policy Researcher, Crop Specialist, Pest Advisor

#### Region Detector Tool
- **Purpose**: Detects if query mentions Andhra Pradesh or other regions
- **Technology**: Rule-based pattern matching with comprehensive region databases
- **Features**: Detects AP districts, cities, non-AP states and cities, returns structured JSON with region type
- **Used by**: Query Analyzer

### MCP Tools

#### Ollama Web Search MCP
- **Purpose**: Web search for real-time information
- **Technology**: Ollama API via Model Context Protocol
- **Features**: Provides current market prices, MSP, weather information, returns source URLs and timestamps
- **Used by**: Market Analyst, Non-AP Researcher
- **Configuration**: Requires `OLLAMA_API_KEY` environment variable

#### PDF MCP Tool
- **Purpose**: PDF text extraction and document processing
- **Technology**: PyPDF2/pypdf via MCP protocol
- **Features**: Extracts text page-by-page, supports both PyPDF2 and FastMCP implementations, provides formatted markdown
- **Used by**: PDF Processor Agent

### ADK Capabilities

#### Calculator Capabilities (via ADK Agent)
- **Purpose**: Agricultural financial calculations
- **Technology**: Google Generative AI (Gemini) via ADK
- **Capabilities**: Cost estimation, yield calculation, subsidy calculation, profit calculation
- **Communication**: A2A Protocol via StateManager
- **Used by**: Calculator Agent (ADK)

## A2A (Agent-to-Agent) Protocol Integration

This project implements A2A Protocol concepts for interoperability between CrewAI and Google ADK agents.

### Implementation Approach

The system uses an **adapter pattern** for local ADK agents:
- **ADKAgentAdapter**: Wraps Google ADK agents to work seamlessly with CrewAI agents
- **StateManager**: Acts as the A2A communication channel
- **A2AMessage**: Enhanced message format aligned with A2A Protocol standards
- **Task Delegation**: CrewAI agents can delegate tasks to ADK agents automatically

### A2A Protocol Features

1. **Task Delegation**: CrewAI agents delegate specialized tasks (calculations) to ADK agents with automatic routing
2. **Message Exchange**: Standardized message format with conversation tracking, status updates, and capability discovery
3. **Capability Discovery**: Agents expose capabilities enabling intelligent task routing
4. **Status Tracking**: Real-time status updates, error handling, and conversation history

### Architecture

The A2A communication flow:
- CrewAI Agent delegates task to ADKAgentAdapter
- ADKAgentAdapter communicates with ADK Agent (Google Gemini) via StateManager
- A2AMessage Exchange follows protocol-compliant format
- Results flow back through the adapter to CrewAI agent

### Why Adapter Pattern?

- **Local Agents**: Google ADK agents run locally (not as remote endpoints)
- **Simplicity**: No HTTP server setup required
- **Performance**: Direct in-process communication
- **Compliance**: Meets A2A Protocol requirements for interoperability

## Requirements Compliance

✅ **Context Sharing** - Via CrewAI memory and task context  
✅ **Tool Integration (MCP)** - Ollama Web Search MCP and PDF MCP implemented  
✅ **Structured Output** - Using Pydantic models for all agent responses  
✅ **Task Monitoring & Logging** - Comprehensive callbacks for tracking execution  
✅ **A2A Communication** - Via ADK integration with A2A Protocol alignment  
✅ **CrewAI/ADK Framework** - Primary CrewAI with ADK for calculator agent  

## License

MIT
