"""
Guardrail Factory
Creates hallucination guardrails for different task types with appropriate context
"""

import logging
from typing import Optional, Dict, Any
from crewai.tasks.hallucination_guardrail import HallucinationGuardrail
from crewai import LLM

from policy_navigator.guardrails.guardrail_config import (
    get_threshold_for_task,
    get_guardrail_llm
)

logger = logging.getLogger(__name__)


def extract_rag_context(tool_response: str) -> str:
    """
    Extract context from RAG tool response
    
    Args:
        tool_response: RAG tool output string
    
    Returns:
        Extracted context for guardrail validation
    """
    if not tool_response or len(tool_response.strip()) < 50:
        return "No relevant information found in RAG search results."
    
    # RAG tool returns formatted text with source, category, score, and content
    # Extract the content portions for context
    context_parts = []
    
    # Split by result markers
    if "**Result" in tool_response:
        results = tool_response.split("**Result")
        for result in results[1:]:  # Skip first empty part
            # Extract content section
            if "Content:" in result:
                content = result.split("Content:")[1]
                # Remove source/category/score lines, keep content
                lines = content.split("\n")
                content_lines = []
                for line in lines:
                    if not line.startswith("Source:") and not line.startswith("Category:") and not line.startswith("Relevance Score:"):
                        content_lines.append(line)
                context_parts.append("\n".join(content_lines).strip())
    else:
        # Fallback: use entire response
        context_parts.append(tool_response)
    
    context = "\n\n".join(context_parts)
    
    # Limit context size (first 3000 chars should be enough)
    if len(context) > 3000:
        context = context[:3000] + "..."
    
    return context if context else "RAG search returned results but content extraction failed."


def extract_pdf_context(tool_response: str) -> str:
    """
    Extract context from PDF MCP tool response
    
    Args:
        tool_response: PDF MCP tool output string
    
    Returns:
        Extracted context for guardrail validation
    """
    if not tool_response or len(tool_response.strip()) < 50:
        return "No content extracted from PDF."
    
    # PDF MCP tool returns formatted text with file info and extracted content
    # Extract the actual PDF text content
    if "**Extracted Content:**" in tool_response:
        # Extract content after the marker
        content = tool_response.split("**Extracted Content:**")[1]
        # Remove any trailing metadata
        lines = content.split("\n")
        content_lines = []
        for line in lines:
            if not line.startswith("**") and not line.startswith("File:") and not line.startswith("Total"):
                content_lines.append(line)
        context = "\n".join(content_lines).strip()
    else:
        # Fallback: use entire response
        context = tool_response
    
    # Limit context size (first 5000 chars for PDFs)
    if len(context) > 5000:
        context = context[:5000] + "..."
    
    return context if context else "PDF content extraction failed."


def create_guardrail(
    context: str,
    task_name: str,
    llm: Optional[LLM] = None,
    threshold: Optional[float] = None,
    tool_response: Optional[str] = None
) -> HallucinationGuardrail:
    """
    Create a hallucination guardrail with specified context
    
    Args:
        context: Reference context for validation
        task_name: Name of the task (for threshold lookup)
        llm: Optional LLM instance (uses default if not provided)
        threshold: Optional custom threshold (uses task default if not provided)
        tool_response: Optional tool response to include in context
    
    Returns:
        HallucinationGuardrail instance
    """
    if llm is None:
        llm = get_guardrail_llm()
    
    if threshold is None:
        threshold = get_threshold_for_task(task_name)
    
    logger.info(f"Creating guardrail for {task_name} with threshold {threshold}")
    
    guardrail = HallucinationGuardrail(
        context=context,
        llm=llm,
        threshold=threshold
    )
    
    # Add tool response if provided
    if tool_response:
        # Note: HallucinationGuardrail may not have tool_response parameter in all versions
        # This is a best-effort approach
        try:
            # Combine context and tool response
            enhanced_context = f"{context}\n\nTool Response:\n{tool_response}"
            guardrail = HallucinationGuardrail(
                context=enhanced_context,
                llm=llm,
                threshold=threshold
            )
        except Exception as e:
            logger.warning(f"Could not add tool_response to guardrail: {e}")
    
    return guardrail


def create_rag_guardrail(
    rag_tool_response: str,
    task_name: str = "rag_based_task",
    llm: Optional[LLM] = None
) -> HallucinationGuardrail:
    """
    Create guardrail for RAG-based tasks
    
    Args:
        rag_tool_response: RAG tool response string
        task_name: Task name for threshold lookup
        llm: Optional LLM instance
    
    Returns:
        HallucinationGuardrail instance
    """
    context = extract_rag_context(rag_tool_response)
    return create_guardrail(
        context=context,
        task_name=task_name,
        llm=llm
    )


def create_pdf_guardrail(
    pdf_tool_response: str,
    task_name: str = "pdf_processing_task",
    llm: Optional[LLM] = None
) -> HallucinationGuardrail:
    """
    Create guardrail for PDF processing tasks
    
    Args:
        pdf_tool_response: PDF MCP tool response string
        task_name: Task name for threshold lookup
        llm: Optional LLM instance
    
    Returns:
        HallucinationGuardrail instance
    """
    context = extract_pdf_context(pdf_tool_response)
    return create_guardrail(
        context=context,
        task_name=task_name,
        llm=llm
    )


def create_synthesis_guardrail(
    task_outputs: Dict[str, Any],
    task_name: str = "synthesis_task",
    llm: Optional[LLM] = None
) -> HallucinationGuardrail:
    """
    Create guardrail for synthesis task using all previous task outputs
    
    Args:
        task_outputs: Dictionary of task outputs (task_name -> output)
        task_name: Task name for threshold lookup
        llm: Optional LLM instance
    
    Returns:
        HallucinationGuardrail instance
    """
    # Build comprehensive context from all task outputs
    context_parts = []
    
    for output_task_name, output in task_outputs.items():
        if output:
            # Convert output to string if needed
            if hasattr(output, 'model_dump'):
                output_str = str(output.model_dump())
            elif isinstance(output, dict):
                output_str = str(output)
            else:
                output_str = str(output)
            
            context_parts.append(f"Task: {output_task_name}\n{output_str}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # Limit context size (first 5000 chars)
    if len(context) > 5000:
        context = context[:5000] + "..."
    
    if not context:
        context = "No previous task outputs available for validation."
    
    return create_guardrail(
        context=context,
        task_name=task_name,
        llm=llm
    )

