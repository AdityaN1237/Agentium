"""
Pydantic Models for Candidates.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


class CandidateBase(BaseModel):
    """Base candidate model with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: int = Field(default=0, ge=0)
    education: Optional[str] = None
    current_role: Optional[str] = None
    
    
class CandidateSkills(BaseModel):
    """Candidate skills and preferences."""
    skills: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list, description="Preferred job roles/technologies")
    certifications: List[str] = Field(default_factory=list)


class CandidateCreate(CandidateBase, CandidateSkills):
    """Model for creating a new candidate."""
    resume_text: str = Field(..., min_length=10, description="Full resume content")


class CandidateInDB(CandidateBase, CandidateSkills):
    """Candidate model as stored in database."""
    id: Optional[str] = Field(default=None, alias="_id")
    resume_text: str
    resume_embedding: Optional[List[float]] = None
    expanded_skills: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class CandidateResponse(CandidateBase, CandidateSkills):
    """Candidate response model for API."""
    id: str = Field(..., alias="_id")
    resume_text: str
    expanded_skills: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        populate_by_name = True


class CandidateListResponse(BaseModel):
    """Paginated list of candidates."""
    total: int
    page: int
    page_size: int
    candidates: List[CandidateResponse]
