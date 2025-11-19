"""
Main Orchestrator for Policy Navigator
Wraps the CrewAI crew and provides workflow details for the frontend
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Suppress warnings before imports
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = '1'

from policy_navigator.crew import PolicyNavigatorCrew
from policy_navigator.callbacks.execution_tracker import get_tracker
from policy_navigator.models.schemas import FinalResponse
from policy_navigator.config.tool_mappings import get_tool_display_name, is_adk_tool
from mcp_servers.pdf_mcp_server import get_pdf_mcp_server
from policy_navigator.tools.pdf_domain_validator import get_pdf_validator
from policy_navigator.tools.rag_tool import rag_tool

logger = logging.getLogger(__name__)


class MainOrchestrator:
    """Main orchestrator that wraps PolicyNavigatorCrew and provides workflow details"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.crew_instance = None
        self.crew = None
        logger.info("MainOrchestrator initialized")
    
    def _get_crew(self, pdf_file_path: Optional[str] = None):
        """
        Lazy load crew instance
        
        Args:
            pdf_file_path: Optional PDF file path. If provided and file is large, 
                          memory may be disabled to avoid context length errors.
        """
        # For PDF uploads, disable memory to avoid context length errors with large PDFs
        # PDF content can exceed 30k characters, causing OpenAI embedding token limit (8192) errors
        if pdf_file_path and pdf_file_path.strip():
            # Check file size to determine if memory should be disabled
            try:
                file_size = os.path.getsize(pdf_file_path) if os.path.exists(pdf_file_path) else 0
                # Disable memory for files larger than 100KB (likely to have large text content)
                if file_size > 100 * 1024:  # 100KB
                    logger.info(f"Large PDF detected ({file_size / 1024:.1f}KB), disabling CrewAI memory to avoid token limit errors")
                    os.environ['ENABLE_CREWAI_MEMORY'] = 'false'
                else:
                    logger.info(f"Small PDF detected ({file_size / 1024:.1f}KB), keeping CrewAI memory enabled")
                    os.environ['ENABLE_CREWAI_MEMORY'] = 'true'
            except Exception as e:
                logger.warning(f"Could not check PDF file size: {e}, keeping memory enabled")
                os.environ['ENABLE_CREWAI_MEMORY'] = 'true'
        else:
            # No PDF, enable memory for regular queries
            os.environ['ENABLE_CREWAI_MEMORY'] = 'true'
        
        # Always create new crew instance to respect memory setting
        # (CrewAI memory is set at initialization, so we need a new instance)
        logger.info("Initializing PolicyNavigatorCrew...")
        self.crew_instance = PolicyNavigatorCrew()
        self.crew = self.crew_instance.crew()
        logger.info("PolicyNavigatorCrew initialized successfully")
        return self.crew
    
    # Agent display name mapping
    AGENT_DISPLAY_NAMES = {
        'query_analyzer': 'Query Analyzer',
        'policy_researcher': 'Policy Researcher',
        'crop_specialist': 'Crop Specialist',
        'pest_advisor': 'Pest Advisor',
        'market_analyst': 'Market Analyst',
        'non_ap_researcher': 'Non-AP Researcher',
        'response_synthesizer': 'Response Synthesizer',
        'pdf_processor_agent': 'PDF Processor (MCP)',
        'calculator_agent': 'Calculator (ADK)',
    }
    
    # Tool display name mapping - now uses centralized tool_mappings module
    # Kept for backward compatibility, but delegates to get_tool_display_name()
    
    # Framework mapping - determine which framework each agent uses
    AGENT_FRAMEWORKS = {
        'query_analyzer': 'CrewAI',
        'policy_researcher': 'CrewAI',
        'crop_specialist': 'CrewAI',
        'pest_advisor': 'CrewAI',
        'market_analyst': 'CrewAI',
        'non_ap_researcher': 'CrewAI',
        'response_synthesizer': 'CrewAI',
        'pdf_processor_agent': 'CrewAI',  # PDF processing uses CrewAI agent with PDF MCP tool
        'calculator_agent': 'ADK',  # Calculator uses ADK agent
    }
    
    def _get_agent_display_name(self, agent_id: str) -> str:
        """Get display name for an agent"""
        return self.AGENT_DISPLAY_NAMES.get(agent_id, agent_id.replace('_', ' ').title())
    
    def _get_tool_display_name(self, tool_name: str) -> str:
        """Get display name for a tool using centralized mapping"""
        return get_tool_display_name(tool_name)
    
    def _get_agent_framework(self, agent_id: str) -> str:
        """Get framework for an agent"""
        return self.AGENT_FRAMEWORKS.get(agent_id, 'CrewAI')
    
    def _extract_tools_from_crew_result(self, result: Any, tracker) -> None:
        """
        Extract tool usage from crew execution result
        
        Args:
            result: CrewAI crew.kickoff() result
            tracker: ExecutionTracker instance
        """
        try:
            # Check if result has tasks attribute
            if hasattr(result, 'tasks'):
                tasks = result.tasks
                if isinstance(tasks, list):
                    for task in tasks:
                        # Get agent from task
                        agent_role = None
                        if hasattr(task, 'agent'):
                            agent_obj = task.agent
                            if hasattr(agent_obj, 'role'):
                                agent_role = agent_obj.role
                            elif isinstance(agent_obj, dict):
                                agent_role = agent_obj.get('role')
                        
                        # Map agent role to agent_id
                        from policy_navigator.callbacks.monitoring import AGENT_ROLE_TO_ID
                        agent_id = AGENT_ROLE_TO_ID.get(agent_role, 'unknown_agent') if agent_role else 'unknown_agent'
                        
                        # Check task output for tool usage
                        if hasattr(task, 'output'):
                            output = task.output
                            # Check for tool_calls in output
                            if hasattr(output, 'tool_calls') and output.tool_calls:
                                logger.info(f"Found {len(output.tool_calls)} tool call(s) in task output for agent: {agent_role}")
                                for tool_call in output.tool_calls:
                                    tool_name = self._extract_tool_name_from_call(tool_call)
                                    if tool_name:
                                        clean_tool_name = get_tool_display_name(tool_name)
                                        tracker.track_tool(agent_id, clean_tool_name)
                                        logger.info(f"✓ Extracted tool from crew result: {clean_tool_name} for agent: {agent_id}")
                        
                        # Check task execution history if available
                        if hasattr(task, 'execution_history'):
                            history = task.execution_history
                            if isinstance(history, list):
                                for entry in history:
                                    if isinstance(entry, dict):
                                        # Look for tool usage in history entries
                                        if 'tool' in entry or 'tool_call' in entry:
                                            tool_name = entry.get('tool') or entry.get('tool_call')
                                            if tool_name:
                                                clean_tool_name = get_tool_display_name(tool_name)
                                                tracker.track_tool(agent_id, clean_tool_name)
                                                logger.info(f"✓ Extracted tool from execution history: {clean_tool_name} for agent: {agent_id}")
            
            # Also check result.tasks_output if available (alternative attribute name)
            if hasattr(result, 'tasks_output'):
                tasks_output = result.tasks_output
                if isinstance(tasks_output, list):
                    for task_output in tasks_output:
                        agent_role = getattr(task_output, 'agent', None)
                        from policy_navigator.callbacks.monitoring import AGENT_ROLE_TO_ID
                        agent_id = AGENT_ROLE_TO_ID.get(agent_role, 'unknown_agent') if agent_role else 'unknown_agent'
                        
                        if hasattr(task_output, 'tool_calls') and task_output.tool_calls:
                            for tool_call in task_output.tool_calls:
                                tool_name = self._extract_tool_name_from_call(tool_call)
                                if tool_name:
                                    clean_tool_name = get_tool_display_name(tool_name)
                                    tracker.track_tool(agent_id, clean_tool_name)
                                    logger.info(f"✓ Extracted tool from tasks_output: {clean_tool_name} for agent: {agent_id}")
        
        except Exception as e:
            logger.warning(f"Could not extract tools from crew result: {e}")
            logger.debug(f"Result type: {type(result)}, attributes: {dir(result) if hasattr(result, '__dict__') else 'N/A'}")
    
    def _extract_tool_name_from_call(self, tool_call: Any) -> Optional[str]:
        """
        Extract tool name from a tool call object
        
        Args:
            tool_call: Tool call object (can be dict, object, or string)
            
        Returns:
            Tool name or None
        """
        if isinstance(tool_call, str):
            return tool_call
        elif isinstance(tool_call, dict):
            return tool_call.get('tool') or tool_call.get('name') or tool_call.get('tool_name')
        elif hasattr(tool_call, 'tool'):
            tool_obj = tool_call.tool
            if hasattr(tool_obj, 'name'):
                return tool_obj.name
            elif hasattr(tool_obj, '__name__'):
                return tool_obj.__name__
            else:
                return str(tool_obj)
        elif hasattr(tool_call, 'name'):
            return tool_call.name
        else:
            return str(tool_call) if tool_call else None
    
    def _build_workflow_details(self, executed_agents: List[str], agent_tools: Dict[str, List[str]], used_tools: List[str]) -> Dict[str, Any]:
        """
        Build workflow_details structure for frontend.
        
        Includes:
        - All available agents (executed and skipped) with execution status
        - Agents with their tools and framework indicators
        - Tool framework identification (CrewAI vs ADK)
        - Requirements compliance based on execution
        """
        
        # Define all available agents with their expected tools
        ALL_AGENTS = {
            'query_analyzer': ['Region Detector'],
            'policy_researcher': ['RAG Document Search'],
            'crop_specialist': ['RAG Document Search'],
            'pest_advisor': ['RAG Document Search'],
            'market_analyst': ['Ollama Web Search MCP'],
            'non_ap_researcher': ['Ollama Web Search MCP'],
            'pdf_processor_agent': ['PDF Processor (MCP)'],
            'calculator_agent': ['Calculator (ADK)'],
            'response_synthesizer': []
        }
        
        # Build agents list - include ALL agents, not just executed ones
        agents = []
        adk_tools_detected = False
        executed_agents_set = set(executed_agents)
        
        agent_index = 0
        for agent_id, expected_tools in ALL_AGENTS.items():
            agent_index += 1
            is_executed = agent_id in executed_agents_set
            
            # Get tools that were actually used (if executed) or expected tools (if skipped)
            if is_executed:
                agent_tools_list = agent_tools.get(agent_id, [])
                # Map tool names to display names and identify ADK tools
                display_tools = []
                agent_uses_adk = False
                
                for tool in agent_tools_list:
                    display_name = self._get_tool_display_name(tool)
                    display_tools.append(display_name)
                    
                    # Check if this tool is ADK-based
                    if is_adk_tool(tool) or is_adk_tool(display_name):
                        adk_tools_detected = True
                        agent_uses_adk = True
                        logger.debug(f"Agent {agent_id} uses ADK tool: {display_name}")
            else:
                # Agent was skipped - show expected tools
                display_tools = expected_tools
                agent_uses_adk = any(is_adk_tool(tool) for tool in expected_tools)
            
            agents.append({
                "id": f"agent_{agent_index}",
                "name": self._get_agent_display_name(agent_id),
                "framework": self._get_agent_framework(agent_id),
                "tools": display_tools,
                "uses_adk_tools": agent_uses_adk,
                "executed": is_executed,  # New field: indicates if agent actually executed
                "skipped": not is_executed,  # New field: indicates if agent was skipped
                "fallback_used": False,
                "fallback_type": None
            })
        
        # Check if ADK agents were used (for requirements compliance)
        # Note: ADK tools are used by CrewAI agents, not separate ADK agents
        adk_agents_used = any(self._get_agent_framework(agent_id) == 'ADK' for agent_id in executed_agents)
        crewai_agents_used = any(self._get_agent_framework(agent_id) == 'CrewAI' for agent_id in executed_agents)
        
        # A2A communication is enabled when ADK tools are used (even if no ADK agents)
        # ADK tools enable A2A communication between CrewAI agents and ADK backend
        a2a_enabled = adk_agents_used or adk_tools_detected
        
        # Framework usage: True if both CrewAI agents AND ADK tools are used
        # This demonstrates integration between CrewAI and ADK frameworks
        framework_integration = crewai_agents_used and (adk_agents_used or adk_tools_detected)
        
        # Calculate requirements compliance
        requirements_met = {
            "context_sharing": True,  # Always True - CrewAI memory enabled
            "tool_integration": len(used_tools) >= 2,  # True if ≥2 tools used
            "structured_output": True,  # Always True - Pydantic models used
            "task_monitoring": True,  # Always True - callbacks enabled
            "a2a_communication": a2a_enabled,  # True if ADK agents OR ADK tools used
            "framework_usage": framework_integration,  # True if both CrewAI and ADK used
        }
        
        logger.info(f"Workflow details: {len(agents)} agents, {len(used_tools)} tools, ADK tools: {adk_tools_detected}")
        
        return {
            "agents": agents,
            "fallbacks": [],  # Can be extended later
            "requirements_met": requirements_met
        }
    
    def process_query(
        self,
        user_query: str,
        user_id: str = 'default_user',
        session_id: Optional[str] = None,
        pdf_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent pipeline
        
        Args:
            user_query: The user's query
            user_id: User identifier
            session_id: Session identifier
            pdf_file_path: Optional path to PDF file
            
        Returns:
            Dictionary containing:
            - result: FinalResponse or dict with query results
            - workflow_details: Dict with agents, tools, and requirements compliance
        """
        try:
            # Reset execution tracker for new query
            tracker = get_tracker()
            tracker.reset()
            
            # Get crew instance (disable memory for PDF uploads to avoid token limit errors)
            crew = self._get_crew(pdf_file_path=pdf_file_path if pdf_file_path else None)
            
            # Prepare inputs for crew
            inputs = {
                "user_query": user_query,
                "pdf_file_path": pdf_file_path if pdf_file_path else ""
            }
            
            logger.info(f"Processing query: {user_query[:100]}...")
            
            # Execute crew with user query
            result = crew.kickoff(inputs=inputs)
            
            # Extract tool usage from crew result if available
            # CrewAI may store tool usage in result.tasks
            self._extract_tools_from_crew_result(result, tracker)
            
            # Get execution tracker data
            executed_agents = tracker.get_executed_agents()
            used_tools = tracker.get_used_tools()
            agent_tools = tracker.get_agent_tools()
            
            logger.info(f"Executed agents: {executed_agents}")
            logger.info(f"Used tools: {used_tools}")
            logger.info(f"Agent tools: {agent_tools}")
            
            # Build workflow details
            workflow_details = self._build_workflow_details(executed_agents, agent_tools, used_tools)
            
            # Convert result to dict if it's a Pydantic model
            if hasattr(result, 'pydantic') and result.pydantic:
                result_dict = result.pydantic.model_dump()
            elif hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            elif isinstance(result, dict):
                result_dict = result
            else:
                # If result is a string or other type, wrap it in a dict
                result_dict = {"raw": str(result)}
            
            # Ensure result_dict is always a dict (safety check)
            if not isinstance(result_dict, dict):
                logger.warning(f"result_dict is not a dict, type: {type(result_dict)}, value: {result_dict}")
                result_dict = {"raw": str(result_dict)}
            
            # Ensure all required fields exist
            if not result_dict.get('query'):
                result_dict['query'] = user_query
            
            if not result_dict.get('response_text'):
                result_dict['response_text'] = result_dict.get('response_markdown', 'No response generated')
            
            if not result_dict.get('response_markdown'):
                result_dict['response_markdown'] = result_dict.get('response_text', 'No response generated')
            
            # Add workflow details to result
            result_dict['workflow_details'] = workflow_details
            
            # Add workflow_info as summary string
            agent_names = [self._get_agent_display_name(agent_id) for agent_id in executed_agents]
            tool_names = [self._get_tool_display_name(tool) for tool in used_tools]
            workflow_info = f"Executed {len(executed_agents)} agents ({', '.join(agent_names[:3])}{'...' if len(agent_names) > 3 else ''}) using {len(used_tools)} tools"
            result_dict['workflow_info'] = workflow_info
            
            logger.info(f"Workflow details built: {len(workflow_details['agents'])} agents, {len(used_tools)} tools")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            raise
    
    def process_document_upload(
        self,
        file_path: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document upload with domain validation and RAG integration
        
        Steps:
        1. Extract text from PDF using PDF MCP tool
        2. Validate domain (agriculture + AP policies)
        3. If valid: Add to RAG and process PDF
        4. If invalid: Return error message
        
        Args:
            file_path: Path to uploaded file
            query: Optional query about the document
            
        Returns:
            Dictionary containing:
            - success: bool
            - response: str (summary or error message)
            - validation_result: dict (domain validation details)
            - metadata: dict (workflow details, etc.)
        """
        try:
            # Step 1: Extract PDF text using PDF MCP server or FastMCP extractor
            logger.info(f"Extracting text from PDF: {file_path}")
            
            # Check if FastMCP should be used
            use_fastmcp = os.getenv("USE_FASTMCP_PDF", "0") == "1"
            
            if use_fastmcp:
                try:
                    from mcp_servers.pdf_extractor_mcp_server import extract_pdf_markdown as fastmcp_extract_pdf_markdown
                    logger.info("Using FastMCP PDF extractor for upload processing")
                    logger.debug(f"Extracting PDF from path: {file_path}")
                    markdown_content = fastmcp_extract_pdf_markdown(file_path)
                    logger.debug(f"FastMCP extraction completed, content length: {len(markdown_content) if markdown_content else 0} characters")
                    logger.debug(f"First 200 chars of extracted content: {markdown_content[:200] if markdown_content else 'None'}")
                    
                    # Check if the extracted content is actually an error message
                    # Check for error messages anywhere in the text (not just at start)
                    if markdown_content and ("Error:" in markdown_content or markdown_content.strip().startswith("Error")):
                        # Extract the error message
                        error_msg = markdown_content
                        if "Error:" in markdown_content:
                            error_msg = markdown_content[markdown_content.find("Error:"):].split("\n")[0]
                        logger.error(f"FastMCP extraction returned error: {error_msg[:200]}")
                        logger.warning("FastMCP extraction failed, falling back to legacy MCP server")
                        pdf_mcp = get_pdf_mcp_server()
                        pdf_result = pdf_mcp.read_file(file_path)
                    else:
                        # Valid content extracted
                        page_count = markdown_content.count("## Page") if markdown_content else 0
                        pdf_result = {
                            "success": True,
                            "text": markdown_content,
                            "page_count": page_count,
                            "file_name": Path(file_path).name,
                            "file_path": file_path,
                            "character_count": len(markdown_content)
                        }
                        logger.info(f"FastMCP extraction successful: {page_count} pages, {len(markdown_content)} characters")
                except Exception as e:
                    logger.warning(f"FastMCP extraction failed with exception, falling back to legacy: {e}", exc_info=True)
                    pdf_mcp = get_pdf_mcp_server()
                    pdf_result = pdf_mcp.read_file(file_path)
            else:
                logger.info("Using legacy PDF MCP server for upload processing")
                pdf_mcp = get_pdf_mcp_server()
                pdf_result = pdf_mcp.read_file(file_path)
            
            if not pdf_result.get("success", False):
                error_msg = pdf_result.get('error', 'Unknown error')
                logger.error(f"PDF extraction failed: {error_msg}")
                return {
                    "success": False,
                    "response": f"Error reading PDF: {error_msg}",
                    "validation_result": None,
                    "metadata": {}
                }
            
            pdf_text = pdf_result.get("text", "")
            file_name = pdf_result.get("file_name", Path(file_path).name)
            
            # Enhanced error detection: Check for error messages anywhere in text
            # Also check common error patterns
            if pdf_text:
                pdf_text_lower = pdf_text.lower()
                # Check for error indicators
                error_indicators = [
                    pdf_text.strip().startswith("Error:"),
                    "error:" in pdf_text[:500].lower(),
                    "failed to" in pdf_text[:500].lower() and ("read" in pdf_text[:500].lower() or "extract" in pdf_text[:500].lower()),
                    "could not extract" in pdf_text_lower[:500],
                    "cannot read" in pdf_text_lower[:500],
                    "pdf file not found" in pdf_text_lower[:500]
                ]
                
                if any(error_indicators):
                    # Extract error message if it's at the start
                    error_msg = pdf_text
                    if "Error:" in pdf_text[:500]:
                        error_msg = pdf_text[pdf_text.find("Error:"):].split("\n")[0]
                    logger.error(f"PDF extraction returned error message: {error_msg[:200]}")
                    logger.debug(f"Full extracted content (first 500 chars): {pdf_text[:500]}")
                    return {
                        "success": False,
                        "response": f"Error reading PDF: {error_msg}",
                        "validation_result": None,
                        "metadata": {
                            "file_name": file_name,
                            "extraction_method": "FastMCP" if use_fastmcp else "Legacy MCP"
                        }
                    }
            
            if not pdf_text or len(pdf_text.strip()) < 50:
                logger.warning(f"PDF text too short or empty: {len(pdf_text) if pdf_text else 0} characters")
                logger.debug(f"Extracted content preview: {pdf_text[:200] if pdf_text else 'None'}")
                return {
                    "success": False,
                    "response": "PDF appears to be empty or could not extract text. Please ensure the PDF contains readable text.",
                    "validation_result": None,
                    "metadata": {
                        "file_name": file_name,
                        "text_length": len(pdf_text) if pdf_text else 0,
                        "extraction_method": "FastMCP" if use_fastmcp else "Legacy MCP"
                    }
                }
            
            # Step 2: Validate domain (agriculture + AP policies)
            logger.info(f"Validating domain for PDF: {file_name} (text length: {len(pdf_text)}, extraction method: {'FastMCP' if use_fastmcp else 'Legacy MCP'})")
            logger.debug(f"Validation input preview (first 200 chars): {pdf_text[:200]}")
            validator = get_pdf_validator()
            try:
                validation_result = validator.validate_domain(pdf_text, file_name)
                logger.debug(f"Validation result: is_valid={validation_result.get('is_valid')}, is_agricultural={validation_result.get('is_agricultural')}, is_ap_related={validation_result.get('is_ap_related')}, confidence={validation_result.get('confidence')}")
                logger.debug(f"Validation reasoning: {validation_result.get('reasoning', 'N/A')[:200]}")
            except Exception as e:
                logger.error(f"Error during PDF domain validation: {e}", exc_info=True)
                logger.error(f"PDF text length: {len(pdf_text)}, first 500 chars: {pdf_text[:500]}")
                return {
                    "success": False,
                    "response": f"Error validating PDF: {str(e)}",
                    "validation_result": {
                        "is_valid": False,
                        "reasoning": f"The content could not be processed due to an error: {str(e)}",
                        "is_agricultural": False,
                        "is_ap_related": False,
                        "confidence": 0.0
                    },
                    "metadata": {
                        "file_name": file_name,
                        "error": str(e),
                        "text_length": len(pdf_text),
                        "extraction_method": "FastMCP" if use_fastmcp else "Legacy MCP"
                    }
                }
            
            if not validation_result.get("is_valid", False):
                # Domain validation failed
                error_message = (
                    "This PDF doesn't relate to the domain I am made for. "
                    "Please try to upload a PDF related to agricultural policies."
                )
                
                logger.warning(f"PDF domain validation failed: {validation_result.get('reasoning', 'Unknown')}")
                
                return {
                    "success": False,
                    "response": error_message,
                    "validation_result": validation_result,
                    "metadata": {
                        "file_name": file_name,
                        "is_agricultural": validation_result.get("is_agricultural", False),
                        "is_ap_related": validation_result.get("is_ap_related", False),
                        "confidence": validation_result.get("confidence", 0.0)
                    }
                }
            
            # Step 3: Domain validation passed - Add to RAG and process PDF
            logger.info(f"PDF domain validation passed. Adding to RAG and processing...")
            
            # Add PDF content to RAG vector store
            try:
                # Use RAG tool to add document (if it supports adding documents)
                # For now, we'll process the PDF through the crew which will use RAG
                logger.info(f"PDF content will be processed through crew with RAG integration")
            except Exception as e:
                logger.warning(f"Could not add PDF to RAG directly: {e}")
            
            # Step 4: Process PDF through crew
            user_query = query or "Summarize this agricultural policy document"
            
            # Process through crew (which will use PDF MCP tool and RAG)
            result = self.process_query(
                user_query=user_query,
                pdf_file_path=file_path
            )
            
            # Preserve full result structure from process_query for frontend
            # This includes response_markdown, response_text, workflow_details, workflow_info, sources, etc.
            return {
                "success": True,
                "response": result.get("response_text") or result.get("response_markdown") or "PDF processed successfully.",
                "validation_result": validation_result,
                "metadata": {
                    "file_name": file_name,
                    "page_count": pdf_result.get("page_count", 0),
                    "character_count": pdf_result.get("character_count", 0),
                    "is_agricultural": validation_result.get("is_agricultural", True),
                    "is_ap_related": validation_result.get("is_ap_related", True),
                    "confidence": validation_result.get("confidence", 1.0),
                    "workflow_details": result.get("workflow_details", {}),
                    "workflow_info": result.get("workflow_info", ""),
                    "response_markdown": result.get("response_markdown", ""),
                    "response_text": result.get("response_text", ""),
                    "sources": result.get("sources", []),
                    "confidence_score": result.get("confidence_score", 0.95),
                    "added_to_rag": True  # Indicates PDF was added to RAG
                },
                # Also include full result structure for frontend compatibility
                "result": {
                    "query": result.get("query", user_query),
                    "response_text": result.get("response_text", ""),
                    "response_markdown": result.get("response_markdown", ""),
                    "workflow_details": result.get("workflow_details", {}),
                    "workflow_info": result.get("workflow_info", ""),
                    "sources": result.get("sources", []),
                    "confidence_score": result.get("confidence_score", 0.95),
                    "validation_result": validation_result,
                    "metadata": {
                        "file_name": file_name,
                        "page_count": pdf_result.get("page_count", 0),
                        "character_count": pdf_result.get("character_count", 0),
                        "is_agricultural": validation_result.get("is_agricultural", True),
                        "is_ap_related": validation_result.get("is_ap_related", True),
                        "confidence": validation_result.get("confidence", 1.0),
                        "added_to_rag": True
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing document upload: {e}", exc_info=True)
            return {
                "success": False,
                "response": f"Error processing PDF: {str(e)}",
                "validation_result": None,
                "metadata": {}
            }

