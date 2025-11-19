"""
Policy Navigator Crew
Main crew orchestration using CrewAI @CrewBase pattern
"""

import os
import sys
import logging
import warnings

# Suppress ChromaDB telemetry errors before CrewAI imports (CrewAI uses ChromaDB for memory)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = '1'

# Suppress ChromaDB deprecation warning about CHROMA_OPENAI_API_KEY (we use SentenceTransformer, not OpenAI)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='chromadb')
warnings.filterwarnings('ignore', message='.*CHROMA_OPENAI_API_KEY.*')
warnings.filterwarnings('ignore', message='.*legacy embedding function.*')
warnings.filterwarnings('ignore', message='.*Direct api_key configuration.*')
warnings.filterwarnings('ignore', message='.*will not be persisted.*')

# Suppress CrewAI internal deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, module='crewai')
warnings.filterwarnings('ignore', message='.*import_and_validate_definition.*')
warnings.filterwarnings('ignore', message='.*Use `crewai.utilities.import_utils.*')

# Create null handler for ChromaDB telemetry
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

null_handler = NullHandler()
logging.getLogger('chromadb.telemetry').addHandler(null_handler)
logging.getLogger('chromadb.telemetry').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry.product.posthog').addHandler(null_handler)
logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.ERROR)
logging.getLogger('chromadb').setLevel(logging.ERROR)
logging.getLogger('root').setLevel(logging.WARNING)

# Suppress CrewAI memory verbose logging to reduce noise
logging.getLogger('crewai.memory').setLevel(logging.WARNING)
logging.getLogger('crewai.rag').setLevel(logging.WARNING)
logging.getLogger('crewai.rag.storage').setLevel(logging.WARNING)
logging.getLogger('crewai.rag.chromadb').setLevel(logging.WARNING)

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput

# Note: Ollama Web Search tools are now direct tool wrappers (see ollama_websearch_tool.py)
# This is more reliable than using MCP subprocess servers

from typing import List

# Import guardrail factory
from policy_navigator.guardrails.guardrail_factory import create_guardrail
from policy_navigator.guardrails.guardrail_config import get_guardrail_llm
from policy_navigator.config.llm_config import get_llm_instance

# Import tools
from policy_navigator.tools.rag_tool import rag_tool
from policy_navigator.tools.region_detector import region_detector_tool
from policy_navigator.tools.pdf_mcp_tool import pdf_mcp_read_file

# Import Pydantic models for output_pydantic
from policy_navigator.models.schemas import (
    QueryAnalysis,
    PolicyResponse,
    CropGuidance,
    PestManagement,
    MarketInfo,
    FinalResponse,
    PDFAnalysis,
    WebSearchResponse
)

# Import callbacks
from policy_navigator.callbacks.monitoring import step_callback, task_callback

# Import ADK agent adapters (only calculator)
from policy_navigator.adk.adk_agent_adapter import (
    create_calculator_adapter,
    ADKAgentAdapter
)


# ============================================================================
# GUARDRAIL CONTEXT HELPERS
# ============================================================================

def get_rag_task_context() -> str:
    """Get context for RAG-based tasks (policy, crop, pest)"""
    return """Agricultural policy and crop information from Andhra Pradesh government documents and agricultural databases.
This includes schemes, policies, crop cultivation guides, and pest management information.
All information should be based on the RAG search results from the document database.
Outputs must be factual and directly supported by the retrieved documents."""

def get_web_search_task_context() -> str:
    """Get context for Ollama Web Search MCP tasks (market, non-AP)"""
    return """Real-time information from Ollama Web Search MCP results including market prices, MSP, weather, and agricultural information.
Information is obtained from Ollama Web Search MCP and may vary in reliability.
Outputs should be based on the Ollama Web Search MCP results and include source URLs.
All claims must be supported by the search results provided."""

def get_pdf_task_context() -> str:
    """Get context for PDF processing tasks"""
    return """Content extracted from uploaded PDF documents related to agricultural policies and Andhra Pradesh.
The PDF contains policy documents, scheme information, or agricultural guidelines.
Outputs must be based solely on the extracted PDF text content.
All information must be directly supported by the PDF content."""

def get_synthesis_task_context() -> str:
    """Get context for synthesis task"""
    return """Comprehensive response synthesizing information from multiple specialized agents.
The response combines policy research, crop guidance, pest management, market information, and other relevant data.
All information in the synthesis must be supported by the outputs from previous tasks.
The response should accurately represent the information from source tasks without adding unsupported claims."""

# ============================================================================
# QUERY ROUTING AND TASK DELEGATION LOGIC
# ============================================================================
# 
# The system uses a two-stage routing approach:
# 
# STAGE 1: Query Analysis (Always Executes First)
#   - query_analyzer agent analyzes the user query
#   - FIRST checks if query is out of scope (non-agricultural)
#   - If out of scope: sets required_agents = ["response_synthesizer"] and skips remaining steps
#   - If in scope: Uses region_detector_tool to detect AP/non-AP regions
#   - Classifies query type (policy, cultivation, pest, market, document_upload, etc.)
#   - Extracts entities (crops, schemes, locations, pests)
#   - Determines required_agents list based on query type and region
#   - Output: QueryAnalysis (Pydantic model)
# 
# STAGE 2: Conditional Task Execution
#   - Each specialized task checks if its agent is in required_agents
#   - If YES: Task executes fully with tools/MCP
#   - If NO: Task returns minimal structured output (still tracked)
#   - This ensures all agents are tracked but only needed ones do real work
# 
# ROUTING DECISIONS:
#   - document_upload → pdf_processor_agent (PDF MCP)
#   - policy queries + AP region → policy_researcher (RAG tool)
#   - cultivation queries + AP region → crop_specialist (RAG tool)
#   - pest queries + AP region → pest_advisor (RAG tool)
#   - market queries → market_analyst (Ollama Web Search MCP)
#   - non-AP or mixed regions → non_ap_researcher (Ollama Web Search MCP)
#   - calculation keywords → calculator_agent (ADK agent)
#   - Always → response_synthesizer (final synthesis)
# 
# A2A COMMUNICATION:
#   - calculator_agent (ADK) communicates with CrewAI agents via StateManager
#   - Uses A2A Protocol message format for interoperability
# ============================================================================

# Condition functions for conditional task execution
# These functions check query_analysis_task output from execution tracker
# since ConditionalTask only receives immediately previous task output

logger = logging.getLogger(__name__)

def get_query_analysis_from_tracker():
    """Get query_analysis_task output from execution tracker"""
    from policy_navigator.callbacks.execution_tracker import get_tracker
    tracker = get_tracker()
    # Query analysis is stored when query_analysis_task completes via task_callback
    return tracker.query_analysis

def _check_condition_with_fallback(agent_id: str, output: TaskOutput, query_analysis=None) -> bool:
    """
    Helper function to check if agent should run with fallback logic
    
    Args:
        agent_id: Agent ID to check (e.g., "pest_advisor")
        output: TaskOutput from previous task
        query_analysis: Optional pre-fetched query_analysis (to avoid multiple lookups)
    
    Returns:
        True if agent should run, False otherwise
    """
    # First try: Use query_analysis from tracker
    if query_analysis is None:
        query_analysis = get_query_analysis_from_tracker()
    
    if query_analysis:
        required_agents = getattr(query_analysis, 'required_agents', [])
        if not isinstance(required_agents, list):
            required_agents = []
        
        result = agent_id in required_agents
        logger.debug(f"Condition check for {agent_id}: {result} (required_agents: {required_agents})")
        return result
    
    # Fallback: Try to extract from previous task output if it's QueryAnalysis
    if output and hasattr(output, 'pydantic'):
        from policy_navigator.models.schemas import QueryAnalysis
        if isinstance(output.pydantic, QueryAnalysis):
            required_agents = getattr(output.pydantic, 'required_agents', [])
            if not isinstance(required_agents, list):
                required_agents = []
            result = agent_id in required_agents
            logger.debug(f"Condition check for {agent_id} (from output.pydantic): {result} (required_agents: {required_agents})")
            return result
    
    # Fallback: Try to extract from output.raw if it's a dict
    if output and hasattr(output, 'raw'):
        try:
            import json
            if isinstance(output.raw, str):
                raw_dict = json.loads(output.raw)
            elif isinstance(output.raw, dict):
                raw_dict = output.raw
            else:
                raw_dict = {}
            
            if 'required_agents' in raw_dict:
                required_agents = raw_dict['required_agents']
                if not isinstance(required_agents, list):
                    required_agents = []
                result = agent_id in required_agents
                logger.debug(f"Condition check for {agent_id} (from output.raw): {result} (required_agents: {required_agents})")
                return result
        except (json.JSONDecodeError, AttributeError):
            pass
    
    logger.warning(f"Condition check for {agent_id}: No query_analysis found, returning False")
    return False

def should_run_policy_research(output: TaskOutput) -> bool:
    """Check if policy_researcher agent should run based on query analysis"""
    return _check_condition_with_fallback("policy_researcher", output)

def should_run_crop_guidance(output: TaskOutput) -> bool:
    """Check if crop_specialist agent should run based on query analysis"""
    return _check_condition_with_fallback("crop_specialist", output)

def should_run_pest_management(output: TaskOutput) -> bool:
    """Check if pest_advisor agent should run based on query analysis"""
    return _check_condition_with_fallback("pest_advisor", output)

def should_run_market_info(output: TaskOutput) -> bool:
    """Check if market_analyst agent should run based on query analysis"""
    return _check_condition_with_fallback("market_analyst", output)

def should_run_non_ap_research(output: TaskOutput) -> bool:
    """Check if non_ap_researcher agent should run based on query analysis"""
    return _check_condition_with_fallback("non_ap_researcher", output)

def should_run_pdf_processing(output: TaskOutput) -> bool:
    """Check if PDF processing should run based on query analysis"""
    query_analysis = get_query_analysis_from_tracker()
    
    # Try fallback if query_analysis is None
    if not query_analysis and output and hasattr(output, 'pydantic'):
        from policy_navigator.models.schemas import QueryAnalysis
        if isinstance(output.pydantic, QueryAnalysis):
            query_analysis = output.pydantic
    
    if query_analysis:
        query_type = getattr(query_analysis, 'query_type', '')
        required_agents = getattr(query_analysis, 'required_agents', [])
        if not isinstance(required_agents, list):
            required_agents = []
        
        # Check multiple conditions
        is_document_upload = query_type == "document_upload"
        has_pdf_processor = "pdf_processor" in required_agents
        has_pdf_processor_agent = "pdf_processor_agent" in required_agents
        
        result = is_document_upload or has_pdf_processor or has_pdf_processor_agent
        
        logger.info(f"📄 PDF Processing Condition Check:")
        logger.info(f"   query_type: '{query_type}' (is_document_upload: {is_document_upload})")
        logger.info(f"   required_agents: {required_agents}")
        logger.info(f"   has 'pdf_processor': {has_pdf_processor}")
        logger.info(f"   has 'pdf_processor_agent': {has_pdf_processor_agent}")
        logger.info(f"   Result: {result} {'✅ WILL RUN' if result else '❌ WILL SKIP'}")
        
        if not result:
            logger.warning(f"⚠️ PDF processing will be SKIPPED. Check query_analysis output:")
            logger.warning(f"   - query_type should be 'document_upload' but got: '{query_type}'")
            logger.warning(f"   - required_agents should contain 'pdf_processor' or 'pdf_processor_agent' but got: {required_agents}")
        
        return result
    
    logger.warning("Condition check for pdf_processing: No query_analysis found, returning False")
    logger.warning("   This means query_analysis_task may not have completed or output was not captured")
    return False

def should_run_calculation(output: TaskOutput) -> bool:
    """Check if calculation should run based on query analysis"""
    query_analysis = get_query_analysis_from_tracker()
    
    # Try fallback if query_analysis is None
    if not query_analysis and output and hasattr(output, 'pydantic'):
        from policy_navigator.models.schemas import QueryAnalysis
        if isinstance(output.pydantic, QueryAnalysis):
            query_analysis = output.pydantic
    
    if query_analysis:
        required_agents = getattr(query_analysis, 'required_agents', [])
        if not isinstance(required_agents, list):
            required_agents = []
        
        # Check if calculator is in required_agents
        if "calculator" in required_agents or "calculator_agent" in required_agents:
            logger.debug(f"Condition check for calculation: True (found in required_agents: {required_agents})")
            return True
        
        # Check query for calculation keywords
        original_query = getattr(query_analysis, 'original_query', '')
        query_lower = original_query.lower() if original_query else ''
        calculation_keywords = ["calculate", "cost", "yield", "subsidy", "profit", "revenue", "area", "hectare"]
        result = any(keyword in query_lower for keyword in calculation_keywords)
        logger.debug(f"Condition check for calculation: {result} (query: {original_query[:50]}...)")
        return result
    
    logger.warning("Condition check for calculation: No query_analysis found, returning False")
    return False


@CrewBase
class PolicyNavigatorCrew:
    """
    Policy Navigator Crew - Main orchestration class
    
    Organizes 8 specialized agents (7 CrewAI + 1 ADK) working collaboratively:
    - Query routing and analysis
    - Policy research (RAG-based)
    - Crop cultivation guidance (RAG-based)
    - Pest management (RAG-based)
    - Market information (MCP-based)
    - Non-AP research (MCP-based)
    - PDF processing (MCP-based)
    - Response synthesis
    - Calculations (ADK-based)
    """
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    agents: List[BaseAgent]
    tasks: List[Task]
    
    # ========================================================================
    # CREWAI AGENTS - Query Analysis and Routing
    # ========================================================================
    
    @agent
    def query_analyzer(self) -> Agent:
        """Query Understanding Agent"""
        return Agent(
            config=self.agents_config['query_analyzer'],  # type: ignore[index]
            verbose=True,
            tools=[region_detector_tool]
        )
    
    # ========================================================================
    # CREWAI AGENTS - RAG-Based Information Retrieval
    # ========================================================================
    
    @agent
    def policy_researcher(self) -> Agent:
        """Agricultural Policy Expert Agent"""
        return Agent(
            config=self.agents_config['policy_researcher'],  # type: ignore[index]
            verbose=True,
            tools=[rag_tool]
        )
    
    @agent
    def crop_specialist(self) -> Agent:
        """Crop Cultivation Expert Agent"""
        return Agent(
            config=self.agents_config['crop_specialist'],  # type: ignore[index]
            verbose=True,
            tools=[rag_tool]
        )
    
    @agent
    def pest_advisor(self) -> Agent:
        """Pest Control Advisor Agent"""
        return Agent(
            config=self.agents_config['pest_advisor'],  # type: ignore[index]
            verbose=True,
            tools=[rag_tool]
        )
    
    # ========================================================================
    # CREWAI AGENTS - MCP-Based Search (Ollama Web Search MCP)
    # ========================================================================
    
    @agent
    def market_analyst(self) -> Agent:
        """Market & Weather Analyst Agent"""
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        
        if ollama_api_key:
            # Use direct tool wrappers (more reliable than MCP subprocess)
            from policy_navigator.tools.ollama_websearch_tool import web_search, web_fetch
            tools = [web_search, web_fetch]
            logger.info(f"✓ Market Analyst: Ollama Web Search tools configured (direct tools, API key length: {len(ollama_api_key)})")
            logger.info(f"  Tools: web_search, web_fetch")
        else:
            logger.warning("⚠ Market Analyst: OLLAMA_API_KEY not found - Ollama Web Search tools unavailable")
            tools = []
        
        try:
            agent = Agent(
                config=self.agents_config['market_analyst'],  # type: ignore[index]
                verbose=True,
                tools=tools if tools else None
            )
            
            # Verify tools are available
            if tools:
                if hasattr(agent, 'tools') and agent.tools:
                    tool_count = len(agent.tools) if isinstance(agent.tools, (list, tuple)) else 1
                    tool_names = [getattr(t, 'name', str(t)) for t in (agent.tools if isinstance(agent.tools, (list, tuple)) else [agent.tools])]
                    logger.info(f"  ✅ Verified: Agent has {tool_count} tool(s): {', '.join(tool_names[:5])}")
                else:
                    logger.warning("  ⚠ Agent tools not immediately available (may be lazy-loaded)")
            
            return agent
        except Exception as e:
            logger.error(f"❌ Market Analyst: Failed to create agent: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: create agent without tools
            return Agent(
                config=self.agents_config['market_analyst'],  # type: ignore[index]
                verbose=True
            )
    
    @agent
    def non_ap_researcher(self) -> Agent:
        """Non-AP Region Web Research Specialist Agent"""
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        
        if ollama_api_key:
            # Use direct tool wrappers (more reliable than MCP subprocess)
            from policy_navigator.tools.ollama_websearch_tool import web_search, web_fetch
            tools = [web_search, web_fetch]
            logger.info(f"✓ Non-AP Researcher: Ollama Web Search tools configured (direct tools, API key length: {len(ollama_api_key)})")
            logger.info(f"  Tools: web_search, web_fetch")
        else:
            logger.warning("⚠ Non-AP Researcher: OLLAMA_API_KEY not found - Ollama Web Search tools unavailable")
            tools = []
        
        try:
            agent = Agent(
                config=self.agents_config['non_ap_researcher'],  # type: ignore[index]
                verbose=True,
                tools=tools if tools else None
            )
            
            # Verify tools are available
            if tools:
                if hasattr(agent, 'tools') and agent.tools:
                    tool_count = len(agent.tools) if isinstance(agent.tools, (list, tuple)) else 1
                    tool_names = [getattr(t, 'name', str(t)) for t in (agent.tools if isinstance(agent.tools, (list, tuple)) else [agent.tools])]
                    logger.info(f"  ✅ Verified: Agent has {tool_count} tool(s): {', '.join(tool_names[:5])}")
                else:
                    logger.warning("  ⚠ Agent tools not immediately available (may be lazy-loaded)")
            
            return agent
        except Exception as e:
            logger.error(f"❌ Non-AP Researcher: Failed to create agent: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: create agent without tools
            return Agent(
                config=self.agents_config['non_ap_researcher'],  # type: ignore[index]
                verbose=True
            )
    
    # ========================================================================
    # CREWAI AGENTS - Response Synthesis
    # ========================================================================
    
    @agent
    def response_synthesizer(self) -> Agent:
        """Response Synthesizer Agent"""
        return Agent(
            config=self.agents_config['response_synthesizer'],  # type: ignore[index]
            verbose=True
        )
    
    # ========================================================================
    # CREWAI AGENTS - MCP-Based PDF Processing
    # ========================================================================
    
    @agent
    def pdf_processor_agent(self) -> Agent:
        """
        PDF Processor Agent - CrewAI agent with PDF MCP tool
        
        Uses PDF MCP tool for text extraction and document processing.
        The tool implements MCP-compatible PDF reading capabilities.
        """
        # Use PDF MCP tool directly (implements MCP protocol concepts)
        # This provides PDF reading capabilities without requiring external MCP server
        return Agent(
            config=self.agents_config['pdf_processor_agent'],  # type: ignore[index]
            verbose=True,
            tools=[pdf_mcp_read_file]  # PDF MCP tool for text extraction
        )
    
    # ========================================================================
    # ADK AGENTS - A2A Communication
    # ========================================================================
    
    @agent
    def calculator_agent(self) -> ADKAgentAdapter:
        """Calculator ADK Agent"""
        return create_calculator_adapter(
            agent_config=self.agents_config.get('calculator_agent')  # type: ignore[index]
        )
    
    @task
    def query_analysis_task(self) -> Task:
        """Query Analysis Task"""
        return Task(
            config=self.tasks_config['query_analysis_task'],  # type: ignore[index]
            output_pydantic=QueryAnalysis
        )
    
    @task
    def pdf_processing_task(self) -> ConditionalTask:
        """PDF Processing Task - Conditional on PDF upload"""
        # Create guardrail for PDF processing
        guardrail = create_guardrail(
            context=get_pdf_task_context(),
            task_name="pdf_processing_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['pdf_processing_task'],  # type: ignore[index]
            condition=should_run_pdf_processing,
            output_pydantic=PDFAnalysis,
            guardrail=guardrail
        )
    
    @task
    def calculation_task(self) -> ConditionalTask:
        """Calculation Task - Conditional on calculation needs"""
        return ConditionalTask(
            config=self.tasks_config['calculation_task'],  # type: ignore[index]
            condition=should_run_calculation
        )
    
    @task
    def policy_research_task(self) -> ConditionalTask:
        """Policy Research Task - Conditional"""
        # Create guardrail for RAG-based policy research
        guardrail = create_guardrail(
            context=get_rag_task_context(),
            task_name="policy_research_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['policy_research_task'],  # type: ignore[index]
            condition=should_run_policy_research,
            output_pydantic=PolicyResponse,
            guardrail=guardrail
        )
    
    @task
    def crop_guidance_task(self) -> ConditionalTask:
        """Crop Guidance Task - Conditional"""
        # Create guardrail for RAG-based crop guidance
        guardrail = create_guardrail(
            context=get_rag_task_context(),
            task_name="crop_guidance_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['crop_guidance_task'],  # type: ignore[index]
            condition=should_run_crop_guidance,
            output_pydantic=CropGuidance,
            guardrail=guardrail
        )
    
    @task
    def pest_management_task(self) -> ConditionalTask:
        """Pest Management Task - Conditional"""
        # Create guardrail for RAG-based pest management
        guardrail = create_guardrail(
            context=get_rag_task_context(),
            task_name="pest_management_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['pest_management_task'],  # type: ignore[index]
            condition=should_run_pest_management,
            output_pydantic=PestManagement,
            guardrail=guardrail
        )
    
    @task
    def market_info_task(self) -> ConditionalTask:
        """Market Information Task - Conditional"""
        # Create guardrail for Ollama Web Search MCP-based market information
        guardrail = create_guardrail(
            context=get_web_search_task_context(),
            task_name="market_info_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['market_info_task'],  # type: ignore[index]
            condition=should_run_market_info,
            output_pydantic=MarketInfo,
            guardrail=guardrail
        )
    
    @task
    def non_ap_research_task(self) -> ConditionalTask:
        """Non-AP Research Task - Conditional on non-AP region detection"""
        # Create guardrail for Ollama Web Search MCP-based non-AP research
        guardrail = create_guardrail(
            context=get_web_search_task_context(),
            task_name="non_ap_research_task",
            llm=get_guardrail_llm()
        )
        return ConditionalTask(
            config=self.tasks_config['non_ap_research_task'],  # type: ignore[index]
            condition=should_run_non_ap_research,
            output_pydantic=WebSearchResponse,
            guardrail=guardrail
        )
    
    @task
    def synthesis_task(self) -> Task:
        """Response Synthesis Task"""
        # Create guardrail for synthesis task
        guardrail = create_guardrail(
            context=get_synthesis_task_context(),
            task_name="synthesis_task",
            llm=get_guardrail_llm()
        )
        return Task(
            config=self.tasks_config['synthesis_task'],  # type: ignore[index]
            output_pydantic=FinalResponse,
            guardrail=guardrail
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Creates the Policy Navigator crew with sequential process execution.
        
        Execution Order (Sequential Process):
        1. query_analysis_task (always runs) - Analyzes query, detects region, determines required agents
        2. pdf_processing_task (always runs) - Checks if PDF needed, processes or returns minimal output
        3. policy_research_task (always runs) - Checks if needed, researches or returns minimal output
        4. crop_guidance_task (always runs) - Checks if needed, provides guidance or returns minimal output
        5. pest_management_task (always runs) - Checks if needed, manages pests or returns minimal output
        6. market_info_task (always runs) - Checks if needed, fetches info or returns minimal output
        7. non_ap_research_task (always runs) - Checks if needed, web searches or returns minimal output
        8. synthesis_task (always runs) - Synthesizes final response from all previous tasks
        
        Task Behavior:
        - All tasks are regular Tasks (not ConditionalTasks) for simplicity and reliability
        - Each specialized task checks query_analysis_task output (available via context parameter)
        - If agent not in required_agents, task returns minimal structured output
        - If agent is needed, task executes fully with tools
        - This ensures all agents execute and are tracked, but only needed ones do real work
        
        Context Sharing:
        - All tasks have access to query_analysis_task output via 'context' parameter in tasks.yaml
        - CrewAI memory enables agent-to-agent context sharing
        """
        # Configure LLM from environment variables
        try:
            crew_llm = get_llm_instance(use_fallback=False)
            logger.info("✓ Crew LLM configured from PRIMARY_LLM_PROVIDER/MODEL")
        except Exception as e:
            logger.warning(f"⚠ Failed to configure PRIMARY LLM, trying fallback: {e}")
            try:
                crew_llm = get_llm_instance(use_fallback=True)
                logger.info("✓ Crew LLM configured from FALLBACK_LLM_PROVIDER/MODEL")
            except Exception as e2:
                logger.warning(f"⚠ Failed to configure FALLBACK LLM, using auto-detection: {e2}")
                crew_llm = get_llm_instance(use_fallback=False, default_model="gpt-4o-mini")
        
        # Verify OLLAMA_API_KEY is available for MCP agents
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        if ollama_api_key:
            logger.info(f"✓ OLLAMA_API_KEY found in environment (length: {len(ollama_api_key)})")
            logger.debug(f"  API Key starts with: {ollama_api_key[:8]}...")
            
            # Test if MCP server can be imported and started
            try:
                import subprocess
                import sys
                test_cmd = [sys.executable, "-m", "mcp_servers.ollama_websearch_mcp_server", "--help"]
                result = subprocess.run(
                    test_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={"OLLAMA_API_KEY": ollama_api_key, **os.environ}
                )
                logger.info(f"✓ MCP server module can be imported and executed")
            except subprocess.TimeoutExpired:
                logger.warning("⚠ MCP server test timed out (this is normal if server waits for stdio)")
            except Exception as e:
                logger.warning(f"⚠ Could not test MCP server: {e}")
                logger.warning(f"  This may indicate the MCP server module is not accessible")
        else:
            logger.warning("⚠ OLLAMA_API_KEY not found in environment variables!")
            logger.warning("  Market Analyst and Non-AP Researcher agents will not have Ollama Web Search MCP capabilities.")
            logger.warning("  Please set OLLAMA_API_KEY in your .env file.")
        
        # Memory configuration: Optimized for performance
        # - Disable memory for PDF upload queries to avoid context length errors
        # - Use optimized memory settings for faster execution
        # - Reduce verbosity for synthesis task (configured in agents.yaml)
        enable_memory = os.getenv("ENABLE_CREWAI_MEMORY", "true").lower() == "true"
        
        if enable_memory:
            logger.info("✓ CrewAI memory enabled for context sharing (optimized for performance)")
            logger.info("  Note: Memory may be disabled for large PDF uploads to avoid token limit errors")
            logger.info("  Note: Synthesis task verbosity reduced to minimize memory update noise")
            # Memory is enabled with default optimized settings
            # CrewAI will use efficient embedding models automatically
        else:
            logger.info("⚠ CrewAI memory disabled (set ENABLE_CREWAI_MEMORY=false)")
        
        return Crew(
            agents=self.agents,  # Automatically collected by @agent decorator
            tasks=self.tasks,    # Automatically collected by @task decorator
            process=Process.sequential,  # Sequential execution - tasks run in order
            verbose=True,
            memory=enable_memory,  # Enable memory conditionally (optimized for performance)
            llm=crew_llm,  # Use LLM from environment variables (PRIMARY_LLM_PROVIDER/MODEL)
            step_callback=step_callback,  # Step-level monitoring (tracks tool usage)
            task_callback=task_callback,  # Task-level monitoring (tracks agent execution)
        )

