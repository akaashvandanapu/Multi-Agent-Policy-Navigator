"""
PDF MCP Server Wrapper
Creates a simple local PDF MCP server using PyPDF2 for text extraction
This implements MCP protocol for PDF reading capabilities
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
import PyPDF2
import logging

logger = logging.getLogger(__name__)


class PDFMCPServer:
    """
    Simple PDF MCP Server implementation using PyPDF2
    Provides PDF text extraction capabilities via MCP protocol
    """
    
    def __init__(self):
        """Initialize PDF MCP Server"""
        self.server_name = "pdf_reader"
        logger.info("PDF MCP Server initialized")
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read and extract text from PDF file (MCP tool: read_file)
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            pdf_path = Path(file_path)
            
            if not pdf_path.exists():
                return {
                    "error": f"File not found: {file_path}",
                    "success": False
                }
            
            if pdf_path.suffix.lower() != '.pdf':
                return {
                    "error": f"File is not a PDF: {pdf_path.suffix}",
                    "success": False
                }
            
            # Extract text from PDF
            text = ""
            page_count = 0
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num} ---\n"
                    text += page_text + "\n"
            
            return {
                "success": True,
                "text": text,
                "page_count": page_count,
                "file_name": pdf_path.name,
                "file_path": str(pdf_path),
                "character_count": len(text)
            }
            
        except PyPDF2.errors.PdfReadError as e:
            return {
                "error": f"Failed to read PDF: {str(e)}",
                "success": False
            }
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return {
                "error": f"Error processing PDF: {str(e)}",
                "success": False
            }
    
    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """
        List PDF files in a directory (MCP tool: list_files)
        
        Args:
            directory: Directory path to list
            
        Returns:
            Dictionary with list of PDF files
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {
                    "error": f"Directory not found: {directory}",
                    "success": False
                }
            
            pdf_files = [
                {
                    "name": f.name,
                    "path": str(f),
                    "size": f.stat().st_size
                }
                for f in dir_path.iterdir()
                if f.is_file() and f.suffix.lower() == '.pdf'
            ]
            
            return {
                "success": True,
                "files": pdf_files,
                "count": len(pdf_files)
            }
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return {
                "error": f"Error listing files: {str(e)}",
                "success": False
            }


# Singleton instance
_pdf_mcp_server = None


def get_pdf_mcp_server() -> PDFMCPServer:
    """Get singleton PDF MCP Server instance"""
    global _pdf_mcp_server
    if _pdf_mcp_server is None:
        _pdf_mcp_server = PDFMCPServer()
    return _pdf_mcp_server

