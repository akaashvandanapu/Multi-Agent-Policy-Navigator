"""
PDF Domain Validator
Validates if a PDF document is related to agriculture and Andhra Pradesh policies
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Try to import LLM for validation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class PDFDomainValidator:
    """
    Validates if PDF content is related to agriculture and AP policies
    Uses LLM to analyze extracted text and determine domain relevance
    """
    
    def __init__(self):
        """Initialize PDF Domain Validator"""
        self.llm_client = None
        self.llm_model = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client for validation"""
        # Try OpenAI first
        openai_key = os.getenv("OPENAI_API_KEY")
        if OPENAI_AVAILABLE and openai_key:
            self.llm_client = OpenAI(api_key=openai_key)
            self.llm_model = "gpt-4o-mini"  # Use cheaper model for validation
            logger.info("PDF Domain Validator: Using OpenAI")
            return
        
        # Try Groq as fallback
        groq_key = os.getenv("GROQ_API_KEY")
        if GROQ_AVAILABLE and groq_key:
            self.llm_client = Groq(api_key=groq_key)
            self.llm_model = "llama-3.1-8b-instant"  # Fast model for validation
            logger.info("PDF Domain Validator: Using Groq")
            return
        
        logger.warning("PDF Domain Validator: No LLM available, validation will be limited")
    
    def validate_domain(self, pdf_text: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate if PDF is related to agriculture and AP policies
        
        Args:
            pdf_text: Extracted text from PDF (first 5000 chars for efficiency)
            file_name: Optional PDF file name for context
            
        Returns:
            Dictionary with validation results:
            - is_agricultural: bool
            - is_ap_related: bool
            - is_valid: bool (both agriculture AND AP)
            - confidence: float (0.0-1.0)
            - reasoning: str
        """
        logger.debug(f"Starting domain validation for file: {file_name}")
        
        # Early detection: Check if input text is an error message
        if pdf_text:
            pdf_text_lower = pdf_text.lower()
            # Check for error indicators in first 500 characters
            error_indicators = [
                pdf_text.strip().startswith("Error:"),
                "error:" in pdf_text[:500].lower(),
                "failed to" in pdf_text[:500].lower() and ("read" in pdf_text[:500].lower() or "extract" in pdf_text[:500].lower()),
                "could not extract" in pdf_text_lower[:500],
                "cannot read" in pdf_text_lower[:500],
                "pdf file not found" in pdf_text_lower[:500],
                "corrupted" in pdf_text_lower[:500] and "pdf" in pdf_text_lower[:500],
                "encrypted" in pdf_text_lower[:500] and "pdf" in pdf_text_lower[:500]
            ]
            
            if any(error_indicators):
                error_msg = "PDF text appears to be an error message rather than actual content"
                logger.warning(f"Domain validation rejected: {error_msg}")
                logger.debug(f"Error text sample (first 200 chars): {pdf_text[:200]}")
                return {
                    "is_agricultural": False,
                    "is_ap_related": False,
                    "is_valid": False,
                    "confidence": 0.0,
                    "reasoning": f"The content could not be processed due to an error, preventing any analysis of its content."
                }
        
        if not pdf_text or len(pdf_text.strip()) < 50:
            logger.warning(f"PDF text too short for validation: {len(pdf_text) if pdf_text else 0} characters")
            return {
                "is_agricultural": False,
                "is_ap_related": False,
                "is_valid": False,
                "confidence": 0.0,
                "reasoning": "PDF text is too short or empty"
            }
        
        # Limit text for efficiency (first 5000 chars should be enough)
        text_sample = pdf_text[:5000] if len(pdf_text) > 5000 else pdf_text
        logger.debug(f"Validation text sample length: {len(text_sample)} characters")
        
        # Use LLM for validation if available
        if self.llm_client:
            try:
                result = self._validate_with_llm(text_sample, file_name)
                logger.debug(f"LLM validation completed: is_valid={result.get('is_valid')}, confidence={result.get('confidence')}")
                return result
            except Exception as e:
                logger.error(f"LLM validation failed, falling back to keyword validation: {e}", exc_info=True)
                # Fall through to keyword-based validation
                return self._validate_with_keywords(text_sample, file_name)
        else:
            # Fallback to keyword-based validation
            logger.debug("Using keyword-based validation (no LLM available)")
            result = self._validate_with_keywords(text_sample, file_name)
            logger.debug(f"Keyword validation completed: is_valid={result.get('is_valid')}, confidence={result.get('confidence')}")
            return result
    
    def _validate_with_llm(self, text_sample: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """Validate using LLM for better accuracy"""
        try:
            logger.debug(f"Validating with LLM ({self.llm_model}) for file: {file_name}")
            prompt = f"""Analyze the following PDF document content and determine if it is related to:
1. Agriculture, farming, or agricultural policies (including national schemes like PM-KISAN, PMFBY, KCC)
2. Andhra Pradesh (AP) state policies, schemes, or programs

IMPORTANT: National agricultural schemes/policies (like PM-KISAN, PMFBY, KCC, etc.) are valid even if they don't explicitly mention Andhra Pradesh, because they apply to all farmers including those in Andhra Pradesh.

PDF File Name: {file_name or "Unknown"}
PDF Content Sample (first 5000 chars):
{text_sample}

Respond with a JSON object containing:
- "is_agricultural": true/false (is it about agriculture/farming/policies/schemes?)
- "is_ap_related": true/false (does it explicitly mention Andhra Pradesh OR is it a national agricultural scheme?)
- "is_national_scheme": true/false (is it a national/central government agricultural scheme like PM-KISAN, PMFBY, KCC?)
- "confidence": 0.0-1.0 (how confident are you?)
- "reasoning": brief explanation

Only respond with valid JSON, no other text."""

            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                # OpenAI format
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a document classifier. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                result_text = response.choices[0].message.content.strip()
            else:
                # Groq format
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a document classifier. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                result_text = response.choices[0].message.content.strip()
            
            logger.debug(f"LLM response received: {result_text[:200]}")
            
            # Parse JSON response
            import json
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}, response: {result_text[:500]}")
                # Fallback to keyword validation
                return self._validate_with_keywords(text_sample, file_name)
            
            # Ensure all required fields
            is_agricultural = result.get("is_agricultural", False)
            is_ap_related = result.get("is_ap_related", False)
            is_national_scheme = result.get("is_national_scheme", False)
            
            # Validation logic: Accept if agricultural AND (AP-related OR national scheme)
            # National schemes like PM-KISAN are valid even without explicit AP mention
            is_valid = is_agricultural and (is_ap_related or is_national_scheme)
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "LLM analysis")
            
            logger.debug(f"LLM validation result: is_agricultural={is_agricultural}, is_ap_related={is_ap_related}, is_national_scheme={is_national_scheme}, is_valid={is_valid}, confidence={confidence}")
            
            return {
                "is_agricultural": is_agricultural,
                "is_ap_related": is_ap_related,
                "is_valid": is_valid,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in LLM validation: {e}", exc_info=True)
            logger.warning("Falling back to keyword-based validation")
            # Fallback to keyword validation
            return self._validate_with_keywords(text_sample, file_name)
    
    def _validate_with_keywords(self, text_sample: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """Fallback keyword-based validation"""
        text_lower = text_sample.lower()
        file_lower = (file_name or "").lower()
        combined_text = f"{text_lower} {file_lower}"
        
        # Agriculture keywords
        agriculture_keywords = [
            "agriculture", "farming", "farmer", "crop", "cultivation", "paddy", "rice", "maize",
            "cotton", "groundnut", "scheme", "subsidy", "policy", "agricultural", "farm",
            "irrigation", "fertilizer", "seed", "pest", "disease", "yield", "harvest"
        ]
        
        # National agricultural scheme keywords (PM-KISAN, PMFBY, KCC, etc.)
        national_scheme_keywords = [
            "pm-kisan", "pm kisan", "pradhan mantri kisan", "kisan samman nidhi",
            "pmfby", "pm fby", "pradhan mantri fasal", "fasal bima yojana",
            "kcc", "kisan credit card", "pradhan mantri",
            "central scheme", "central sector", "government of india", "ministry of agriculture"
        ]
        
        # AP-related keywords
        ap_keywords = [
            "andhra pradesh", "ap", "andhra", "hyderabad", "amaravati", "visakhapatnam",
            "vijayawada", "guntur", "nellore", "kurnool", "anantapur", "chittoor",
            "kadapa", "prakasam", "srikakulam", "vizianagaram", "east godavari",
            "west godavari", "krishna", "guntur district"
        ]
        
        # Count matches
        agriculture_matches = sum(1 for keyword in agriculture_keywords if keyword in combined_text)
        national_scheme_matches = sum(1 for keyword in national_scheme_keywords if keyword in combined_text)
        ap_matches = sum(1 for keyword in ap_keywords if keyword in combined_text)
        
        # Determine validity
        is_agricultural = agriculture_matches >= 3  # At least 3 agriculture keywords
        is_ap_related = ap_matches >= 1  # At least 1 AP keyword
        is_national_scheme = national_scheme_matches >= 1  # At least 1 national scheme keyword
        
        # Validation logic: Accept if agricultural AND (AP-related OR national scheme)
        # National schemes like PM-KISAN are valid even without explicit AP mention
        is_valid = is_agricultural and (is_ap_related or is_national_scheme)
        
        # Calculate confidence
        confidence = min(0.9, 0.5 + (agriculture_matches * 0.1) + (ap_matches * 0.1) + (national_scheme_matches * 0.15))
        
        if is_national_scheme and not is_ap_related:
            reasoning = f"Keyword analysis: {agriculture_matches} agriculture matches, {national_scheme_matches} national scheme matches (valid: national agricultural scheme applies to all states including AP)"
        else:
            reasoning = f"Keyword analysis: {agriculture_matches} agriculture matches, {ap_matches} AP matches, {national_scheme_matches} national scheme matches"
        
        return {
            "is_agricultural": is_agricultural,
            "is_ap_related": is_ap_related,
            "is_valid": is_valid,
            "confidence": confidence,
            "reasoning": reasoning
        }


# Singleton instance
_pdf_validator = None


def get_pdf_validator() -> PDFDomainValidator:
    """Get singleton PDF Domain Validator instance"""
    global _pdf_validator
    if _pdf_validator is None:
        _pdf_validator = PDFDomainValidator()
    return _pdf_validator

