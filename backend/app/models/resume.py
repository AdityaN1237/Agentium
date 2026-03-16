from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


class ResumeBase(BaseModel):
    user_id: str
    filename: str
    content_type: str
    file_path: str
    resume_text: Optional[str] = None
    extracted_skills: List[str] = Field(default_factory=list)
    current_role: Optional[str] = None
    experience_years: Optional[int] = 0
    education: Optional[str] = None


class ResumeInDB(ResumeBase):
    id: Optional[str] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ResumeUploadResponse(BaseModel):
    resume_id: str
    candidate_id: Optional[str] = None
    message: str
