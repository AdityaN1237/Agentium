"""
Unified Inference Chat Router.
Handles natural language queries and routes them to appropriate agents.
Supports multi-turn conversations and context awareness.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import uuid

from app.agents.registry import registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Inference Chat"])

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    agent_id: Optional[str] = None
    context_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    agent_used: str
    context_id: str

# Simple in-memory context store (replace with Redis/DB in production)
_context_store: Dict[str, List[Message]] = {}

def _detect_intent(query: str) -> str:
    """
    Simple intent detection to route to the best agent.
    In a real system, this would be a classification model.
    """
    query_lower = query.lower()
    
    if any(k in query_lower for k in ["job", "role", "vacancy", "opening", "hiring", "recommend"]):
        return "skill_job_matching" # or screening
    
    if any(k in query_lower for k in ["skill", "learn", "gap", "improve", "study"]):
        return "skill_gap"
    
    if any(k in query_lower for k in ["salary", "market", "trend", "pay", "demand"]):
        return "market_trend"
    
    # Default to RAG for general knowledge/document questions
    return "rag_qa"

@router.post("/", response_model=ChatResponse)
async def chat_inference(
    request: ChatRequest
):
    """
    Unified chat endpoint.
    Routes queries to the appropriate agent based on context and intent.
    """
    context_id = request.context_id or str(uuid.uuid4())
    
    # update context
    if context_id not in _context_store:
        _context_store[context_id] = []
    
    # Append user message
    user_msg = request.messages[-1]
    _context_store[context_id].append(user_msg)
    
    # Determine agent
    agent_id = request.agent_id
    if not agent_id:
        agent_id = _detect_intent(user_msg.content)
        
    try:
        agent = registry.get_agent(agent_id)
    except Exception:
        # Fallback
        agent = registry.get_agent("rag_qa")
        agent_id = "rag_qa"

    logger.info(f"🤖 Routing query to agent: {agent_id} (Context: {context_id})")

    # Construct Agent Input
    # Some agents expect different formats, we try to standardize here
    agent_input = {
        "query": user_msg.content,
        "chat_history": [m.dict() for m in _context_store[context_id][:-1]], # exclude current
        "user_context": {"id": "local_user", "role": "admin"} # Default context
    }

    # Execute Prediction
    try:
        result = await agent.predict(agent_input)
        
        # Parse output (Agent output formats vary)
        response_text = ""
        sources = []
        metadata = {}
        
        # Unwrap 'data' if present (standard agent response format)
        if isinstance(result, dict) and "data" in result:
            # Metadata from top-level wrapper
            if "confidence" in result:
                metadata["confidence"] = result["confidence"]
            if "latency_ms" in result:
                metadata["latency_ms"] = result["latency_ms"]
            
            # Use inner data for content
            result = result["data"]

        if isinstance(result, dict):
            response_text = result.get("answer") or result.get("message") or str(result)
            sources = result.get("sources", [])
            
            # Extract additional metadata from inner result if not already set
            if "confidence" in result and "confidence" not in metadata:
                metadata["confidence"] = result["confidence"]
            if "latency_ms" in result and "latency_ms" not in metadata:
                metadata["latency_ms"] = result["latency_ms"]
            if "verified" in result:
                metadata["verified"] = result["verified"]
                
        elif isinstance(result, list):
            # Probably a list of recommendations
            response_text = "Here are the top matches I found:\n\n"
            for item in result[:5]:
                name = item.get("name") or item.get("title") or "Unknown"
                score = item.get("score", 0)
                response_text += f"- **{name}** ({int(score*100)}% match)\n"
        else:
            response_text = str(result)

        # Append assistant response to context
        _context_store[context_id].append(Message(role="assistant", content=response_text))
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            metadata=metadata,
            agent_used=agent_id,
            context_id=context_id
        )

    except Exception as e:
        logger.error(f"❌ Inference failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/context/{context_id}")
async def clear_context(context_id: str):
    if context_id in _context_store:
        del _context_store[context_id]
    return {"status": "cleared"}
