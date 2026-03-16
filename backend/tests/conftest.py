import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.database import Database
from app.agents.registry import registry
from app.services.memory_service import memory_service

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db():
    """Database fixture."""
    await Database.connect()
    return Database.get_db()

@pytest.fixture(scope="session")
async def agents(db):
    """Agents registry fixture."""
    await registry.initialize(db)
    return registry

@pytest.fixture(scope="session")
async def memory():
    """Memory service fixture."""
    return memory_service

@pytest.fixture(autouse=True)
async def mock_llm(monkeypatch):
    """Global mock for LLM to avoid external API calls during tests."""
    mock_provider = AsyncMock()
    
    async def side_effect(messages, **kwargs):
        content = messages[-1]["content"].lower()
        if "fit" in content or "candidate" in content:
            return {
                "choices": [{
                    "message": {
                        "content": '{"overall_fit_score": 0.85, "technical_readiness": 0.9, "cultural_alignment": 0.8, "retention_probability": 0.95, "reasoning": {"steps": ["stack check", "experience check"], "conclusion": "Good fit"}}'
                    }
                }]
            }
        elif "answer" in content or "question" in content:
            return {
                "choices": [{
                    "message": {
                        "content": '{"answer": "Based on the context, you get 25 days of annual leave.", "confidence_score": 0.95}'
                    }
                }]
            }
        return {
            "choices": [{
                "message": {
                    "content": '{"result": "mocked response"}'
                }
            }]
        }
    
    mock_provider.chat_completion.side_effect = side_effect
    
    # Patch get_llm in all agent modules where it's imported
    agent_modules = [
        "app.agents.candidate_fit.agent",
        "app.agents.rag_qa.agent",
        "app.agents.base",
        "app.services.llm_factory"
    ]
    
    for module in agent_modules:
        try:
            monkeypatch.setattr(f"{module}.get_llm", lambda name=None: mock_provider)
        except (AttributeError, ImportError):
            pass
            
    return mock_provider

@pytest.fixture(autouse=True)
async def clean_db(db):
    """Clean specific test collections before each test."""
    await db.episodes.delete_many({"agent_id": {"$regex": "^test_"}})
    yield
