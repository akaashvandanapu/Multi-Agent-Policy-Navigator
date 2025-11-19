"""
PDF MCP Tool - CrewAI tool wrapper for PDF MCP Server
Provides PDF reading capabilities via MCP protocol

Supports two implementations:
1. Legacy PyPDF2-based server (default, backward compatible)
2. FastMCP pypdf-based extractor (optional, uses newer pypdf library)
"""

from pathlib import Path
from crewai.tools import tool
from mcp_servers.pdf_mcp_server import get_pdf_mcp_server
import logging
import os

logger = logging.getLogger(__name__)

# Try to import FastMCP extractor (optional)
try:
    from mcp_servers.pdf_extractor_mcp_server import extract_pdf_markdown as fastmcp_extract_pdf_markdown
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    logger.debug("FastMCP PDF extractor not available, using legacy implementation")


def _use_fastmcp() -> bool:
    """
    Check if FastMCP should be used for PDF extraction.
    
    Can be controlled via environment variable USE_FASTMCP_PDF=1
    """
    return FASTMCP_AVAILABLE and os.getenv("USE_FASTMCP_PDF", "0") == "1"


@tool("PDF MCP Reader Tool")
def pdf_mcp_read_file(file_path: str) -> str:
    """
    Read and extract text from a PDF file using PDF MCP server.
    
    This tool uses the PDF MCP server to extract text content from PDF documents.
    It provides comprehensive text extraction with page-by-page breakdown.
    
    Supports two implementations:
    - Legacy PyPDF2-based (default, backward compatible)
    - FastMCP pypdf-based (optional, set USE_FASTMCP_PDF=1 environment variable)
    
    Args:
        file_path: Path to the PDF file to read.
                   Can be absolute or relative path.
    
    Returns:
        Formatted string with PDF content including:
        - File name and page count
        - Extracted text organized by page
        - Character count
        - Error message if file cannot be read
    """
    try:
        # Try FastMCP implementation first if enabled
        if _use_fastmcp():
            logger.debug("Using FastMCP PDF extractor")
            try:
                markdown_content = fastmcp_extract_pdf_markdown(file_path)
                
                # Format output similar to legacy format
                # Extract file name from path
                file_name = Path(file_path).name
                
                # Count pages from markdown (## Page X format)
                page_count = markdown_content.count("## Page")
                
                output = f"**PDF File Read Successfully (FastMCP)**\n\n"
                output += f"File: {file_name}\n"
                output += f"Total Pages: {page_count}\n"
                output += f"Total Characters: {len(markdown_content)}\n\n"
                output += f"**Extracted Content (Markdown):**\n\n"
                output += markdown_content
                
                return output
            except Exception as e:
                logger.warning(f"FastMCP extraction failed, falling back to legacy: {e}")
                # Fall through to legacy implementation
        
        # Legacy implementation using PyPDF2
        logger.debug("Using legacy PDF MCP server")
        mcp_server = get_pdf_mcp_server()
        result = mcp_server.read_file(file_path)
        
        if not result.get("success", False):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        # Format output
        output = f"**PDF File Read Successfully**\n\n"
        output += f"File: {result['file_name']}\n"
        output += f"Total Pages: {result['page_count']}\n"
        output += f"Total Characters: {result['character_count']}\n\n"
        output += f"**Extracted Content:**\n\n"
        output += result['text']
        
        return output
        
    except Exception as e:
        logger.error(f"Error in PDF MCP read_file tool: {e}")
        return f"Error reading PDF file: {str(e)}"

