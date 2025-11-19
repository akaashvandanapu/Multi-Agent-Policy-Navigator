"""
LLM Configuration Helper
Reads LLM provider and model settings from environment variables
Supports PRIMARY_LLM_PROVIDER/MODEL and FALLBACK_LLM_PROVIDER/MODEL
"""

import os
import logging
from typing import Optional, Tuple
from crewai import LLM

logger = logging.getLogger(__name__)


def get_llm_provider_and_model(use_fallback: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """
    Get LLM provider and model from environment variables
    
    Args:
        use_fallback: If True, get fallback provider/model instead of primary
    
    Returns:
        Tuple of (provider, model) or (None, None) if not configured
    """
    if use_fallback:
        provider = os.getenv("FALLBACK_LLM_PROVIDER", "").strip()
        model = os.getenv("FALLBACK_LLM_MODEL", "").strip()
        prefix = "FALLBACK"
    else:
        provider = os.getenv("PRIMARY_LLM_PROVIDER", "").strip()
        model = os.getenv("PRIMARY_LLM_MODEL", "").strip()
        prefix = "PRIMARY"
    
    if provider and model:
        logger.debug(f"{prefix} LLM configured: provider={provider}, model={model}")
        return provider.lower(), model
    
    logger.debug(f"{prefix} LLM not configured via environment variables")
    return None, None


def get_llm_instance(use_fallback: bool = False, default_model: Optional[str] = None) -> LLM:
    """
    Create LLM instance from environment variables
    
    Args:
        use_fallback: If True, use fallback LLM configuration
        default_model: Default model to use if no env vars configured (e.g., "gpt-4o-mini")
    
    Returns:
        LLM instance configured with provider and model from env vars
    """
    provider, model = get_llm_provider_and_model(use_fallback=use_fallback)
    
    if provider and model:
        # Get API keys based on provider
        api_key = None
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found for PRIMARY LLM provider")
                # Try fallback if primary not available
                if not use_fallback:
                    return get_llm_instance(use_fallback=True, default_model=default_model)
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY not found for PRIMARY LLM provider")
                # Try fallback if primary not available
                if not use_fallback:
                    return get_llm_instance(use_fallback=True, default_model=default_model)
        
        # Format model name based on provider
        formatted_model = model
        if provider == "groq" and not model.startswith("groq/"):
            formatted_model = f"groq/{model}"
        
        logger.info(f"Using LLM: {formatted_model} (provider: {provider})")
        
        if api_key:
            return LLM(model=formatted_model, api_key=api_key)
        else:
            # If no API key but provider/model specified, try without explicit key
            # (may use environment variable from litellm)
            return LLM(model=formatted_model)
    
    # Fallback to default or environment-based detection
    if default_model:
        logger.info(f"Using default LLM model: {default_model}")
        return LLM(model=default_model)
    
    # Try to auto-detect from available API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if openai_key:
        default = "gpt-4o-mini"
        logger.info(f"Auto-detected OpenAI API key, using {default}")
        return LLM(model=default, api_key=openai_key)
    elif groq_key:
        default = "groq/llama-3.3-70b-versatile"
        logger.info(f"Auto-detected Groq API key, using {default}")
        return LLM(model=default)
    else:
        logger.warning("No LLM API keys found, using default gpt-4o-mini (may fail without key)")
        return LLM(model="gpt-4o-mini")


def get_embedding_model() -> str:
    """
    Get embedding model from environment variable
    
    Returns:
        Embedding model name (default: 'all-MiniLM-L6-v2')
    """
    model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
    
    # Remove sentence-transformers/ prefix if present (it's implied)
    if model.startswith("sentence-transformers/"):
        model = model.replace("sentence-transformers/", "")
    
    logger.debug(f"Using embedding model: {model}")
    return model

