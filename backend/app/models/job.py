"""
Pydantic Models for Job Postings.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class JobBase(BaseModel):
    """Base job model with common fields."""
    title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=100)
    location: str = Field(default="Remote")
    job_type: str = Field(default="Full-time")  # Full-time, Part-time, Contract
    experience_required: str = Field(default="0-2 years")
    salary_range: Optional[str] = None


class JobSkills(BaseModel):
    """Job skill requirements."""
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    

class JobCreate(JobBase, JobSkills):
    """Model for creating a new job posting."""
    description: str = Field(..., min_length=20, description="Full job description")
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)


class JobInDB(JobBase, JobSkills):
    """Job model as stored in database."""
    id: Optional[str] = Field(default=None, alias="_id")
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    job_embedding: Optional[List[float]] = None
    expanded_skills: Optional[List[str]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class JobResponse(JobBase, JobSkills):
    """Job response model for API."""
    id: str = Field(..., alias="_id")
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    expanded_skills: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        populate_by_name = True


class JobListResponse(BaseModel):
    """Paginated list of jobs."""
    total: int
    page: int
    page_size: int
    jobs: List[JobResponse]


class JobRecommendation(BaseModel):
    """A single job recommendation with match details."""
    job: JobResponse
    match_score: float = Field(..., ge=0, le=1, description="Overall match score 0-1")
    semantic_score: float = Field(..., ge=0, le=1, description="Semantic similarity score")
    skill_score: float = Field(..., ge=0, le=1, description="Skill match score")
    preference_score: float = Field(..., ge=0, le=1, description="Preference alignment score")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    match_explanation: str = Field(default="", description="Human-readable match explanation")


class RecommendationResponse(BaseModel):
    """Full recommendation response for a candidate."""
    candidate_id: str
    candidate_name: str
    total_jobs_analyzed: int
    recommendations: List[JobRecommendation]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
