"""
Tool Name Mappings - Single Source of Truth
Consolidates tool name mappings used across monitoring and orchestrator
"""

# Tool display name mapping - maps raw tool names to clean display names
# This ensures consistency across monitoring callbacks and orchestrator
TOOL_DISPLAY_NAMES = {
    # RAG Tools - handle various name formats
    'RAG Document Search': 'RAG Document Search',
    'RAG Document Search Tool': 'RAG Document Search',
    'rag_tool': 'RAG Document Search',
    'rag document search tool': 'RAG Document Search',
    
    # PDF Processing Tools (MCP)
    'PDF Processor (MCP)': 'PDF Processor (MCP)',
    'PDF Processor': 'PDF Processor (MCP)',
    'PDF MCP': 'PDF Processor (MCP)',
    # MCP tools are prefixed with server name, so handle common variations
    'pdf_reader': 'PDF Processor (MCP)',
    'read_pdf': 'PDF Processor (MCP)',
    'extract_pdf_text': 'PDF Processor (MCP)',
    
    # Calculator Tools (ADK only)
    'Calculator (ADK)': 'Calculator (ADK)',
    'Agricultural Calculator ADK Tool': 'Calculator (ADK)',
    
    # Region Detector Tools
    'Region Detector': 'Region Detector',
    'Region Detector Tool': 'Region Detector',
    'region_detector_tool': 'Region Detector',
    'region detector tool': 'Region Detector',
    'region_detector': 'Region Detector',
    
    # Additional variations that might appear
    'RAG Tool': 'RAG Document Search',
    'RAG': 'RAG Document Search',
    'PDF Tool': 'PDF Processor (MCP)',
    'PDF': 'PDF Processor (MCP)',
    
    # MCP Tools - Ollama Web Search MCP variations
    'Ollama Web Search MCP': 'Ollama Web Search MCP',
    'Ollama MCP': 'Ollama Web Search MCP',
    'ollama_web_search': 'Ollama Web Search MCP',
    'ollama': 'Ollama Web Search MCP',
    'web_search': 'Ollama Web Search MCP',
    'web_fetch': 'Ollama Web Search MCP',
    'web search': 'Ollama Web Search MCP',
    'Web Search': 'Ollama Web Search MCP',
    
    # PDF MCP tool variations
    'pdf_mcp_read_file': 'PDF Processor (MCP)',
    'PDF MCP Reader Tool': 'PDF Processor (MCP)',
    'read_pdf': 'PDF Processor (MCP)',
}

# Tool framework mapping - identifies which tools are ADK-based
# Used to determine A2A communication and framework usage requirements
ADK_TOOLS = {
    'Calculator (ADK)',
    'Calculator Tool (ADK)',
    'Agricultural Calculator ADK Tool',
}

# Helper function to get tool display name
def get_tool_display_name(tool_name: str) -> str:
    """
    Get standardized display name for a tool
    
    Args:
        tool_name: Raw tool name from tracking
        
    Returns:
        Clean display name for the tool
    """
    if not tool_name or tool_name == 'Unknown':
        return tool_name
    
    # Check direct mapping first
    if tool_name in TOOL_DISPLAY_NAMES:
        return TOOL_DISPLAY_NAMES[tool_name]
    
    # Clean common suffixes
    cleaned = tool_name.replace(' Tool', '').replace('_tool', '').replace('_', ' ')
    
    # Check if cleaned version exists
    if cleaned in TOOL_DISPLAY_NAMES:
        return TOOL_DISPLAY_NAMES[cleaned]
    
    # Return cleaned version if no mapping found
    return cleaned

# Helper function to check if tool is ADK-based
def is_adk_tool(tool_name: str) -> bool:
    """
    Check if a tool is ADK-based
    
    Args:
        tool_name: Tool name (can be raw or display name)
        
    Returns:
        True if tool is ADK-based, False otherwise
    """
    display_name = get_tool_display_name(tool_name)
    return display_name in ADK_TOOLS or any(adk_name in tool_name for adk_name in ['ADK', 'adk'])

