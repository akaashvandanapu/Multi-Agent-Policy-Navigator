"""
Pydantic models for structured outputs from all agents
Following CrewAI documentation patterns for output_pydantic
"""

from datetime import datetime
from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Agent 1: Query Analyzer Output
# ============================================================================

class QueryAnalysis(BaseModel):
    """Output schema for Query Understanding Agent"""
    
    original_query: str = Field(..., description="The original user query")
    query_type: Literal["policy", "cultivation", "pest", "market", "general", "document_upload", "out_of_scope"] = Field(
        ..., description="Classified type of query"
    )
    entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Extracted entities: crop names, schemes, locations, pests, diseases"
    )
    complexity: Literal["simple", "moderate", "complex"] = Field(
        ..., description="Query complexity level"
    )
    required_agents: List[str] = Field(
        ..., description="List of agent IDs required to answer this query"
    )
    context_needed: bool = Field(
        default=False, description="Whether historical context is needed"
    )
    is_ap_query: bool = Field(
        default=True, description="Whether the query is about Andhra Pradesh"
    )
    detected_regions: List[str] = Field(
        default_factory=list,
        description="List of detected regions (states, cities, districts) in the query"
    )
    region_type: Literal["ap", "non_ap", "mixed"] = Field(
        default="ap", description="Type of region detected: ap (defaults to AP if no region mentioned), non_ap, or mixed"
    )
    is_out_of_scope: bool = Field(
        default=False, description="Whether the query is completely out of scope (non-agricultural)"
    )
    
    @field_validator('entities')
    @classmethod
    def validate_entities(cls, v):
        """Ensure entities dict has expected keys"""
        expected_keys = ['crop', 'scheme', 'location', 'pest', 'disease', 'region_limitation']
        for key in expected_keys:
            if key not in v:
                v[key] = []
        return v


# ============================================================================
# Agent 2: Policy Researcher Output
# ============================================================================

class PolicyResponse(BaseModel):
    """Output schema for Policy Retrieval Agent"""
    
    scheme_name: str = Field(..., description="Name of the policy/scheme")
    description: str = Field(..., description="Detailed description of the scheme")
    eligibility: List[str] = Field(
        default_factory=list,
        description="Eligibility criteria"
    )
    benefits: List[str] = Field(
        default_factory=list,
        description="Benefits provided by the scheme"
    )
    application_process: str = Field(
        default="", description="How to apply for the scheme"
    )
    documents_required: List[str] = Field(
        default_factory=list,
        description="Documents needed for application"
    )
    contact_info: Dict[str, str] = Field(
        default_factory=dict,
        description="Contact information (phone, email, website, office)"
    )
    source_documents: List[str] = Field(
        default_factory=list,
        description="Source PDF documents used"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence score of the retrieval (0-1)"
    )


# ============================================================================
# Agent 3: Crop Specialist Output
# ============================================================================

class CropVariety(BaseModel):
    """Crop variety information"""
    name: str = Field(..., description="Variety name")
    description: str = Field(..., description="Characteristics and suitability")
    season: Optional[str] = Field(None, description="Recommended season")


class SowingDetails(BaseModel):
    """Sowing details"""
    sowing_time: str = Field(..., description="Best time for sowing")
    spacing: str = Field(..., description="Row and plant spacing")
    seed_rate: str = Field(..., description="Seeds per hectare")


class FertilizerSchedule(BaseModel):
    """Fertilizer application schedule"""
    stage: str = Field(..., description="Growth stage")
    npk: str = Field(..., description="NPK ratio or details")
    details: str = Field(..., description="Application method")


class CropEconomics(BaseModel):
    """Crop economics information"""
    expected_yield: str = Field(..., description="Yield per hectare")
    cost_of_cultivation: str = Field(..., description="Estimated cost")
    expected_profit: Optional[str] = Field(None, description="Expected profit")


class CropGuidance(BaseModel):
    """Output schema for Crop Cultivation Agent"""
    
    crop_name: str = Field(..., description="Name of the crop")
    varieties: List[CropVariety] = Field(
        default_factory=list,
        description="Recommended varieties with descriptions"
    )
    sowing_details: SowingDetails = Field(
        ..., description="Sowing timing, spacing, seed rate"
    )
    fertilizer_schedule: List[FertilizerSchedule] = Field(
        default_factory=list,
        description="Stage-wise fertilizer applications"
    )
    irrigation_schedule: List[str] = Field(
        default_factory=list,
        description="Irrigation timing and frequency"
    )
    best_practices: List[str] = Field(
        default_factory=list,
        description="Best practices for cultivation"
    )
    economics: CropEconomics = Field(
        ..., description="Cost and yield estimates"
    )


# ============================================================================
# Agent 4: Pest Advisor Output
# ============================================================================

class PestInfo(BaseModel):
    """Pest/disease information"""
    symptoms: str = Field(..., description="Visual symptoms and signs")
    affected_parts: str = Field(..., description="Which plant parts are affected")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Severity level"
    )


class ControlMeasures(BaseModel):
    """Control measures for pests/diseases"""
    cultural: List[str] = Field(
        default_factory=list,
        description="Cultural control practices"
    )
    biological: List[str] = Field(
        default_factory=list,
        description="Biological control agents"
    )
    chemical: List[str] = Field(
        default_factory=list,
        description="Chemical control options with dosages"
    )


class PestManagement(BaseModel):
    """Output schema for Pest Control Advisor"""
    
    pest_disease_name: str = Field(..., description="Common name of pest or disease")
    pest_info: PestInfo = Field(..., description="Pest/disease information")
    control_measures: ControlMeasures = Field(
        ..., description="Control measures (cultural, biological, chemical)"
    )
    prevention: List[str] = Field(
        default_factory=list,
        description="Prevention methods"
    )
    safe_period: int = Field(
        ..., ge=0,
        description="Days after chemical application before safe consumption"
    )
    estimated_yield_loss: str = Field(
        ..., description="Estimated yield loss if not controlled"
    )


# ============================================================================
# Agent 5: Market Analyst Output
# ============================================================================

class MarketInfo(BaseModel):
    """Output schema for Market & Weather Analyst"""
    
    info_type: Literal["msp", "weather", "market_price", "announcement"] = Field(
        ..., description="Type of real-time information"
    )
    crop_name: Optional[str] = Field(
        None, description="Crop name (if applicable)"
    )
    location: Optional[str] = Field(
        None, description="Location (if applicable)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant data fields"
    )
    last_updated: str = Field(
        ..., description="ISO 8601 timestamp of last update"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of source URLs"
    )
    reliability_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Reliability assessment (0-1)"
    )


# ============================================================================
# Agent 6: Non-AP Web Researcher Output
# ============================================================================

class WebSearchResponse(BaseModel):
    """Output schema for Non-AP Region Web Research Agent"""
    
    data_source: Literal["web_searched"] = Field(
        default="web_searched",
        description="Always 'web_searched' to indicate data is from web search, not local database"
    )
    query_type: Literal["policy", "cultivation", "pest", "market", "general"] = Field(
        ..., description="Type of query being researched"
    )
    region: str = Field(
        ..., description="Detected non-AP region(s) for this query"
    )
    search_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured web search results with key information found"
    )
    recommend_market_analyst: bool = Field(
        default=False,
        description="True if market-related information was found and market_analyst should be called"
    )
    market_related_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Market-related findings if recommend_market_analyst is True (MSP, prices, etc.)"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of source URLs from web search"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Reliability score of the web search results (0-1)"
    )
    disclaimer: str = Field(
        ...,
        description="Text indicating that this data is web-searched and not from the local database"
    )


# ============================================================================
# Agent 7: Response Synthesizer Output
# ============================================================================

class AgentContribution(BaseModel):
    """Individual agent contribution"""
    agent_id: str = Field(..., description="Agent identifier")
    contribution: str = Field(..., description="Summary of agent's contribution")


class FinalResponse(BaseModel):
    """Final structured output from Response Synthesizer"""
    
    query: str = Field(..., description="Original user query")
    is_out_of_scope: bool = Field(
        default=False,
        description="True if the query is out of scope (non-agricultural)"
    )
    response_text: str = Field(
        ..., min_length=100,
        description="Plain text summary (minimum 100 characters, no markdown)"
    )
    response_markdown: Optional[str] = Field(
        None,
        description="Detailed markdown response with proper formatting. Optional for out-of-scope queries."
    )
    agent_contributions: Dict[str, str] = Field(
        default_factory=dict,
        description="Summary of each agent's contribution"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="All source documents and URLs"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall confidence (0-1)"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Relevant follow-up questions (2-3 questions). Empty for out-of-scope queries."
    )
    
    @field_validator('response_markdown')
    @classmethod
    def validate_markdown(cls, v):
        """Validate markdown length if provided"""
        if v is not None and len(v) < 200:
            raise ValueError("response_markdown must be at least 200 characters if provided")
        return v


# ============================================================================
# PDF Analysis Output (CrewAI Agent with PDF MCP Tool)
# ============================================================================

class PDFAnalysis(BaseModel):
    """Output schema for PDF Processing Agent (CrewAI Agent with PDF MCP Tool)"""
    
    extracted_text: str = Field(
        ..., description="Full text extracted from PDF document"
    )
    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data extracted from PDF (tables, forms, key-value pairs)"
    )
    answers: Dict[str, str] = Field(
        default_factory=dict,
        description="Answers to questions about the PDF content (question: answer pairs)"
    )
    summary: str = Field(
        ..., description="Summary of the PDF document content"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence score of the PDF analysis (0-1)"
    )
    file_name: str = Field(
        ..., description="Name of the processed PDF file"
    )
    page_count: int = Field(
        ..., ge=0,
        description="Number of pages in the PDF document"
    )

