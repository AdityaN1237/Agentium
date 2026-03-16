from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class EpisodicMemory(BaseModel):
    """Stores individual decision events and outcomes."""
    id: Optional[str] = Field(None, alias="_id")
    agent_id: str
    query_id: str
    input_data: Any
    prediction: Any
    confidence: float
    ground_truth: Optional[Any] = None
    outcome_score: Optional[float] = None # 0.0 to 1.0
    feedback: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str

class ReflectiveMemory(BaseModel):
    """Stores analyses of past performance and errors."""
    id: Optional[str] = Field(None, alias="_id")
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mistake_patterns: List[str] = Field(default_factory=list)
    root_causes: List[str] = Field(default_factory=list)
    new_decision_rules: List[str] = Field(default_factory=list)
    confidence_adjustments: Dict[str, float] = Field(default_factory=dict)
    learning_summary: str
    source_episodes: List[str] = Field(default_factory=list) # IDs of EpisodicMemory

class PolicyMemory(BaseModel):
    """Stores current decision rules, heuristics, and adaptive weights."""
    agent_id: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str
    weights: Dict[str, float] = Field(default_factory=dict) # e.g., {"semantic": 0.45, "skill": 0.30}
    heuristics: List[str] = Field(default_factory=list)
    bias_corrections: Dict[str, Any] = Field(default_factory=dict)
    uncertainty_calibration: Dict[str, Any] = Field(default_factory=dict)
