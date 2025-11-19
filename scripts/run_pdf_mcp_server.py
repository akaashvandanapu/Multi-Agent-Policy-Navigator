"""
Standalone execution script for PDF Extractor MCP Server
Run this script to start the FastMCP PDF extractor server on stdio transport.

Usage:
    python -m scripts.run_pdf_mcp_server
    
Or directly:
    python scripts/run_pdf_mcp_server.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.pdf_extractor_mcp_server import mcp_server

if __name__ == "__main__":
    print("PDF Extractor MCP Server starting...", file=sys.stderr)
    print("Running on stdio transport. Ready for input...", file=sys.stderr)
    print("Press Ctrl+C to stop the server.", file=sys.stderr)
    
    try:
        # Run the FastMCP server on stdio transport
        # This will listen for tool calls over standard input (stdin)
        # and print results to standard output (stdout)
        mcp_server.run(transport='stdio')
    except KeyboardInterrupt:
        print("\nServer stopped by user.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error running PDF MCP server: {e}", file=sys.stderr)
        sys.exit(1)

