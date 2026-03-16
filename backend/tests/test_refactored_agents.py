import pytest
import asyncio
import json
import numpy as np
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.agents.skill_job_matching.agent import SkillJobMatchingAgent
from app.agents.rag_qa.agent import RAGQAAgent
from app.services.training_manager import training_manager

# Test Data Paths
TEST_Data_DIR = Path(__file__).parent / "test_data"
TEST_JOBS_FILE = TEST_Data_DIR / "jobs_dataset.json"

@pytest.fixture(scope="session", autouse=True)
def setup_test_files():
    """Setup temporary test environment."""
    TEST_Data_DIR.mkdir(exist_ok=True)
    
    # Create dummy jobs dataset
    jobs = [
        {
            "id": "job_1",
            "title": "Python Developer",
            "required_skills": ["Python", "Django"],
            "description": "Backend python role"
        },
        {
            "id": "job_2", 
            "title": "Frontend Developer",
            "required_skills": ["React", "TypeScript"],
            "description": "UI frontend role"
        }
    ]
    with open(TEST_JOBS_FILE, 'w') as f:
        json.dump(jobs, f)
        
    yield
    
    # Cleanup
    if TEST_Data_DIR.exists():
        shutil.rmtree(TEST_Data_DIR)

@pytest.fixture
def mock_embedding_service():
    with patch("app.agents.skill_job_matching.agent.get_embedding_service") as mock:
        service = MagicMock()
        # Mock encode to return random vectors
        service.encode.return_value = np.random.rand(2, 384)
        service.encode_batch_async.return_value = np.random.rand(2, 384)
        service.encode_resume_async.return_value = np.random.rand(384)
        service.encode_single_async.return_value = np.random.rand(384)
        mock.return_value = service
        yield service

@pytest.fixture
def mock_rag_embedding_service():
    with patch("app.agents.rag_qa.agent.get_embedding_service") as mock:
        service = MagicMock()
        service.encode.return_value = np.random.rand(1, 384)
        service.encode_batch_async.return_value = np.random.rand(1, 384)
        service.encode_single_async.return_value = np.random.rand(384)
        mock.return_value = service
        yield service

@pytest.mark.asyncio
async def test_skill_job_agent_local_load(mock_embedding_service):
    """Test that SkillJobMatchingAgent loads from local JSON."""
    # Patch the JOBS_DATASET_PATH in the agent module
    with patch("app.agents.skill_job_matching.agent.JOBS_DATASET_PATH", TEST_JOBS_FILE):
        agent = SkillJobMatchingAgent()
        
        # Check if jobs loaded
        assert len(agent._jobs) == 2
        assert agent._jobs[0]["title"] == "Python Developer"
        
        # Test validation
        ready = await agent.validate_data_readiness()
        assert ready is True

@pytest.mark.asyncio
async def test_skill_job_agent_prediction(mock_embedding_service):
    with patch("app.agents.skill_job_matching.agent.JOBS_DATASET_PATH", TEST_JOBS_FILE):
        agent = SkillJobMatchingAgent()
        # Mock embeddings to ensuredot product works
        agent._job_embeddings = np.random.rand(2, 384)
        
        input_data = {"resume_text": "I know Python and Django"}
        response = await agent.predict(input_data)
        
        assert response["status"] == "SUCCESS"
        assert len(response["data"]) > 0

@pytest.mark.asyncio
async def test_rag_agent_upload_and_index(mock_rag_embedding_service):
    """Test RAG agent document upload and indexing."""
    # Patch storage paths to use temp dir
    with patch("app.agents.rag_qa.agent.DOCS_DIR", TEST_Data_DIR / "rag_docs"), \
         patch("app.agents.rag_qa.agent.EMBEDDINGS_DIR", TEST_Data_DIR / "rag_emb"):
        
        agent = RAGQAAgent()
        
        docs = [{"text": "This is a test document about AI.", "title": "Doc 1"}]
        result = await agent.upload_dataset(docs)
        
        assert result["status"] == "success"
        assert len(agent._documents) == 1
        
        # Wait for background task (simulated)
        await agent.incremental_index(docs)
        
        assert len(agent._chunks) > 0
        assert agent._chunk_embeddings is not None

@pytest.mark.asyncio
async def test_rag_agent_predict(mock_rag_embedding_service):
    with patch("app.agents.rag_qa.agent.DOCS_DIR", TEST_Data_DIR / "rag_docs"), \
         patch("app.agents.rag_qa.agent.EMBEDDINGS_DIR", TEST_Data_DIR / "rag_emb"):
        
        agent = RAGQAAgent()
        
        # Setup fake state
        agent._chunks = [{"text": "AI is great.", "title": "Doc 1", "chunk_id": "1", "score": 0.9}]
        agent._chunk_embeddings = np.random.rand(1, 384)
        
        # Mock LLM
        with patch("app.agents.rag_qa.agent.get_llm") as mock_llm_factory:
            mock_llm = MagicMock()
            mock_llm.chat_completion = AsyncMock(return_value={
                "choices": [{"message": {"content": "AI is indeed great."}}]
            })
            mock_llm_factory.return_value = mock_llm
            
            response = await agent.predict({"query": "How is AI?"})
            
            assert response["status"] == "SUCCESS"
            assert response["data"]["answer"] == "AI is indeed great."


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
