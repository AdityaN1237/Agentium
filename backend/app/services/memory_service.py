from typing import Any, Dict, List, Optional
from datetime import datetime
from app.database import Database
from app.models.memory import EpisodicMemory, ReflectiveMemory, PolicyMemory
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    """Manages the 4-brain memory system for autonomous agents."""

    @staticmethod
    async def store_episode(episode: EpisodicMemory) -> str:
        db = Database.get_db()
        data = episode.model_dump(by_alias=True, exclude_none=True)
        result = await db.episodic_memory.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_failed_episodes(agent_id: str, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        db = Database.get_db()
        cursor = db.episodic_memory.find({
            "agent_id": agent_id,
            "outcome_score": {"$lt": score_threshold}
        }).sort("timestamp", -1).limit(50)
        return await cursor.to_list(length=50)

    @staticmethod
    async def store_reflection(reflection: ReflectiveMemory) -> str:
        db = Database.get_db()
        data = reflection.model_dump(by_alias=True, exclude_none=True)
        result = await db.reflective_memory.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_latest_policy(agent_id: str) -> Optional[PolicyMemory]:
        db = Database.get_db()
        data = await db.policy_memory.find_one(
            {"agent_id": agent_id},
            sort=[("updated_at", -1)]
        )
        if data:
            return PolicyMemory(**data)
        return None

    @staticmethod
    async def get_latest_reflection(agent_id: str) -> Optional[ReflectiveMemory]:
        db = Database.get_db()
        data = await db.reflective_memory.find_one(
            {"agent_id": agent_id},
            sort=[("timestamp", -1)]
        )
        if data:
            return ReflectiveMemory(**data)
        return None

    @staticmethod
    async def update_policy(policy: PolicyMemory):
        db = Database.get_db()
        data = policy.model_dump(exclude_none=True)
        await db.policy_memory.update_one(
            {"agent_id": policy.agent_id},
            {"$set": data},
            upsert=True
        )

    @staticmethod
    async def record_feedback(episode_id: str, ground_truth: Any, score: float, feedback: Optional[str] = None):
        """Update an episode with ground truth and outcome score."""
        db = Database.get_db()
        from bson import ObjectId
        await db.episodic_memory.update_one(
            {"_id": ObjectId(episode_id)},
            {"$set": {
                "ground_truth": ground_truth,
                "outcome_score": score,
                "feedback": feedback,
                "updated_at": datetime.utcnow()
            }}
        )

memory_service = MemoryService()
