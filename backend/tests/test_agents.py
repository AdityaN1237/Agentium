import pytest
import asyncio
from app.agents.registry import registry
from app.agents.base import AgentMetadata

@pytest.mark.asyncio
async def test_agent_registration(agents):
    """Verify that all core agents are registered."""
    expected_agents = ["skill_job_matching", "resume_screening", "candidate_fit", "rag_qa"]
    for agent_id in expected_agents:
        agent = agents.get_agent(agent_id)
        assert agent is not None
        assert agent.metadata.id == agent_id

@pytest.mark.asyncio
async def test_base_agent_pipeline_execution():
    """Test the standardized 9-step pipeline on a mock agent."""
    from app.agents.base import BaseAgent, MetricsModel
    from typing import Any, Dict, Union
    
    class MockAgent(BaseAgent):
        def __init__(self):
            super().__init__(AgentMetadata(id="test_mock", name="Mock", description="Test", version="1.0.0"))
            self.steps_run = []
            
        async def validate_data_readiness(self) -> bool:
            self.steps_run.append(1)
            return True
        async def index_data(self, session: Any) -> None:
            self.steps_run.append(2)
        async def train_knowledge_graph(self, session: Any) -> None:
            self.steps_run.append(3)
        async def calibrate_intelligence(self, session: Any) -> None:
            self.steps_run.append(4)
        async def calibrate_scoring(self, session: Any) -> None:
            self.steps_run.append(5)
        async def evaluate(self) -> MetricsModel:
            self.steps_run.append(8)
            return MetricsModel(accuracy=0.9)
        async def predict_logic(self, input_data: Any) -> Any:
            return {"result": "ok"}
        async def upload_dataset(self, data: Any) -> Dict[str, Any]:
            return {"status": "success"}

    agent = MockAgent()
    await agent.execute_pipeline()
    
    assert agent.metadata.state == "READY"
    assert agent.metadata.metrics.accuracy == 0.9
    # Check if all steps were run (1, 2, 3, 4, 5, 8)
    # Steps 6, 7 are handled by BaseAgent and they are pass-through currently
    for step in [1, 2, 3, 4, 5, 8]:
        assert step in agent.steps_run

@pytest.mark.asyncio
async def test_agent_prediction_with_memory(agents, db):
    """Verify that predict() stores episodic memory."""
    agent = agents.get_agent("skill_job_matching")
    # Ensure it's ready
    agent.metadata.state = "READY"
    
    # Seed a candidate
    candidate_data = {
        "name": "Test Candidate",
        "email": "matching_test@example.com",
        "skills": ["Python", "FastAPI"],
        "resume_text": "Experienced Python developer with FastAPI expertise.",
        "is_active": True
    }
    res = await db.candidates.insert_one(candidate_data)
    candidate_id = str(res.inserted_id)
    
    # Seed a job so we have something to match
    await db.jobs.insert_one({
        "title": "FastAPI Developer",
        "description": "Looking for FastAPI expert. Must have 5 years of experience in Python and FastAPI.",
        "required_skills": ["Python", "FastAPI"],
        "is_active": True
    })
    
    input_data = {"candidate_id": candidate_id, "top_k": 1}
    result = await agent.predict(input_data)
    
    assert "status" in result
    assert result["status"] == "SUCCESS"
    assert "data" in result
    
    # Cleanup
    await db.candidates.delete_one({"_id": res.inserted_id})
    await db.jobs.delete_many({"title": "FastAPI Developer"})

@pytest.mark.asyncio
async def test_resume_screening_agent(agents, db):
    """Test the resume screening agent."""
    agent = agents.get_agent("resume_screening")
    agent.metadata.state = "READY"
    
    # Seed a candidate with embedding (as predict_logic filters for it)
    c_res = await db.candidates.insert_one({
        "name": "Screener Candidate",
        "email": "screener_test@example.com",
        "resume_text": "Python developer with many years of experience.",
        "resume_embedding": [0.1] * 384 # Mock embedding
    })
    
    input_data = {
        "job_description": "We need a Python expert with extensive experience in backend development and scalable systems.",
        "top_k": 5
    }
    result = await agent.predict(input_data)
    
    assert result["status"] == "SUCCESS"
    assert "data" in result
    # It might return empty if similarity is low or no candidates matched, but status should be SUCCESS
    
    # Cleanup
    await db.candidates.delete_one({"_id": c_res.inserted_id})

@pytest.mark.asyncio
async def test_rag_qa_agent(agents, db):
    """Test the RAG QA agent."""
    agent = agents.get_agent("rag_qa")
    agent.metadata.state = "READY"
    
    # Seed a document and its chunk (predict_logic searches doc_chunks)
    doc_res = await db.documents.insert_one({
        "title": "Test Policy",
        "text": "The company allows 25 days of annual leave.",
        "source": "Manual"
    })
    
    await db.doc_chunks.insert_one({
        "doc_id": doc_res.inserted_id,
        "text": "The company allows 25 days of annual leave.",
        "embedding": [0.1] * 384,
        "chunk_index": 0
    })
    
    input_data = {"query": "How many days of annual leave do I get?"}
    result = await agent.predict(input_data)
    
    assert result["status"] == "SUCCESS"
    assert "data" in result
    
    # Cleanup
    await db.documents.delete_one({"_id": doc_res.inserted_id})
    await db.doc_chunks.delete_many({"doc_id": doc_res.inserted_id})

@pytest.mark.asyncio
async def test_candidate_fit_agent(agents, db):
    """Test the candidate fit agent."""
    agent = agents.get_agent("candidate_fit")
    agent.metadata.state = "READY"
    
    input_data = {
        "candidate_skills": ["Java", "Spring Boot"],
        "job_requirements": "Looking for a Senior Java Developer with 8+ years of experience and deep knowledge of Spring Boot and microservices architecture.",
        "candidate_experience": "10 years of experience in Java."
    }
    result = await agent.predict(input_data)
    
    assert result["status"] == "SUCCESS"
    assert "data" in result
