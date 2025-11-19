"""
Guardrail Configuration
Defines thresholds, LLM settings, and context extraction strategies for hallucination guardrails
"""

import os
import logging
from typing import Optional
from crewai import LLM

logger = logging.getLogger(__name__)


class GuardrailConfig:
    """Configuration for hallucination guardrails"""
    
    # Thresholds for different task types (0-10 scale)
    THRESHOLDS = {
        'rag_based': 7.0,  # RAG-based tasks (policy, crop, pest)
        'web_search': 6.5,  # Ollama Web Search MCP tasks (market, non_ap)
        'pdf_processing': 7.5,  # PDF processing (document-based, high-stakes)
        'synthesis': 7.0,  # Synthesis task (multiple sources)
        'query_analysis': 6.0,  # Query analysis (lower priority)
    }
    
    # LLM model for guardrail evaluation (efficient models)
    GUARDRAIL_MODELS = {
        'openai': 'gpt-4o-mini',
        'groq': 'llama-3.1-8b-instant',
    }
    
    @staticmethod
    def get_threshold(task_type: str) -> float:
        """Get threshold for a task type"""
        return GuardrailConfig.THRESHOLDS.get(task_type, 7.0)
    
    @staticmethod
    def get_guardrail_llm() -> LLM:
        """
        Get LLM instance for guardrail evaluation
        Uses efficient models to minimize cost
        Uses PRIMARY_LLM_PROVIDER/MODEL if configured, otherwise falls back to auto-detection
        """
        from policy_navigator.config.llm_config import get_llm_instance, get_llm_provider_and_model
        
        # Try to use PRIMARY LLM configuration if available
        provider, model = get_llm_provider_and_model(use_fallback=False)
        
        if provider and model:
            # Use primary LLM configuration
            try:
                llm = get_llm_instance(use_fallback=False, default_model=None)
                logger.info(f"Guardrail LLM: Using PRIMARY LLM ({provider}: {model})")
                return llm
            except Exception as e:
                logger.warning(f"Failed to use PRIMARY LLM for guardrail, trying fallback: {e}")
        
        # Try fallback LLM configuration
        provider, model = get_llm_provider_and_model(use_fallback=True)
        if provider and model:
            try:
                llm = get_llm_instance(use_fallback=True, default_model=None)
                logger.info(f"Guardrail LLM: Using FALLBACK LLM ({provider}: {model})")
                return llm
            except Exception as e:
                logger.warning(f"Failed to use FALLBACK LLM for guardrail: {e}")
        
        # Fallback to efficient models for guardrail
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = GuardrailConfig.GUARDRAIL_MODELS['openai']
            logger.info(f"Guardrail LLM: Using OpenAI {model}")
            return LLM(model=model, api_key=openai_key)
        
        # Try Groq as fallback
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            model = GuardrailConfig.GUARDRAIL_MODELS['groq']
            logger.info(f"Guardrail LLM: Using Groq {model}")
            return LLM(model=f"groq/{model}")
        
        # Fallback to default (will use environment LLM config)
        logger.warning("No guardrail LLM API key found, using default LLM")
        return LLM(model="gpt-4o-mini")


def get_threshold_for_task(task_name: str) -> float:
    """
    Get appropriate threshold for a task
    
    Args:
        task_name: Name of the task (e.g., 'policy_research_task', 'market_info_task')
    
    Returns:
        Threshold value (0-10)
    """
    # Map task names to task types
    task_type_mapping = {
        'policy_research_task': 'rag_based',
        'crop_guidance_task': 'rag_based',
        'pest_management_task': 'rag_based',
        'market_info_task': 'web_search',
        'non_ap_research_task': 'web_search',
        'pdf_processing_task': 'pdf_processing',
        'synthesis_task': 'synthesis',
        'query_analysis_task': 'query_analysis',
    }
    
    task_type = task_type_mapping.get(task_name, 'rag_based')
    return GuardrailConfig.get_threshold(task_type)


def get_guardrail_llm() -> LLM:
    """Get LLM instance for guardrail evaluation"""
    return GuardrailConfig.get_guardrail_llm()

