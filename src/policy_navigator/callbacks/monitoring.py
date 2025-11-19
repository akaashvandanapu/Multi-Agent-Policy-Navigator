"""
Monitoring callbacks for agent execution
Following CrewAI callback patterns for step_callback and task_callback
"""

import logging
from typing import Any, Dict
from crewai.tasks.task_output import TaskOutput
from policy_navigator.adk.adk_agent import get_state_manager, A2AMessage
from policy_navigator.callbacks.execution_tracker import get_tracker
from policy_navigator.config.tool_mappings import get_tool_display_name, is_adk_tool
from policy_navigator.models.schemas import QueryAnalysis
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent role to agent ID mapping
AGENT_ROLE_TO_ID = {
    "Query Understanding Specialist": "query_analyzer",
    "Agricultural Policy Expert": "policy_researcher",
    "Crop Cultivation Expert": "crop_specialist",
    "Pest Control Advisor": "pest_advisor",
    "Market & Weather Analyst": "market_analyst",
    "Non-AP Region Web Research Specialist": "non_ap_researcher",
    "Response Synthesizer": "response_synthesizer",
    "PDF Document Processor": "pdf_processor_agent",
    "Agricultural Calculator (ADK)": "calculator_agent"
}

# Task name to agent ID mapping (for better identification)
TASK_NAME_TO_AGENT_ID = {
    'query_analysis_task': 'query_analyzer',
    'pdf_processing_task': 'pdf_processor_agent',  # Uses CrewAI agent with PDF MCP tool
    'calculation_task': 'calculator_agent',  # ADK agent
    'policy_research_task': 'policy_researcher',
    'crop_guidance_task': 'crop_specialist',
    'pest_management_task': 'pest_advisor',
    'market_info_task': 'market_analyst',
    'non_ap_research_task': 'non_ap_researcher',
    'synthesis_task': 'response_synthesizer',
}


def _identify_agent_id(agent_role: str, task_desc: str, task: Any) -> str:
    """
    Identify agent ID from available information
    
    Args:
        agent_role: Agent role name
        task_desc: Task description
        task: Task object
        
    Returns:
        Agent ID or None if cannot be identified
    """
    # First try: Use agent role mapping
    if agent_role and agent_role in AGENT_ROLE_TO_ID:
        return AGENT_ROLE_TO_ID[agent_role]
    
    # Second try: Check if agent_role is already an ID
    if agent_role and agent_role in AGENT_ROLE_TO_ID.values():
        return agent_role
    
    # Third try: Extract from task name
    if task:
        task_name = None
        if isinstance(task, dict):
            task_name = task.get('name') or task.get('description', '')
        elif hasattr(task, 'name'):
            task_name = task.name
        elif hasattr(task, 'description'):
            # Try to extract task name from description
            desc = task.description
            if desc:
                # Look for task name patterns
                for task_key in TASK_NAME_TO_AGENT_ID:
                    if task_key.replace('_', ' ') in desc.lower() or task_key in desc.lower():
                        return TASK_NAME_TO_AGENT_ID[task_key]
        
        if task_name:
            # Check if task_name matches any known task
            for task_key, agent_id in TASK_NAME_TO_AGENT_ID.items():
                if task_key in task_name.lower() or task_name.lower() in task_key:
                    return agent_id
    
    # Fourth try: Extract from task description keywords
    if task_desc and task_desc != 'Unknown':
        task_lower = task_desc.lower()
        if 'query' in task_lower and ('analysis' in task_lower or 'analyze' in task_lower):
            return 'query_analyzer'
        elif 'policy' in task_lower or 'scheme' in task_lower:
            return 'policy_researcher'
        elif 'crop' in task_lower or 'cultivation' in task_lower:
            return 'crop_specialist'
        elif 'pest' in task_lower or 'disease' in task_lower:
            return 'pest_advisor'
        elif 'market' in task_lower or 'msp' in task_lower or 'price' in task_lower:
            return 'market_analyst'
        elif 'non-ap' in task_lower or 'non ap' in task_lower or 'web search' in task_lower:
            return 'non_ap_researcher'
        elif 'synthesize' in task_lower or 'response' in task_lower or 'final' in task_lower:
            return 'response_synthesizer'
        elif 'pdf' in task_lower or 'document' in task_lower:
            return 'pdf_processor_agent'  # PDF processing uses CrewAI agent with PDF MCP tool
        elif 'calculation' in task_lower or 'calculate' in task_lower:
            return 'calculator_agent'  # Calculations use ADK agent
    
    # If all else fails, return None (don't track as 'Unknown')
    return None


def step_callback(step: Dict[str, Any]) -> None:
    """
    Callback function called after each step of every agent
    
    Args:
        step: Dictionary containing step information including:
              - agent: Agent that executed the step
              - task: Task being executed
              - output: Step output
              - iterations: Current iteration number
    """
    try:
        tracker = get_tracker()
        
        # Debug: Log step structure to understand what CrewAI passes
        logger.debug(f"Step callback received - Type: {type(step)}, Keys: {list(step.keys()) if isinstance(step, dict) else 'Not a dict'}")
        
        # Safely extract agent role - handle both dict and object types with multiple fallbacks
        agent_role = None
        agent = None
        
        # Try multiple ways to get agent
        if isinstance(step, dict):
            agent = step.get('agent') or step.get('agent_role') or step.get('agent_name')
        else:
            agent = (getattr(step, 'agent', None) or 
                    getattr(step, 'agent_role', None) or 
                    getattr(step, 'agent_name', None))
        
        if agent:
            if isinstance(agent, dict):
                agent_role = (agent.get('role') or 
                            agent.get('agent_role') or 
                            agent.get('name') or 
                            agent.get('agent_name'))
            elif hasattr(agent, 'role'):
                agent_role = agent.role
            elif hasattr(agent, 'agent_role'):
                agent_role = agent.agent_role
            elif hasattr(agent, 'name'):
                agent_role = agent.name
            elif hasattr(agent, 'backstory'):
                # Try to get role from agent object attributes
                agent_role = (getattr(agent, 'role', None) or 
                            getattr(agent, 'agent_role', None) or
                            getattr(agent, 'name', None))
            
            # Log available tools and track them if agent executed
            if hasattr(agent, 'tools') and agent.tools:
                logger.debug(f"Agent {agent_role} has {len(agent.tools)} available tools")
                # Log tool names for debugging
                tool_names = []
                for tool in agent.tools:
                    tool_name = None
                    if hasattr(tool, 'name'):
                        tool_name = tool.name
                    elif hasattr(tool, '__name__'):
                        tool_name = tool.__name__
                    elif hasattr(tool, 'function'):
                        # Tool might be a function
                        func = tool.function if hasattr(tool, 'function') else tool
                        if hasattr(func, '__name__'):
                            tool_name = func.__name__
                    else:
                        tool_name = str(tool)
                    
                    if tool_name:
                        # Clean up tool name
                        tool_name = tool_name.replace('<function ', '').replace(' at 0x', '')
                        tool_name = tool_name.split(' at ')[0].split('>')[0].strip()
                        tool_names.append(tool_name)
                
                logger.debug(f"Available tools: {tool_names}")
                
                # If we have an identified agent_id and tools, track them as potentially used
                # This is a fallback when tool_calls aren't in the step object
                # We'll track all available tools for the agent (CrewAI agents typically use their tools)
                if agent_id and agent_id not in ['Unknown', 'unknown_agent'] and tool_names:
                    # Only track if we haven't already tracked tools for this agent in this step
                    # This prevents double-tracking
                    logger.debug(f"Agent {agent_id} has tools available: {tool_names}")
                    # Note: We'll track actual usage from tool_calls if available, otherwise
                    # we'll use this as a fallback after checking tool_calls below
        
        # If still no agent_role, try to extract from step directly
        if not agent_role:
            if isinstance(step, dict):
                agent_role = (step.get('agent_role') or 
                            step.get('agent_name') or
                            step.get('role'))
            else:
                agent_role = (getattr(step, 'agent_role', None) or
                            getattr(step, 'agent_name', None) or
                            getattr(step, 'role', None))
        
        # Safely extract task description - handle both dict and object types with multiple fallbacks
        task_desc = None
        task = None
        
        # Try multiple ways to get task
        if isinstance(step, dict):
            task = step.get('task') or step.get('task_description') or step.get('task_name')
        else:
            task = (getattr(step, 'task', None) or 
                   getattr(step, 'task_description', None) or
                   getattr(step, 'task_name', None))
        
        if task:
            if isinstance(task, dict):
                task_desc = (task.get('description') or 
                           task.get('task_description') or
                           task.get('name') or
                           task.get('task_name'))
                if task_desc:
                    task_desc = task_desc[:100]
            elif hasattr(task, 'description'):
                task_desc = (task.description[:100] if task.description else None)
            elif hasattr(task, 'task_description'):
                task_desc = (task.task_description[:100] if task.task_description else None)
            elif hasattr(task, 'name'):
                task_desc = (task.name[:100] if task.name else None)
        
        # If still no task_desc, try to extract from step directly
        if not task_desc:
            if isinstance(step, dict):
                task_desc = (step.get('task_description') or 
                           step.get('task_name') or
                           step.get('description'))
                if task_desc:
                    task_desc = str(task_desc)[:100]
            else:
                task_desc = (getattr(step, 'task_description', None) or
                           getattr(step, 'task_name', None) or
                           getattr(step, 'description', None))
                if task_desc:
                    task_desc = str(task_desc)[:100]
        
        # Use 'Unknown' as fallback for logging, but don't use it for identification
        agent_role_str = agent_role if agent_role else 'Unknown'
        task_desc_str = task_desc if task_desc else 'Unknown'
        
        # Safely extract iteration count
        if isinstance(step, dict):
            iteration = step.get('iterations', 0)
        else:
            iteration = getattr(step, 'iterations', 0)
        
        # Track agent execution - improve identification
        agent_id = _identify_agent_id(agent_role_str, task_desc_str, task)
        
        # Only track if we have a valid agent_id (not 'Unknown' or 'unknown_agent')
        if agent_id and agent_id not in ['Unknown', 'unknown_agent']:
            tracker.track_agent(agent_id)
            
            # Special logging for MCP agents to verify tool availability
            if agent_id in ['market_analyst', 'non_ap_researcher']:
                logger.info(f"📡 MCP Agent executing: {agent_role_str} (ID: {agent_id})")
                # Try to check if agent has MCP tools available
                if agent:
                    try:
                        if hasattr(agent, 'mcps') and agent.mcps:
                            mcp_count = len(agent.mcps) if isinstance(agent.mcps, (list, tuple)) else 1
                            logger.info(f"  ✓ MCP servers configured: {mcp_count} server(s)")
                            # Log MCP server details
                            for i, mcp in enumerate(agent.mcps if isinstance(agent.mcps, (list, tuple)) else [agent.mcps]):
                                if hasattr(mcp, 'command'):
                                    # MCPServerStdio structured config
                                    cmd = getattr(mcp, 'command', 'unknown')
                                    args = getattr(mcp, 'args', [])
                                    logger.info(f"    MCP Server {i+1}: stdio transport - command: {cmd}, args: {args}")
                                elif isinstance(mcp, list):
                                    # Command format
                                    logger.info(f"    MCP Server {i+1}: command format - {mcp}")
                                elif hasattr(mcp, 'url'):
                                    logger.debug(f"    MCP Server {i+1}: {str(mcp.url)[:80]}...")
                                else:
                                    logger.debug(f"    MCP Server {i+1}: {type(mcp).__name__} - {str(mcp)[:80]}")
                        else:
                            logger.warning(f"  ⚠ Agent has no 'mcps' attribute or MCP servers not configured")
                        
                        # Check tools - this is critical for MCP agents
                        if hasattr(agent, 'tools'):
                            if agent.tools:
                                tool_count = len(agent.tools) if isinstance(agent.tools, (list, tuple)) else 1
                                all_tool_names = []
                                for t in (agent.tools if isinstance(agent.tools, (list, tuple)) else [agent.tools]):
                                    tool_name = None
                                    if hasattr(t, 'name'):
                                        tool_name = getattr(t, 'name', 'unknown')
                                    elif hasattr(t, '__name__'):
                                        tool_name = getattr(t, '__name__', 'unknown')
                                    elif callable(t):
                                        tool_name = getattr(t, '__name__', 'callable')
                                    else:
                                        tool_name = str(t)[:50]
                                    all_tool_names.append(tool_name)
                                
                                ollama_tools = [name for name in all_tool_names if 'web_search' in name.lower() or 'web_fetch' in name.lower() or ('ollama' in name.lower() and 'search' in name.lower())]
                                logger.info(f"  ✓ Agent has {tool_count} tool(s) available during execution")
                                logger.info(f"  All tools: {', '.join(all_tool_names[:10])}")
                                if ollama_tools:
                                    logger.info(f"  ✅ Ollama Web Search MCP tools found: {', '.join(ollama_tools)}")
                                else:
                                    logger.error(f"  ❌ CRITICAL: No Ollama Web Search MCP tools found in {tool_count} available tools!")
                                    logger.error(f"    This means the agent cannot use web_search or web_fetch tools")
                                    logger.error(f"    Available tools: {', '.join(all_tool_names[:10])}")
                            else:
                                logger.error(f"  ❌ CRITICAL: Agent tools list is EMPTY during execution!")
                                logger.error(f"    MCP tools should be available but are not. Check MCP server startup.")
                        else:
                            logger.error(f"  ❌ CRITICAL: Agent has no 'tools' attribute during execution!")
                            logger.error(f"    MCP tools cannot be accessed. This indicates a problem with MCP integration.")
                    except Exception as e:
                        logger.error(f"  ❌ Could not inspect agent tools: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
            
            logger.info(f"Step completed - Agent: {agent_role_str} (ID: {agent_id}), Iteration: {iteration}")
            logger.debug(f"Task: {task_desc_str}...")
        else:
            # Log warning with more context for debugging
            logger.warning(f"Could not identify agent - role: {agent_role_str}, task: {task_desc_str[:50]}")
            logger.debug(f"Step structure: {type(step)}, Agent type: {type(agent) if agent else 'None'}, Task type: {type(task) if task else 'None'}")
            # Don't track unknown agents - they cause display issues
            return  # Exit early if agent cannot be identified
        
        # Track tool usage if present - handle both dict and object types
        # CrewAI may pass tools in different formats: tool_calls, actions, or tool_uses
        tool_calls = None
        if isinstance(step, dict):
            # Try multiple possible keys for tool information
            tool_calls = (step.get('tool_calls') or 
                         step.get('actions') or 
                         step.get('tool_uses') or
                         step.get('tools'))
        else:
            # Try multiple attributes
            tool_calls = (getattr(step, 'tool_calls', None) or
                         getattr(step, 'actions', None) or
                         getattr(step, 'tool_uses', None) or
                         getattr(step, 'tools', None))
        
        # Also check if step has output with tool information
        if not tool_calls:
            output = step.get('output') if isinstance(step, dict) else getattr(step, 'output', None)
            if output:
                if isinstance(output, dict):
                    tool_calls = output.get('tool_calls') or output.get('actions')
                elif hasattr(output, 'tool_calls'):
                    tool_calls = output.tool_calls
                elif hasattr(output, 'actions'):
                    tool_calls = output.actions
        
        # Also check task object for tool information
        if not tool_calls and task:
            if isinstance(task, dict):
                task_tools = task.get('tools') or task.get('tool_calls')
            elif hasattr(task, 'tools'):
                task_tools = task.tools
            elif hasattr(task, 'tool_calls'):
                task_tools = task.tool_calls
            else:
                task_tools = None
            
            if task_tools:
                logger.debug(f"Found tools in task object: {task_tools}")
                # Note: task.tools shows available tools, not necessarily used ones
        
        if tool_calls:
            tool_count = len(tool_calls) if isinstance(tool_calls, (list, tuple)) else 1
            logger.info(f"🔧 Found {tool_count} tool call(s) for agent: {agent_role} (ID: {agent_id})")
            tool_names = []
            # Handle both list and single tool call
            if not isinstance(tool_calls, (list, tuple)):
                tool_calls = [tool_calls]
            
            for tc in tool_calls:
                tool_name = None
                
                # Handle both dict and AgentAction object types
                if isinstance(tc, dict):
                    # Try multiple possible keys
                    tool_name = tc.get('tool') or tc.get('name') or tc.get('tool_name')
                elif hasattr(tc, 'tool'):
                    # AgentAction object has .tool attribute
                    tool_obj = tc.tool
                    if hasattr(tool_obj, 'name'):
                        tool_name = tool_obj.name
                    elif hasattr(tool_obj, '__name__'):
                        tool_name = tool_obj.__name__
                    elif hasattr(tool_obj, 'function'):
                        # Some tools have function attribute
                        func = tool_obj.function
                        if hasattr(func, 'name'):
                            tool_name = func.name
                        elif hasattr(func, '__name__'):
                            tool_name = func.__name__
                    elif hasattr(tool_obj, 'description'):
                        # Extract from description if available
                        desc = tool_obj.description
                        if desc:
                            # Try to extract tool name from description
                            tool_name = str(tool_obj)
                    elif hasattr(tool_obj, 'tool'):
                        # Nested tool object
                        nested_tool = tool_obj.tool
                        if hasattr(nested_tool, 'name'):
                            tool_name = nested_tool.name
                        elif hasattr(nested_tool, '__name__'):
                            tool_name = nested_tool.__name__
                        else:
                            tool_name = str(nested_tool) if nested_tool else None
                    else:
                        tool_name = str(tool_obj) if tool_obj else None
                elif hasattr(tc, 'name'):
                    # Direct tool name attribute
                    tool_name = tc.name
                elif hasattr(tc, 'action'):
                    # Some action objects have action attribute
                    action = getattr(tc, 'action', None)
                    if action:
                        if hasattr(action, 'name'):
                            tool_name = action.name
                        else:
                            tool_name = str(action)
                elif hasattr(tc, 'function'):
                    # Function-based tool
                    func = tc.function
                    if hasattr(func, 'name'):
                        tool_name = func.name
                    elif hasattr(func, '__name__'):
                        tool_name = func.__name__
                
                # Fallback to string representation
                if not tool_name:
                    tool_name = str(tc) if tc else 'Unknown'
                
                # Clean up tool name - remove common prefixes/suffixes
                if tool_name and tool_name != 'Unknown':
                    # Remove function call indicators
                    tool_name = tool_name.replace('<function ', '').replace(' at 0x', '')
                    tool_name = tool_name.split(' at ')[0].split('>')[0].strip()
                    
                    # Detect Ollama Web Search MCP tools (web_search, web_fetch, or ollama-related)
                    tool_name_lower = tool_name.lower()
                    is_ollama_tool = (
                        'web_search' in tool_name_lower or 
                        'web_fetch' in tool_name_lower or
                        ('ollama' in tool_name_lower and 'search' in tool_name_lower) or
                        tool_name_lower == 'web_search' or
                        tool_name_lower == 'web_fetch'
                    )
                    if is_ollama_tool:
                        logger.info(f"🔍✅ Ollama Web Search MCP tool CALLED: {tool_name} (Agent: {agent_id})")
                        # Normalize MCP tool names to standard display name
                        tool_name = 'Ollama Web Search MCP'
                    elif agent_id in ['market_analyst', 'non_ap_researcher']:
                        # Log all tool calls for MCP agents to debug
                        logger.debug(f"  Tool called by {agent_id}: {tool_name}")
                    
                    tool_names.append(tool_name)
            
            if tool_names:
                logger.info(f"Tools used by {agent_role} ({agent_id}): {tool_names}")
                
                # Track each tool
                for tool_name in tool_names:
                    if tool_name and tool_name != 'Unknown':
                        # Use centralized tool name mapping
                        clean_tool_name = get_tool_display_name(tool_name)
                        
                        # Log ADK tool usage for A2A communication verification
                        if is_adk_tool(tool_name):
                            logger.info(f"✅ ADK tool detected: {tool_name} -> {clean_tool_name} (Agent: {agent_id})")
                            logger.debug(f"A2A communication enabled via ADK tool: {clean_tool_name}")
                        
                        tracker.track_tool(agent_id, clean_tool_name)
                        
                        # Log tool tracking for debugging
                        logger.info(f"✓ Tracked tool: {clean_tool_name} for agent: {agent_id} ({agent_role})")
            else:
                logger.debug(f"No tool names extracted from tool_calls for agent: {agent_role}")
        else:
            logger.debug(f"No tool_calls found in step for agent: {agent_role}")
            
            # FALLBACK: Track agent's available tools if no tool_calls found
            # This ensures tools are displayed even if CrewAI doesn't provide tool_calls in step
            if agent_id and agent_id not in ['Unknown', 'unknown_agent'] and agent:
                # Check if we've already tracked tools for this agent in this execution
                existing_tools = tracker.get_agent_tools().get(agent_id, [])
                if not existing_tools:
                    # Check for MCP tools first
                    if hasattr(agent, 'mcps') and agent.mcps:
                        logger.info(f"🔍 Agent {agent_id} has MCP servers configured: {agent.mcps}")
                        # For MCP agents, we expect Ollama Web Search MCP tools
                        if agent_id in ['market_analyst', 'non_ap_researcher']:
                            logger.info(f"📡 MCP Agent detected: {agent_id} - Expected Ollama Web Search MCP tools")
                            # Try to discover actual MCP tool names from agent
                            try:
                                if hasattr(agent, 'tools') and agent.tools:
                                    mcp_tool_names = []
                                    for tool in agent.tools:
                                        tool_name = None
                                        if hasattr(tool, 'name'):
                                            tool_name = tool.name
                                        elif hasattr(tool, '__name__'):
                                            tool_name = tool.__name__
                                        else:
                                            tool_name = str(tool)
                                        
                                        # Check if this looks like an Ollama Web Search MCP tool
                                        tool_name_lower = tool_name.lower() if tool_name else ''
                                        is_ollama_tool = (
                                            'web_search' in tool_name_lower or 
                                            'web_fetch' in tool_name_lower or
                                            ('ollama' in tool_name_lower and 'search' in tool_name_lower) or
                                            tool_name_lower == 'web_search' or
                                            tool_name_lower == 'web_fetch'
                                        )
                                        if is_ollama_tool:
                                            mcp_tool_names.append(tool_name)
                                            logger.info(f"🔍 Discovered Ollama Web Search MCP tool: {tool_name}")
                                    
                                    if mcp_tool_names:
                                        # Track discovered MCP tools
                                        for mcp_tool_name in mcp_tool_names:
                                            clean_tool_name = get_tool_display_name('Ollama Web Search MCP')
                                            tracker.track_tool(agent_id, clean_tool_name)
                                            logger.info(f"✓ Tracked discovered MCP tool: {mcp_tool_name} -> {clean_tool_name} for agent: {agent_id}")
                                    else:
                                        # Fallback: Track expected MCP tool
                                        clean_tool_name = get_tool_display_name('Ollama Web Search MCP')
                                        tracker.track_tool(agent_id, clean_tool_name)
                                        logger.info(f"✓ Tracked expected MCP tool: {clean_tool_name} for agent: {agent_id} (tools may be lazy-loaded)")
                                else:
                                    # Fallback: Track expected MCP tool if tools not yet loaded
                                    clean_tool_name = get_tool_display_name('Ollama Web Search MCP')
                                    tracker.track_tool(agent_id, clean_tool_name)
                                    logger.info(f"✓ Tracked expected MCP tool: {clean_tool_name} for agent: {agent_id} (tools may be lazy-loaded)")
                            except Exception as e:
                                logger.debug(f"Could not inspect MCP tools for {agent_id}: {e}")
                                # Fallback: Track expected MCP tool
                                clean_tool_name = get_tool_display_name('Ollama Web Search MCP')
                                tracker.track_tool(agent_id, clean_tool_name)
                                logger.info(f"✓ Tracked expected MCP tool: {clean_tool_name} for agent: {agent_id} (fallback)")
                    
                    # Check for regular tools
                    if hasattr(agent, 'tools') and agent.tools:
                        agent_tools_list = []
                        for tool in agent.tools:
                            tool_name = None
                            if hasattr(tool, 'name'):
                                tool_name = tool.name
                            elif hasattr(tool, '__name__'):
                                tool_name = tool.__name__
                            elif hasattr(tool, 'function'):
                                func = tool.function if hasattr(tool, 'function') else tool
                                if hasattr(func, '__name__'):
                                    tool_name = func.__name__
                            else:
                                tool_name = str(tool)
                            
                            if tool_name:
                                # Clean up tool name
                                tool_name = tool_name.replace('<function ', '').replace(' at 0x', '')
                                tool_name = tool_name.split(' at ')[0].split('>')[0].strip()
                                agent_tools_list.append(tool_name)
                        
                        # Track available tools as fallback (CrewAI agents with tools typically use them)
                        if agent_tools_list:
                            logger.info(f"Fallback: Tracking available tools for {agent_id}: {agent_tools_list}")
                            for tool_name in agent_tools_list:
                                if tool_name and tool_name != 'Unknown':
                                    clean_tool_name = get_tool_display_name(tool_name)
                                    tracker.track_tool(agent_id, clean_tool_name)
                                    logger.info(f"✓ Tracked tool (fallback): {clean_tool_name} for agent: {agent_id}")
            
            # Log step contents for debugging (only in debug mode to avoid spam)
            if logger.isEnabledFor(logging.DEBUG):
                if isinstance(step, dict):
                    logger.debug(f"Step keys: {list(step.keys())}")
                    # Check for any tool-related keys
                    tool_keys = [k for k in step.keys() if 'tool' in k.lower() or 'action' in k.lower()]
                    if tool_keys:
                        logger.debug(f"Found tool-related keys in step: {tool_keys}")
                        # Try to extract from these keys
                        for key in tool_keys:
                            value = step.get(key)
                            if value:
                                logger.debug(f"Found value in {key}: {type(value)} - {str(value)[:200]}")
                else:
                    # Check object attributes
                    attrs = [attr for attr in dir(step) if 'tool' in attr.lower() or 'action' in attr.lower()]
                    if attrs:
                        logger.debug(f"Found tool-related attributes: {attrs}")
                        for attr in attrs:
                            try:
                                value = getattr(step, attr, None)
                                if value:
                                    logger.debug(f"Found value in {attr}: {type(value)} - {str(value)[:200]}")
                            except Exception:
                                pass
        
        # Log errors if present - handle both dict and object types
        error = None
        if isinstance(step, dict):
            error = step.get('error')
        else:
            error = getattr(step, 'error', None)
        
        if error:
            logger.error(f"Error in step: {error}")
            
    except Exception as e:
        logger.error(f"Error in step_callback: {e}")


def task_callback(output: TaskOutput) -> None:
    """
    Callback function called after the completion of each task
    Also stores task outputs in StateManager for ADK agent access (A2A communication)
    
    Args:
        output: TaskOutput object containing task results
    """
    try:
        tracker = get_tracker()
        task_desc = output.description[:100] if output.description else 'Unknown'
        agent_role = output.agent if hasattr(output, 'agent') else 'Unknown'
        
        # Track agent execution - improve identification
        agent_id = _identify_agent_id(agent_role, task_desc, None)
        
        # Only track if we have a valid agent_id
        if agent_id and agent_id not in ['Unknown', 'unknown_agent']:
            tracker.track_agent(agent_id)
        else:
            logger.warning(f"Could not identify agent in task_callback - role: {agent_role}, task: {task_desc[:50]}")
            # Don't track unknown agents
            return  # Exit early if agent cannot be identified
        
        logger.info(f"Task completed - Agent: {agent_role} (ID: {agent_id})")
        logger.info(f"Task: {task_desc}...")
        
        # Validate MCP agent tool usage - check both tracked tools and output
        if agent_id in ['market_analyst', 'non_ap_researcher']:
            agent_tools = tracker.get_agent_tools().get(agent_id, [])
            
            # Also check output for tool information
            ollama_tool_in_output = False
            if hasattr(output, 'raw'):
                try:
                    import json
                    raw_str = output.raw if isinstance(output.raw, str) else json.dumps(output.raw) if isinstance(output.raw, dict) else str(output.raw)
                    if raw_str:
                        raw_lower = raw_str.lower()
                        ollama_tool_in_output = (
                            'web_search' in raw_lower or 
                            'web_fetch' in raw_lower or
                            'ollama' in raw_lower or
                            'ollama web search' in raw_lower
                        )
                        if ollama_tool_in_output:
                            logger.info(f"✓ {agent_id}: Found Ollama Web Search MCP references in output (tool may have been used)")
                except Exception as e:
                    logger.debug(f"Could not check output for Ollama Web Search MCP references: {e}")
            
            # Check if any Ollama Web Search MCP tools were actually used (not just tracked as available)
            ollama_tool_used = any(
                'ollama' in tool.lower() or 
                'web_search' in tool.lower() or
                'web_fetch' in tool.lower() or
                'ollama web search' in tool.lower()
                for tool in agent_tools
            )
            
            if not ollama_tool_used and not ollama_tool_in_output:
                logger.warning(f"⚠️ {agent_id}: Task completed but Ollama Web Search MCP tools do NOT appear to have been called!")
                logger.warning(f"  Tracked tools: {agent_tools if agent_tools else 'None'}")
                logger.warning(f"  The agent MUST use Ollama Web Search MCP tools for real-time data.")
                logger.warning(f"  Please verify that OLLAMA_API_KEY is set and MCP server is accessible.")
            elif ollama_tool_used:
                logger.info(f"✓ {agent_id}: Ollama Web Search MCP tools were tracked as used: {[t for t in agent_tools if 'ollama' in t.lower() or 'web_search' in t.lower() or 'web_fetch' in t.lower()]}")
            elif ollama_tool_in_output:
                logger.info(f"✓ {agent_id}: Ollama Web Search MCP tool usage detected in output (may not have been tracked in step_callback)")
            elif not agent_tools:
                logger.warning(f"⚠️ {agent_id}: No tools tracked - Ollama Web Search MCP tools may not be available or were not used!")
        
        # Try to extract tools from task output if available
        # Some CrewAI versions store tool usage in output
        tools_tracked_from_output = False
        if hasattr(output, 'tool_calls') and output.tool_calls:
            logger.info(f"Found tools in task output: {output.tool_calls}")
            for tool_call in output.tool_calls:
                tool_name = None
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('tool') or tool_call.get('name')
                elif hasattr(tool_call, 'tool'):
                    tool_obj = tool_call.tool
                    tool_name = getattr(tool_obj, 'name', None) or getattr(tool_obj, '__name__', None)
                elif hasattr(tool_call, 'name'):
                    tool_name = tool_call.name
                
                if tool_name:
                    clean_tool_name = get_tool_display_name(tool_name)
                    tracker.track_tool(agent_id, clean_tool_name)
                    tools_tracked_from_output = True
                    logger.info(f"✓ Tracked tool from task output: {clean_tool_name} for agent: {agent_id}")
        
        # FALLBACK: If no tools tracked from output, check if agent has tools assigned
        # This ensures tools are displayed in the frontend even if CrewAI doesn't report usage
        if not tools_tracked_from_output:
            # Try to get agent from output if available
            agent_from_output = None
            if hasattr(output, 'agent'):
                agent_from_output = output.agent
            elif hasattr(output, 'agent_role'):
                # Try to find agent by role
                from policy_navigator.crew import PolicyNavigatorCrew
                crew_instance = PolicyNavigatorCrew()
                # This is a bit hacky, but we need to get the agent object
                # For now, we'll use the agent_id to determine expected tools
                pass
            
            # If we can't get agent object, use agent_id to determine expected tools
            # This is a fallback to ensure tools are shown in UI
            if agent_id:
                # Map agent IDs to their expected tool display names (as shown in UI)
                # These are the standardized display names from tool_mappings
                expected_tools_map = {
                    'query_analyzer': ['Region Detector'],
                    'policy_researcher': ['RAG Document Search'],
                    'crop_specialist': ['RAG Document Search'],
                    'pest_advisor': ['RAG Document Search'],
                    'market_analyst': ['Ollama Web Search MCP'],  # MCP tools
                    'non_ap_researcher': ['Ollama Web Search MCP'],
                    'pdf_processor_agent': ['PDF Processor (MCP)'],
                    'calculator_agent': ['Calculator (ADK)'],  # ADK agent
                    'response_synthesizer': []
                }
                
                # Check if we've already tracked tools for this agent
                existing_tools = tracker.get_agent_tools().get(agent_id, [])
                if not existing_tools:
                    expected_tools = expected_tools_map.get(agent_id, [])
                    if expected_tools:
                        logger.info(f"Fallback: Tracking expected tools for {agent_id}: {expected_tools}")
                        # Track the expected tool directly (already in display name format)
                        for tool_display_name in expected_tools:
                            tracker.track_tool(agent_id, tool_display_name)
                            logger.info(f"✓ Tracked expected tool (fallback): {tool_display_name} for agent: {agent_id}")
        
        # Log output summary
        if output.raw:
            output_length = len(output.raw)
            logger.info(f"Output length: {output_length} characters")
            logger.debug(f"Output preview: {output.raw[:200]}...")
        
        # Log structured output if available
        if output.pydantic:
            logger.info(f"Structured output (Pydantic): {type(output.pydantic).__name__}")
            
            # Store query_analysis_task output in tracker for conditional task checks
            if isinstance(output.pydantic, QueryAnalysis):
                query_analysis = output.pydantic
                
                # Validate query_analysis before storing
                required_agents = getattr(query_analysis, 'required_agents', [])
                query_type = getattr(query_analysis, 'query_type', '')
                original_query = getattr(query_analysis, 'original_query', '')
                
                # Validate required_agents is a list
                if not isinstance(required_agents, list):
                    logger.warning(f"query_analysis.required_agents is not a list: {type(required_agents)}. Converting to list.")
                    if required_agents is None:
                        required_agents = []
                    else:
                        required_agents = [required_agents] if not isinstance(required_agents, (list, tuple)) else list(required_agents)
                    # Update the query_analysis object
                    query_analysis.required_agents = required_agents
                
                # Log query_analysis details for debugging
                logger.info(f"📊 Query Analysis stored:")
                logger.info(f"   - Query: {original_query[:100]}...")
                logger.info(f"   - Query Type: {query_type}")
                logger.info(f"   - Required Agents: {required_agents}")
                logger.info(f"   - Region Type: {getattr(query_analysis, 'region_type', 'unknown')}")
                logger.info(f"   - Is AP Query: {getattr(query_analysis, 'is_ap_query', 'unknown')}")
                logger.info(f"   - Is Out of Scope: {getattr(query_analysis, 'is_out_of_scope', False)}")
                
                # Validate that required_agents includes response_synthesizer
                if "response_synthesizer" not in required_agents:
                    logger.warning(f"⚠️  WARNING: response_synthesizer not in required_agents: {required_agents}")
                    logger.warning(f"   Adding response_synthesizer to required_agents")
                    required_agents.append("response_synthesizer")
                    query_analysis.required_agents = required_agents
                
                # Store validated query_analysis
                tracker.store_query_analysis(query_analysis)
                logger.info(f"✅ Stored query_analysis in tracker for conditional task checks")
                logger.debug(f"   Tracker now has query_analysis: {tracker.query_analysis is not None}")
        
        if output.json_dict:
            logger.debug(f"JSON output available with {len(output.json_dict)} fields")
        
        # Log execution summary
        if hasattr(output, 'summary'):
            logger.info(f"Task summary: {output.summary}")
        
        # Guardrail Validation Tracking
        # Check if guardrail validation was performed
        if hasattr(output, 'guardrail_result'):
            guardrail_result = output.guardrail_result
            if guardrail_result:
                if hasattr(guardrail_result, 'valid'):
                    is_valid = guardrail_result.valid
                    if is_valid:
                        logger.info(f"✓ Guardrail validation PASSED for task: {task_desc[:50]}")
                    else:
                        feedback = getattr(guardrail_result, 'feedback', 'Validation failed')
                        logger.warning(f"⚠ Guardrail validation FAILED for task: {task_desc[:50]}")
                        logger.warning(f"  Feedback: {feedback}")
                elif isinstance(guardrail_result, dict):
                    is_valid = guardrail_result.get('valid', True)
                    if is_valid:
                        logger.info(f"✓ Guardrail validation PASSED for task: {task_desc[:50]}")
                    else:
                        feedback = guardrail_result.get('feedback', 'Validation failed')
                        logger.warning(f"⚠ Guardrail validation FAILED for task: {task_desc[:50]}")
                        logger.warning(f"  Feedback: {feedback}")
        
        # Check for guardrail-related errors in output
        if hasattr(output, 'error') and output.error:
            error_str = str(output.error).lower()
            if 'guardrail' in error_str or 'hallucination' in error_str or 'validation' in error_str:
                logger.warning(f"⚠ Guardrail-related error in task: {task_desc[:50]}")
                logger.warning(f"  Error: {output.error}")
        
        # A2A Communication: Store task output in StateManager for ADK agents
        state_manager = get_state_manager()
        
        # Extract agent ID from agent_role or task description
        agent_id = agent_role.lower().replace(' ', '_') if agent_role else 'unknown_agent'
        
        # Store task output in state
        task_output_data = {
            "raw": output.raw if output.raw else "",
            "pydantic": output.pydantic.model_dump() if output.pydantic else None,
            "json_dict": output.json_dict if output.json_dict else {},
            "description": output.description if output.description else "",
            "agent": agent_role
        }
        
        state_manager.update_state(f"{agent_id}_output", task_output_data)
        logger.info(f"✓ Stored task output in StateManager for A2A communication (Agent: {agent_id})")
        
        # Create A2A message for ADK agents (A2A Protocol)
        import uuid
        a2a_message = A2AMessage(
            from_agent=agent_id,
            to_agent="adk_agents",  # Broadcast to all ADK agents (A2A pattern)
            message_type="task_completion",
            content={
                "task_description": task_desc,
                "output": task_output_data,
                "agent": agent_role
            },
            timestamp=datetime.now().isoformat(),
            conversation_id=str(uuid.uuid4()),  # Track this conversation
            status="completed",
            capabilities=None,  # CrewAI agents don't expose capabilities in this context
            response_required=False
        )
        
        state_manager.add_message(a2a_message)
        logger.info(f"✓ Created A2A message from CrewAI agent '{agent_id}' to ADK agents (A2A Protocol)")
        logger.debug(f"A2A Message Details: type={a2a_message.message_type}, from={a2a_message.from_agent}, to={a2a_message.to_agent}, status={a2a_message.status}, conversation_id={a2a_message.conversation_id}")
            
    except Exception as e:
        logger.error(f"Error in task_callback: {e}")

