from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AnalysisReasoning(BaseModel):
    """Elite schema for Chain-of-Thought reasoning."""
    steps: List[str] = Field(..., description="Logical internal reasoning steps")
    conclusion: str = Field(..., description="Final logical deduction")

class SkillExtractionResult(BaseModel):
    """Structured output for JD parsing."""
    technical_skills: List[str]
    soft_skills: List[str]
    experience_level: str
    education: str
    reasoning: Optional[AnalysisReasoning] = None

class RAGAnswerResult(BaseModel):
    """Structured output for Q&A."""
    answer: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    reasoning: Optional[AnalysisReasoning] = None

class CandidateFitResult(BaseModel):
    """Structured output for Candidate evaluation."""
    overall_fit_score: float
    technical_readiness: float
    cultural_alignment: float
    retention_probability: float
    reasoning: Optional[AnalysisReasoning] = None
