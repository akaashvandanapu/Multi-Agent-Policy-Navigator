"""
PDF Extractor MCP Server using FastMCP
An MCP server that uses the pypdf library to extract text from PDF files and format it as Markdown.
Can be run as a standalone stdio server or integrated with CrewAI tools.
"""

import sys
from pathlib import Path
from urllib.parse import urlparse
import tempfile
import logging

logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP
except ImportError:
    # Fallback: try old import path
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as e:
        raise ImportError(
            "FastMCP is not available. Please install with: pip install fastmcp"
        ) from e

# Simple file download utility (replaces mcp.util.file_util.download_file)
def download_file(file_url_or_path: str) -> str:
    """
    Download a file from URL or return local path.
    
    Args:
        file_url_or_path: Local file path or URL
        
    Returns:
        Local file path (downloads to temp file if URL)
    """
    # First check if it's a local path that exists
    path = Path(file_url_or_path)
    if path.exists():
        return str(path.resolve())
    
    # Check if it's a URL by parsing
    parsed = urlparse(file_url_or_path)
    
    # If it's not a URL (no scheme or file:// scheme), treat as local path
    if not parsed.scheme or parsed.scheme == 'file':
        # File doesn't exist, raise error
        raise FileNotFoundError(f"File not found: {file_url_or_path}")
    
    # If it's a URL (http/https), download it
    if parsed.scheme in ('http', 'https'):
        try:
            import requests
            response = requests.get(file_url_or_path, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            suffix = Path(parsed.path).suffix or '.pdf'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
        except ImportError:
            # Fallback to urllib if requests not available
            from urllib.request import urlretrieve
            suffix = Path(parsed.path).suffix or '.pdf'
            tmp_file, _ = urlretrieve(file_url_or_path)
            return tmp_file
    
    # Unknown scheme
    raise ValueError(f"Unsupported file scheme: {parsed.scheme} (file: {file_url_or_path})")

try:
    from pypdf import PdfReader
except ImportError as e:
    raise ImportError(
        "pypdf is not available. Please install with: pip install pypdf"
    ) from e

# Initialize the FastMCP server with a unique name
mcp_server = FastMCP(
    name="pypdf-extractor",
    instructions="An MCP server that uses the pypdf library to extract text from PDF files and format it as Markdown.",
    version="0.1.0"
)


def _extract_pdf_markdown_impl(file_url_or_path: str) -> str:
    """
    Extracts all text content from a PDF file specified by a local path or a remote URL, 
    and formats the output as simple Markdown.

    Args:
        file_url_or_path: The local file path or a public URL to the PDF file.
                         Can be absolute or relative to project root.
                         For relative paths, will check data/ directory first.

    Returns:
        The extracted PDF text content formatted as Markdown.
    """
    
    logger.debug(f"Attempting to process file: {file_url_or_path}")
    print(f"Attempting to process file: {file_url_or_path}", file=sys.stderr)
    try:
        # Handle relative paths - check if it's a relative path first
        file_path_obj = Path(file_url_or_path)
        
        # If it's not an absolute path and doesn't exist, try relative to project root
        if not file_path_obj.is_absolute() and not file_path_obj.exists():
            # Try project root and data directory
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"
            
            # Try project root first
            potential_path = project_root / file_url_or_path
            if potential_path.exists():
                file_url_or_path = str(potential_path)
                logger.debug(f"Found file at project root: {file_url_or_path}")
            # Try data directory
            elif (data_dir / file_url_or_path).exists():
                file_url_or_path = str(data_dir / file_url_or_path)
                logger.debug(f"Found file in data directory: {file_url_or_path}")
        
        # Use download_file to handle both local paths and remote URLs
        # This function downloads the file and returns the local path to the temp file
        try:
            local_path = download_file(file_url_or_path)
            logger.debug(f"File resolved to: {local_path}")
        except FileNotFoundError as e:
            error_msg = f"Error: PDF file not found at path or URL: {file_url_or_path}"
            logger.error(error_msg)
            return error_msg
        
        # Read the PDF content
        try:
            reader = PdfReader(local_path)
            logger.debug(f"PDF reader created successfully, checking pages...")
        except Exception as e:
            error_msg = f"Error: Failed to read PDF file: {str(e)}. The file may be corrupted or not a valid PDF."
            logger.error(error_msg, exc_info=True)
            return error_msg
        
        if len(reader.pages) == 0:
            error_msg = "Error: PDF file appears to be empty (no pages found)"
            logger.error(error_msg)
            return error_msg
        
        logger.debug(f"PDF has {len(reader.pages)} pages, extracting text...")
        markdown_output = []
        pages_with_text = 0
        
        # Iterate over all pages and extract text
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                
                # Simple Markdown formatting: Page heading and content
                markdown_output.append(f"## Page {i + 1}")
                
                # Replace common multiple newlines with single ones for cleaner Markdown
                clean_text = page_text.replace('\n\n', '\n').strip()
                if clean_text:  # Only add non-empty pages
                    markdown_output.append(clean_text)
                    markdown_output.append("\n---\n")  # Separator between pages
                    pages_with_text += 1
            except Exception as e:
                # If a single page fails, log and continue
                logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                print(f"Warning: Failed to extract text from page {i + 1}: {e}", file=sys.stderr)
                markdown_output.append(f"## Page {i + 1}")
                markdown_output.append(f"[Error extracting text from this page: {str(e)}]")
                markdown_output.append("\n---\n")
        
        # Check if we extracted any text
        full_text = "\n".join(markdown_output)
        # Remove page headers and separators to check actual content
        content_text = full_text.replace("## Page", "").replace("---", "").replace("[Error extracting text from this page:", "").strip()
        
        # Validate extracted content before returning
        if not content_text or len(content_text) < 10:
            error_msg = "Error: Could not extract any readable text from the PDF. The PDF may contain only images or be encrypted."
            logger.error(f"{error_msg} (extracted {pages_with_text} pages with text, total length: {len(content_text)})")
            return error_msg
        
        logger.info(f"Successfully extracted text from PDF: {len(reader.pages)} pages, {pages_with_text} pages with content, {len(full_text)} total characters")
        logger.debug(f"Extracted content preview (first 200 chars): {full_text[:200]}")
        
        # Final validation: ensure the content doesn't look like an error message
        # (though all error messages should start with "Error:", this is a safety check)
        if full_text.strip().startswith("Error:"):
            logger.warning(f"Extracted content appears to be an error message: {full_text[:200]}")
            return full_text  # Return as-is since it's already formatted as an error
        
        # Join all parts to form the final Markdown string
        return full_text
    
    except FileNotFoundError as e:
        error_msg = f"Error: PDF file not found at path or URL: {file_url_or_path}"
        logger.error(error_msg, exc_info=True)
        return error_msg
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Unexpected error during PDF processing: {error_type}: {error_msg}", exc_info=True)
        
        # Check if it's a requests error (URL download failed)
        if "requests" in error_type.lower() or "http" in error_type.lower() or "url" in error_type.lower():
            return f"Error: Failed to download PDF from URL: {error_msg}"
        
        # Ensure all error messages start with "Error:" prefix
        return f"Error: An unexpected error occurred during PDF processing: {error_type}: {error_msg}"


# Register the function as a tool with FastMCP (for MCP server usage)
mcp_server.tool()(_extract_pdf_markdown_impl)

# Export the actual implementation function for direct use (not through MCP)
def extract_pdf_markdown(file_url_or_path: str) -> str:
    """
    Extract PDF markdown directly (bypassing MCP tool wrapper).
    
    This is the actual implementation function that can be called directly
    without going through the MCP server interface. Use this when calling
    from Python code directly.
    """
    return _extract_pdf_markdown_impl(file_url_or_path)


def get_server() -> FastMCP:
    """
    Get the FastMCP server instance.
    
    Returns:
        The configured FastMCP server instance
    """
    return mcp_server


# The main execution block. We use 'stdio' transport for easy integration with CrewAI.
if __name__ == "__main__":
    print("PyPDF MCP Server running on stdio transport. Ready for input...", file=sys.stderr)
    # This call tells FastMCP to listen for tool calls over standard input (stdin)
    # and print results to standard output (stdout), which CrewAI manages.
    mcp_server.run(transport='stdio')

