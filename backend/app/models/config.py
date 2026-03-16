from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime

class AgentConfig(BaseModel):
    """
    Represents the configuration for a single AI agent, stored in the database.
    """
    agent_id: str = Field(..., description="The ID of the agent this config belongs to")
    version: int = Field(default=1, description="The version of the configuration")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific parameters like chunk_size, top_k, etc.")
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "agent_id": "rag_qa",
                "version": 1,
                "parameters": {
                    "chunk_size": 512,
                    "overlap": 64,
                    "top_k": 3,
                    "retrieval_strategy": "hybrid"
                },
                "updated_at": "2023-10-27T10:00:00Z"
            }
        }

class AgentConfigUpdate(BaseModel):
    """
    Pydantic model for updating an agent's configuration parameters.
    """
    parameters: Dict[str, Any]
