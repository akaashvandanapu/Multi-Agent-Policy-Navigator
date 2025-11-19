"""
Hallucination Guardrail Module
Provides guardrails to validate AI-generated content against reference context
"""

from policy_navigator.guardrails.guardrail_factory import (
    create_guardrail,
    create_rag_guardrail,
    create_pdf_guardrail,
    create_synthesis_guardrail
)
from policy_navigator.guardrails.guardrail_config import (
    GuardrailConfig,
    get_threshold_for_task,
    get_guardrail_llm
)

__all__ = [
    'create_guardrail',
    'create_rag_guardrail',
    'create_pdf_guardrail',
    'create_synthesis_guardrail',
    'GuardrailConfig',
    'get_threshold_for_task',
    'get_guardrail_llm',
]

