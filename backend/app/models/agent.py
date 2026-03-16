from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    description: str
    status: str = "active" # active, training, error, inactive
    type: str = "generic"
    config: Dict[str, Any] = {}
    is_live: bool = Field(default=True, description="Whether this agent is live for all users")

class AgentCreate(AgentBase):
    id: str # User defined or slug

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_live: Optional[bool] = None

class AgentInDB(AgentBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentResponse(AgentBase):
    id: str
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
